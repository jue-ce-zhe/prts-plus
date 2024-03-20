import argparse
import logging

from src.logger import logger
from src.excel import Excel, StatusColor
from src.config import PerformActionConfig as actionconfig
from src.logic.perform_action import perform_action, PerformLateError, UserPausedError
from src.logic.calc_view import transform_map_to_view
from src.logic.game_time import GameTime
from src.logic.action import ActionType
from src.cache import get_map_by_code, get_map_by_name
from src.utils.error_to_log import ErrorToLog
from src.logic.convert_pos import convert_position

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
        # Define the check pause closure
        def is_paused():
            return excel.is_paused()
        
        # Load settings
        map_code = excel.get_setting('map_code')
        map_name = excel.get_setting('map_name')
        max_tick = excel.get_setting('max_tick')
        wait_time1 = excel.get_setting('wait_time1')
        wait_time2 = excel.get_setting('wait_time2')
        wait_time3 = excel.get_setting('wait_time3')
        bullet_threshold = excel.get_setting('bullet_threshold')
        frame_threshold = excel.get_setting('frame_threshold')

        # Apply settings
        if max_tick is not None:
            GameTime.set_tick_max(max_tick)
        if wait_time1 is not None:
            actionconfig.MINIMUM_WAITTIME = wait_time1
            logger.debug(f"Set minimum wait time to {actionconfig.MINIMUM_WAITTIME}")
        if wait_time2 is not None:
            actionconfig.FRAME_WAITTIME = wait_time2
            logger.debug(f"Set frame wait time to {actionconfig.FRAME_WAITTIME}")
        if wait_time3 is not None:
            actionconfig.GENERAL_WAITTIME = wait_time3
            logger.debug(f"Set general wait time to {actionconfig.GENERAL_WAITTIME}")
        if bullet_threshold is not None:
            actionconfig.BULLET_THRESHOLD = bullet_threshold
            logger.debug(f"Set bullet threshold to {actionconfig.BULLET_THRESHOLD}")
        if frame_threshold is not None:
            actionconfig.FRAME_THRESHOLD = frame_threshold
            logger.debug(f"Set frame threshold to {actionconfig.FRAME_THRESHOLD}")

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

        map_height, map_width = map_data["height"], map_data["width"]

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

            # Calculate the tile position from raw position
            convert_position(action, map_height, map_width)

            # Memorize operator location if needed
            if action.action_type == ActionType.DEPLOY:
                operator_loc[action.oper] = action.tile_pos
                if action.alias is not None:
                    operator_loc[action.alias] = action.tile_pos
                logger.info(f"Memorized {action.oper} location at {operator_loc[action.oper]}")
            else:
                if action.tile_pos is None:
                    action.tile_pos = operator_loc[action.oper]
                    logger.info(f"Auto set {action.oper} location to {action.tile_pos}")
            
            # Tackle alias if needed
            if action.alias is not None:
                operator_alias[action.alias] = action.oper
                logger.info(f"Memorized {action.alias} as an alias of {action.oper}")
            
            if action.oper in operator_alias.keys():
                logger.info(f"Detected alias, replace {action.oper} with {operator_alias[action.oper]}")
                action.oper = operator_alias[action.oper]

            # Fetch view position
            action.view_pos_front = view_data_front[action.tile_pos[1]][action.tile_pos[0]]
            action.view_pos_side = view_data_side[action.tile_pos[1]][action.tile_pos[0]]
            
            # Perform the action
            try:
                perform_action(action, is_paused)
                excel.set_result(StatusColor.SUCCESS)
            except PerformLateError as e:
                excel.set_result(StatusColor.WARNING)
            except UserPausedError as e:
                raise ErrorToLog("用户停止。")
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