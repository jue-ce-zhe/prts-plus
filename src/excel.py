from win32com import client, __gen_path__
from pywintypes import com_error
import functools
import os
import dataclasses

from src.logic.action import Action, ActionType, DirectionType
from src.utils.singleton import Singleton
from src.utils.error_to_log import ErrorToLog
from src.logger import logger
from src.utils.typecheck import get_optional_type

__all__ = ['Excel']

ACTION_COLUMN_NAME_MAPPING = {
    '费用': 'cost',
    '帧数': 'tick',
    '操作': 'action_type',
    '干员': 'oper',
    '坐标': 'pos',
    '朝向': 'direction',
    '简称': 'alias',
}

@dataclasses.dataclass(order=True)
class StatusColor:
    SUCCESS: int = 0x77FF77 # green
    WARNING: int = 0x77FFFF # yellow
    FAILURE: int = 0x7777FF # red

# Note: All excel index should be 0-based in the code, adding 1 when interacting with Excel
class Excel(metaclass=Singleton):
    def __init__(self, file_path):
        self.file_path = file_path
        self.excel = None
        self.workbook = None
        self.record_sheet = None
        self.data = None
        self._own_excel = False
        self._own_workbook = False
        self.column_loc = {}
        self.data_loc = {}
        self.current_row = 1
        self._connect()
        self._locate_data()
        self._signal_start()
        self._reset_cells()
    
    def _connect(self):
        try:
            self.excel = client.GetActiveObject('Excel.Application')
        except com_error:
            logger.warning("Excel application not found, creating a new one")
            try:
                self.excel = client.Dispatch('Excel.Application')
                self._own_excel = True
            except com_error:
                logger.error("Failed to create Excel application")
                raise
        
        self.workbook = None
        for wb in self.excel.Workbooks:
            logger.debug(f"Checking workbook: {os.path.normpath(os.path.abspath(wb.FullName))}")
            if os.path.normpath(os.path.abspath(wb.FullName)) == self.file_path:
                self.workbook = wb
                break

        if self.workbook is None:
            logger.warning(f"Excel file not found, opening {self.file_path}")
            try:
                self.workbook = self.excel.Workbooks.Open(self.file_path)
                self._own_workbook = True
            except com_error:
                logger.error(f"Failed to open {self.file_path}")
                self._close()
                raise
        try:
            self.record_sheet = self.workbook.Sheets("作战记录")
            self.control_sheet = self.workbook.Sheets("中转站")
        except com_error:
            logger.error("Failed to locate sheet")
            self._close()
            raise

        logger.info(f"Connected to Excel file: {self.file_path}, workbook owned: {self._own_workbook}, excel owned: {self._own_excel}")
    
    def connection_handler(func):
        @functools.wraps(func)
        def wrapper(excel_instance, *args, **kwargs):
            try:
                return func(excel_instance, *args, **kwargs)
            except com_error as e:
                logger.error("Excel connection lost.")
                raise ErrorToLog(f"Excel连接出错。\n{e}")
        return wrapper
    
    @connection_handler
    def _locate_data(self):
        self.data = self.record_sheet.UsedRange.Value

        for key, value in ACTION_COLUMN_NAME_MAPPING.items():
            self.column_loc[value] = self.locate_column(key)
        self.column_loc['cur_exec'] = self.locate_column('当前执行')
        self.column_loc['result'] = self.locate_column('运行结果')
        self.column_loc['settings'] = self.locate_column('设置')

        settings_col = self.column_loc['settings']
        logger.debug(f"Settings column: {settings_col}")
        self.data_loc['map_code'] = (self.locate_row(settings_col, '关卡代号'), settings_col + 1)
        self.data_loc['map_name'] = (self.locate_row(settings_col, '关卡全名'), settings_col + 1)
        self.data_loc['max_tick'] = (self.locate_row(settings_col, '每费帧数'), settings_col + 1)
        self.data_loc['wait_time1'] = (self.locate_row(settings_col, '等待时间1'), settings_col + 1)
        self.data_loc['wait_time2'] = (self.locate_row(settings_col, '等待时间2'), settings_col + 1)
        self.data_loc['wait_time3'] = (self.locate_row(settings_col, '等待时间3'), settings_col + 1)
        self.data_loc['bullet_threshold'] = (self.locate_row(settings_col, '阈值-子弹时间'), settings_col + 1)
        self.data_loc['frame_threshold'] = (self.locate_row(settings_col, '阈值-逐帧定位'), settings_col + 1)

        self.data_loc['cur_status'] = (0, 1) # B1 cell
        self.data_loc['cur_row'] = (1, 1) # B2 cell
        self.data_loc['err_log'] = (2, 1) # B3 cell
    
    def _signal_start(self):
        self.set_control_value('cur_status', '运行中')
        self.set_control_value('err_log', '')
        self.current_row = int(self.get_control_value('cur_row')) - 1
    
    @connection_handler
    def _reset_cells(self):
        last_row = len(self.data)
        # Clear all cells in column '当前执行' and '运行结果'
        logger.debug(f"Clearing cells from {self.current_row + 1} to {last_row} in column '当前执行'({self.column_loc['cur_exec'] + 1}) and '运行结果'({self.column_loc['result'] + 1})")
        self.record_sheet.Range(self.record_sheet.Cells(self.current_row + 1, self.column_loc['cur_exec'] + 1), 
                                self.record_sheet.Cells(last_row, self.column_loc['cur_exec'] + 1)).Value = None
        self.record_sheet.Range(self.record_sheet.Cells(self.current_row + 1, self.column_loc['result'] + 1), 
                                self.record_sheet.Cells(last_row, self.column_loc['result'] + 1)).Interior.ColorIndex = -4142 # xlNone

        # Set pointer to the first action
        self.record_sheet.Cells(self.current_row + 1, self.column_loc['cur_exec'] + 1).Value = '→'

    def _close(self, save_changes=False):
        # Note: keep it open for now
        # if self.workbook is not None and self._own_workbook:
        #     self.workbook.Close(SaveChanges=save_changes)
        #     self.workbook = None
        #     logger.info(f"Closed Excel file: {self.file_path}")
        # if self.excel is not None and self._own_excel:
        #     self.excel.Quit()
        #     self.excel = None
        #     logger.info("Closed Excel application")
        pass
    
    def __del__(self):
        self._close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self._close()

    def locate_column(self, column_name):
        try:
            return self.data[0].index(column_name)
        except ValueError:
            raise ErrorToLog(f"列 {column_name} 未找到。")
    
    def locate_row(self, col, row_value):
        for index, row in enumerate(self.data):
            if row[col] == row_value:
                return index
        raise ErrorToLog(f"行 {row_value} 未找到。")
    
    @connection_handler
    def set_control_value(self, control_name, value):
        logger.debug(f"Setting control {control_name} to {value} at {self.data_loc[control_name]}")
        self.control_sheet.Cells(self.data_loc[control_name][0] + 1, self.data_loc[control_name][1] + 1).Value = value
    
    @connection_handler
    def get_control_value(self, control_name):
        return self.control_sheet.Cells(self.data_loc[control_name][0] + 1, self.data_loc[control_name][1] + 1).Value
    
    def is_paused(self) -> bool:
        return self.get_control_value('cur_status') == '停止中'
    
    def set_paused(self) -> None:
        self.set_control_value('cur_status', '已停止')

    def show_error(self, message) -> None:
        self.set_control_value('err_log', message)
    
    def get_current_action(self):
        if self.current_row >= len(self.data):
            return Action()
        return self.get_action(self.current_row)
    
    def load_cell_with_type(self, row, col, cell_type):
        try:
            logger.debug(f"Loading cell ({row}, {col}) with type {cell_type}")
            cell_value = self.data[row][col]
            if cell_value is None:
                return None
            
            actual_type = get_optional_type(cell_type)
            return actual_type(cell_value) if actual_type else None
        except (ValueError, TypeError) as err:
            logger.debug(f"Failed to load cell ({row}, {col}) with type {cell_type} due to error {err}")
            return None
    
    def get_action(self, row):
        action_data = {}
        for field in dataclasses.fields(Action):
            col = self.column_loc.get(field.name)
            if col is not None:
                cell_value = self.load_cell_with_type(row, col, field.type)
                action_data[field.name] = cell_value
        action = Action(**action_data)
        logger.info(f"Get action: {action}")
        return action

    @connection_handler
    def set_result(self, result: StatusColor):
        self.record_sheet.Cells(self.current_row + 1, self.column_loc['result'] + 1).Interior.Color = result

    @connection_handler
    def next_action(self):
        if self.record_sheet.Cells(self.current_row + 1, self.column_loc['cur_exec'] + 1).Value == '→':
            self.record_sheet.Cells(self.current_row + 1, self.column_loc['cur_exec'] + 1).Value = ''
        self.current_row += 1
        self.record_sheet.Cells(self.current_row + 1, self.column_loc['cur_exec'] + 1).Value = '→'
        self.set_control_value('cur_row', self.current_row + 1)

    def get_setting(self, name):
        return self.data[self.data_loc[name][0]][self.data_loc[name][1]]

if __name__ == "__main__":
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "template.xlsm")
    logger.info(f"Excel file path: {file_path}")
    excel = Excel(file_path)
    current_action = excel.get_current_action()
    logger.info(f"Current action: {current_action}")
