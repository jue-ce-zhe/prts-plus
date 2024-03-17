import argparse

from src.logger import logger
from src.excel import Excel, StatusColor
from src.logic.perform_action import perform_action
from src.logic.calc_view import transform_map_to_view
from src.logic.game_time import GameTime
from src.logic.action import ActionType
from src.cache import get_map_by_code, get_map_by_name

if __name__ == '__main__':
    # Take the only parameter as the Excel file path
    parser = argparse.ArgumentParser(description='PRTS+')
    parser.add_argument('--xlsm', type=str, help='The path to the Excel file')

    file_path = parser.parse_args().xlsm
    logger.info(f"Parsed Argument: {file_path}")
    excel = Excel(file_path)
    map_code = excel.get_map_code()
    max_tick = excel.get_max_tick()

    # Load the map
    map_data = get_map_by_code(map_code)
    view_data_front = transform_map_to_view(map_data, False)
    view_data_side = transform_map_to_view(map_data, True)

    # Set max tick
    GameTime.set_tick_max(max_tick)

    # Setup operator location map
    operator_loc = {}

    # Main loop
    while not excel.is_paused():
        action = excel.get_current_action()
        if not action.is_valid():
            logger.warning(f"Invalid action: {action}")
            logger.info("Terminating the program")
            break

        if action.action_type == ActionType.DEPLOY:
            operator_loc[action.oper] = (action.pos_x, action.pos_y)
            logger.info(f"Memorized {action.oper} location at {operator_loc[action.oper]}")
        else:
            if action.pos_x is None or action.pos_y is None:
                action.pos_x, action.pos_y = operator_loc[action.oper]
                logger.info(f"Auto set {action.oper} location to {action.pos_x}, {action.pos_y}")

        action.view_pos_front = view_data_front[action.pos_y][action.pos_x]
        action.view_pos_side = view_data_side[action.pos_y][action.pos_x]
        
        try:
            perform_action(action)
            excel.set_result(StatusColor.SUCCESS)
        except Exception as e:
            logger.error(f"Error occurred: {e}")
            excel.set_result(StatusColor.FAILURE)
            raise

        excel.next_action()
    
    excel.set_paused()