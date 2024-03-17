import time

from src.logger import logger
from src.config import GameRatioConfig as ratioconfig
from src.config import PerformActionConfig as actionconfig
from src.logic.action import Action, ActionType, DirectionType
from src.logic.game_time import GameTime
from src.logic.locate_avatar import locate_avatar
from src.logic.analyze_time import get_game_time
from src.mumu.mumu_controller import pause, esc, mouseclick, mousedown, mouseup, mousemove

BULLET_THRESHOLD = GameTime(0, actionconfig.BULLET_THRESHOLD)
FRAME_THRESHOLD = GameTime(0, actionconfig.FRAME_THRESHOLD)

def perform_action(action: Action):
    logger.debug(f"Performing action: {action}")
    # Note: Pause invariant: Here the game is paused
    # First, Proceed until we reach the bullet threshold
    pause()

    while get_game_time() + BULLET_THRESHOLD < action.get_game_time():
        pass
    mouseclick(ratioconfig.LAST_OPER_RATIO)
    time.sleep(actionconfig.GENERAL_WAITTIME)

    # Second, click the area of interest
    if action.action_type != ActionType.DEPLOY:
        mouseclick(action.view_pos)
        time.sleep(actionconfig.GENERAL_WAITTIME)

    # Third, Proceed until we reach the frame threshold
    while get_game_time() + FRAME_THRESHOLD < action.get_game_time():
        pass
    esc()
    time.sleep(actionconfig.GENERAL_WAITTIME)

    # Note: Pause invariant: Here the game is paused
    # Fourth, proceed frame by frame until we reach the target time
    while get_game_time() < action.get_game_time():
        pause()
        time.sleep(actionconfig.FRAME_WAITTIME1)
        esc()
        time.sleep(actionconfig.FRAME_WAITTIME2)
    
    # Finally, do the action
    if action.action_type == ActionType.SKILL:
        mouseclick(ratioconfig.SKILL_RATIO)
        time.sleep(actionconfig.GENERAL_WAITTIME)
    elif action.action_type == ActionType.RETREAT:
        # RETREAT_RATIO
        mouseclick(ratioconfig.RETREAT_RATIO)
        time.sleep(actionconfig.GENERAL_WAITTIME)
    else:
        # Find the avatar position first
        locate_avatar(action)
        mouseclick(action.avatar_pos)
        time.sleep(actionconfig.GENERAL_WAITTIME)

        # Now the operator is chosen, find avatar position again
        locate_avatar(action)
        middle_pos = (action.avatar_pos[0], action.avatar_pos[1] - actionconfig.DEPLOY_DRAG_RATIO)

        # Deploy the operator
        pause()
        mousedown(action.avatar_pos)
        mousemove(middle_pos)
        time.sleep(actionconfig.DEPLOY_WAITTIME1)
        esc()
        time.sleep(actionconfig.DEPLOY_WAITTIME2)
        mousemove(action.view_pos)
        time.sleep(actionconfig.DEPLOY_WAITTIME3)
        mouseup(action.view_pos)
        time.sleep(actionconfig.GENERAL_WAITTIME)

        # Set the direction
        dir_pos = None
        if action.direction == DirectionType.LEFT:
            dir_pos = (max(0, action.view_pos[0] - ratioconfig.DIRECTION_RATIO), action.view_pos[1])
        elif action.direction == DirectionType.RIGHT:
            dir_pos = (min(1, action.view_pos[0] + ratioconfig.DIRECTION_RATIO), action.view_pos[1])
        elif action.direction == DirectionType.UP:
            dir_pos = (action.view_pos[0], max(0, action.view_pos[1] - ratioconfig.DIRECTION_RATIO))
        elif action.direction == DirectionType.DOWN:
            dir_pos = (action.view_pos[0], min(1, action.view_pos[1] + ratioconfig.DIRECTION_RATIO))
        if dir_pos:
            mousedown(action.view_pos)
            time.sleep(actionconfig.GENERAL_WAITTIME)
            mousemove(dir_pos)
            time.sleep(actionconfig.GENERAL_WAITTIME)
            mouseup(dir_pos)
            time.sleep(actionconfig.GENERAL_WAITTIME)
    
    # Note: Pause invariant: Here the game is paused
    logger.info(f"Performed action: {action}")
    if get_game_time() != action.get_game_time():
        logger.warning(f"Game time mismatch, performed action at {get_game_time()} instead of {action.get_game_time()}")

if __name__ == "__main__":
    # Usage and testing
    from src.cache import get_map_by_code
    from src.logic.calc_view import transform_map_to_view
    from src.logic.action import DirectionType
    map = get_map_by_code('1-7')
    view_map = transform_map_to_view(map, True)
    action = Action(12, 0, ActionType.DEPLOY, "山", 1, 3, DirectionType.RIGHT, "", None, view_map[3][1])
    start_time = time.time()
    perform_action(action)
    end_time = time.time()
    logger.info(f"Action performed: {action} (time elapsed: {end_time - start_time:.3f} seconds)")