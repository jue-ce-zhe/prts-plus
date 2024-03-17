import shutil
from win32com import client, __gen_path__
from pywintypes import com_error
import functools
import os
import dataclasses

from src.logic.action import Action, ActionType, DirectionType
from src.utils.singleton import Singleton
from src.logger import logger
from src.utils.typecheck import get_optional_type

__all__ = ['Excel']

# def clear_win32com_cache():
#     shutil.rmtree(__gen_path__, ignore_errors=True)

ACTION_COLUMN_NAME_MAPPING = {
    '费用': 'cost',
    '帧数': 'tick',
    '操作': 'action_type',
    '干员': 'oper',
    'x坐标': 'pos_x',
    'y坐标': 'pos_y',
    '朝向': 'direction',
    '简称': 'alias',
}

@dataclasses.dataclass(order=True)
class StatusColor:
    SUCCESS: int = 0x77FF77 # green
    WARNING: int = 0x77FFFF # yellow
    FAILURE: int = 0x7777FF # red

class Excel(metaclass=Singleton):
    def __init__(self, file_path):
        self.file_path = file_path
        self.excel = None
        self.workbook = None
        self.record_sheet = None
        self._own_excel = False
        self._own_workbook = False
        self.column_loc = {}
        self.data_loc = {}
        self._connect()
        self._locate_data()
        self._signal_start()
    
    def _connect(self):
        try:
            self.excel = client.GetActiveObject('Excel.Application')
        except com_error:
            self.excel = client.Dispatch('Excel.Application')
            self._own_excel = True
        
        self.workbook = None
        for wb in self.excel.Workbooks:
            if os.path.normpath(os.path.abspath(wb.FullName)) == self.file_path:
                self.workbook = wb
                break

        if self.workbook is None:
            try:
                self.workbook = self.excel.Workbooks.Open(self.file_path)
                self._own_workbook = True
            except com_error:
                logger.error(f"Failed to open {self.file_path}")
                self._close()
                raise
        
        self.record_sheet = self.workbook.Sheets("作战记录")

        logger.info(f"Connected to Excel file: {self.file_path}, workbook owned: {self._own_workbook}, excel owned: {self._own_excel}")
    
    def _locate_data(self):
        for key, value in ACTION_COLUMN_NAME_MAPPING.items():
            self.column_loc[value] = self.locate_column(self.record_sheet, key)
        self.column_loc['result'] = self.locate_column(self.record_sheet, '运行结果')
        self.column_loc['metadata'] = self.locate_column(self.record_sheet, '元数据')
        self.data_loc['map_code'] = (self.locate_row(self.record_sheet, self.column_loc['metadata'], '关卡代号'), self.column_loc['metadata'] + 1)
        self.data_loc['max_tick'] = (self.locate_row(self.record_sheet, self.column_loc['metadata'], '每费帧数'), self.column_loc['metadata'] + 1)
        self.data_loc['paused'] = (self.locate_row(self.record_sheet, self.column_loc['metadata'], '当前状态'), self.column_loc['metadata'] + 1)
        self.data_loc['current'] = (self.locate_row(self.record_sheet, self.column_loc['metadata'], '当前操作'), self.column_loc['metadata'] + 1)
    
    def _signal_start(self):
        self.record_sheet.Cells(*self.data_loc['paused']).Value = '运行中'
        self.record_sheet.Cells(*self.data_loc['current']).Value = 2

    def _close(self, save_changes=False):
        if self.workbook is not None and self._own_workbook:
            self.workbook.Close(SaveChanges=save_changes)
            self.workbook = None
            logger.info(f"Closed Excel file: {self.file_path}")
        if self.excel is not None and self._own_excel:
            self.excel.Quit()
            self.excel = None
            logger.info("Closed Excel application")
    
    def __del__(self):
        self._close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self._close()

    def reconnect_decorator(func):
        @functools.wraps(func)
        def wrapper(excel_instance, *args, **kwargs):
            try:
                return func(excel_instance, *args, **kwargs)
            except com_error:
                logger.error("Excel connection lost. Reconnecting...")
                excel_instance._connect()
                return func(excel_instance, *args, **kwargs)
        return wrapper
    
    @reconnect_decorator
    def locate_column(self, sheet, column_name):
        for col in range(1, sheet.UsedRange.Columns.Count + 1):
            if sheet.Cells(1, col).Value == column_name:
                return col
        raise ValueError(f"Column {column_name} not found")
    
    @reconnect_decorator
    def locate_row(self, sheet, col, row_value):
        for row in range(2, sheet.UsedRange.Rows.Count + 1):
            if sheet.Cells(row, col).Value == row_value:
                return row
        raise ValueError(f"Row {row_value} not found")
    
    @reconnect_decorator
    def is_paused(self):
        return self.record_sheet.Cells(*self.data_loc['paused']).Value == '已停止'
    
    @reconnect_decorator
    def set_paused(self):
        self.record_sheet.Cells(*self.data_loc['paused']).Value = '已停止'
    
    @reconnect_decorator
    def get_current_row(self):
        return int(self.record_sheet.Cells(*self.data_loc['current']).Value)
    
    @reconnect_decorator
    def get_current_action(self):
        return self.get_action(self.get_current_row())
    
    @reconnect_decorator
    def load_cell_with_type(self, sheet, row, col, cell_type):
        try:
            logger.info(f"Loading cell ({row}, {col}) with type {cell_type}")
            cell_value = sheet.Cells(row, col).Value
            if cell_value is None:
                return None
            
            actual_type = get_optional_type(cell_type)
            return actual_type(cell_value) if actual_type else None
        except (ValueError, TypeError):
            logger.debug(f"Failed to load cell ({row}, {col}) with type {cell_type}")
            return None
    
    @reconnect_decorator
    def get_action(self, row):
        action_data = {}
        for field in dataclasses.fields(Action):
            col = self.column_loc.get(field.name)
            if col is not None:
                cell_value = self.load_cell_with_type(self.record_sheet, row, col, field.type)
                logger.debug(f"Loaded cell ({row}, {col}) with value {cell_value}")
                action_data[field.name] = cell_value
        action = Action(**action_data)
        logger.info(f"Get action: {action}")
        return action

    @reconnect_decorator
    def set_result(self, result: StatusColor):
        self.record_sheet.Cells(self.get_current_row(), self.column_loc['result']).Interior.Color = result

    @reconnect_decorator
    def next_action(self):
        self.record_sheet.Cells(*self.data_loc['current']).Value += 1

    @reconnect_decorator
    def get_map_code(self):
        return self.record_sheet.Cells(*self.data_loc['map_code']).Value
    
    @reconnect_decorator
    def get_max_tick(self):
        return self.record_sheet.Cells(*self.data_loc['max_tick']).Value

if __name__ == "__main__":
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "template.xlsm")
    logger.info(f"Excel file path: {file_path}")
    excel = Excel(file_path)
    # logger.info(f"Metadata is located at column {excel.locate_column(excel.record_sheet, '元数据')}")
    current_action = excel.get_current_action()
    logger.info(f"Current action: {current_action}")
