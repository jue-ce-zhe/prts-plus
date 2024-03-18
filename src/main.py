import argparse
import logging

from src.logger import logger
from src.excel import Excel, StatusColor
from src.config import PerformActionConfig as actionconfig
from src.logic.perform_action import perform_action, PerformLateError
from src.logic.calc_view import transform_map_to_view
from src.logic.game_time import GameTime
from src.logic.action import ActionType
from src.cache import get_map_by_code, get_map_by_name
from src.utils.error_to_log import ErrorToLog

def main(file_path, debug):
    # Set the logger level
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING)
    
    # Establish the connection to the Excel file
    logger.info(f"Excel file path: {file_path}")
    excel = Excel(file_path)

    try:
        # Load settings
        map_code = excel.get_setting('map_code')
        map_name = excel.get_setting('map_name')
        max_tick = excel.get_setting('max_tick')
        wait_time1 = excel.get_setting('wait_time1')
        wait_time2 = excel.get_setting('wait_time2')
        bullet_threshold = excel.get_setting('bullet_threshold')
        frame_threshold = excel.get_setting('frame_threshold')

        # Apply settings
        if max_tick is not None:
            GameTime.set_tick_max(max_tick)
        if wait_time1 is not None:
            actionconfig.DEPLOY_WAITTIME1 = wait_time1
        if wait_time2 is not None:
            actionconfig.GENERAL_WAITTIME = wait_time2
        if bullet_threshold is not None:
            actionconfig.BULLET_THRESHOLD = bullet_threshold
        if frame_threshold is not None:
            actionconfig.FRAME_THRESHOLD = frame_threshold

        # Load map
        if map_name is not None:
            map_data = get_map_by_name(map_name)
        elif map_code is not None:
            map_data = get_map_by_code(map_code)
        else:
            logger.error("No map specified.")
            raise ErrorToLog("未指定关卡。")
        view_data_front = transform_map_to_view(map_data, False)
        view_data_side = transform_map_to_view(map_data, True)

        # Initialize operator location mapping and operator alias mapping
        operator_loc = {}
        operator_alias = {}

        # Main loop
        while not excel.is_paused():
            action = excel.get_current_action()

            # Check if the action is valid
            if not action.is_valid():
                logger.warning(f"Invalid action: {action}")
                logger.info("Terminating the program")
                break
            
            # Tackle alias if needed
            if action.alias is not None:
                operator_alias[action.alias] = action.oper
                logger.info(f"Memorized {action.alias} as an alias of {action.oper}")
            
            if action.oper in operator_alias.keys():
                logger.info(f"Detected alias, replace {action.oper} with {operator_alias[action.oper]}")
                action.oper = operator_alias[action.oper]

            # Memorize operator location if needed
            if action.action_type == ActionType.DEPLOY:
                operator_loc[action.oper] = (action.pos_x, action.pos_y)
                logger.info(f"Memorized {action.oper} location at {operator_loc[action.oper]}")
            else:
                if action.pos_x is None or action.pos_y is None:
                    action.pos_x, action.pos_y = operator_loc[action.oper]
                    logger.info(f"Auto set {action.oper} location to {action.pos_x}, {action.pos_y}")

            # Fetch view position
            action.view_pos_front = view_data_front[action.pos_y][action.pos_x]
            action.view_pos_side = view_data_side[action.pos_y][action.pos_x]
            
            # Perform the action
            try:
                perform_action(action)
                excel.set_result(StatusColor.SUCCESS)
            except PerformLateError as e:
                excel.set_result(StatusColor.WARNING)
            except Exception as e:
                excel.set_result(StatusColor.FAILURE)
                raise

            excel.next_action()
    except ErrorToLog as e:
        logger.error(f"Error occurred: {e}")
        excel.show_error(str(e))
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        excel.show_error(f"未定义错误：{e}")
    finally:
        excel.set_paused()

if __name__ == '__main__':
    # Take the only parameter as the Excel file path
    parser = argparse.ArgumentParser(description='PRTS+')
    parser.add_argument('--xlsm', type=str, help='The path to the Excel file.')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode.')

    args = parser.parse_args()
    main(args.xlsm, args.debug)