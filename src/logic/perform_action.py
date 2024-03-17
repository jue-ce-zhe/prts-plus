import time

from src.logger import logger
from src.config import GameRatioConfig as ratioconfig
from src.config import PerformActionConfig as actionconfig
from src.logic.action import Action, ActionType, DirectionType
from src.logic.game_time import GameTime
from src.logic.locate_avatar import locate_avatar
from src.logic.analyze_time import get_game_time
from src.mumu.mumu_controller import (
    pause,
    esc,
    mouseclick,
    mousedown,
    mouseup,
    mousemove,
)

BULLET_THRESHOLD = GameTime(0, actionconfig.BULLET_THRESHOLD)
FRAME_THRESHOLD = GameTime(0, actionconfig.FRAME_THRESHOLD)


class PerformActionError(Exception):
    def __init__(self, actual_time: GameTime, scheduled_time: GameTime):
        super().__init__(
            f"Performed action at {actual_time} instead of {scheduled_time}"
        )
        self.actual_time = actual_time
        self.scheduled_time = scheduled_time

    def __str__(self):
        return (
            f"Performed action at {self.actual_time} instead of {self.scheduled_time}"
        )

    def __repr__(self):
        return f"PerformActionError({self.actual_time}, {self.scheduled_time})"


def perform_deploy(action: Action) -> bool:
    on_time = True
    # Note: Pause invariant: Here the game is paused
    # First, Proceed until we reach the frame threshold
    if get_game_time() + BULLET_THRESHOLD < action.get_game_time():
        # When we have too much time, first resume, then enter bullet time when appropriate
        pause()
        while get_game_time() + BULLET_THRESHOLD < action.get_game_time():
            pass
        mouseclick(ratioconfig.LAST_OPER_RATIO)
        time.sleep(actionconfig.GENERAL_WAITTIME)
        while get_game_time() + FRAME_THRESHOLD < action.get_game_time():
            pass
        esc()
        time.sleep(actionconfig.GENERAL_WAITTIME)
    elif get_game_time() + FRAME_THRESHOLD < action.get_game_time():
        # When we are within the bullet threshold, directly enter bullet time, then resume
        mouseclick(ratioconfig.LAST_OPER_RATIO)
        time.sleep(actionconfig.GENERAL_WAITTIME)
        pause()
        while get_game_time() + FRAME_THRESHOLD < action.get_game_time():
            pass
        esc()
        time.sleep(actionconfig.GENERAL_WAITTIME)
    else:
        # When we are already within the frame threshold, directly enter bullet time, and don't resume at all
        mouseclick(ratioconfig.LAST_OPER_RATIO)
        time.sleep(actionconfig.GENERAL_WAITTIME)

    # Note: Pause invariant: Here the game is paused
    # and also, we have selected the last operator to be under bullet time
    # Now, proceed frame by frame until we reach the target time
    while get_game_time() < action.get_game_time():
        pause()
        time.sleep(actionconfig.FRAME_WAITTIME1)
        esc()
        time.sleep(actionconfig.FRAME_WAITTIME2)

    # Finally, do the action
    # Find the avatar position
    locate_avatar(action)
    mouseclick(action.avatar_pos)
    time.sleep(actionconfig.GENERAL_WAITTIME)

    # Now the operator is chosen, find avatar position again since it may have changed
    locate_avatar(action)
    middle_pos = (
        action.avatar_pos[0],
        action.avatar_pos[1] - actionconfig.DEPLOY_DRAG_RATIO,
    )

    # Deploy the operator
    pause()
    mousedown(action.avatar_pos)
    mousemove(middle_pos)
    time.sleep(actionconfig.DEPLOY_WAITTIME1)
    esc()
    time.sleep(actionconfig.DEPLOY_WAITTIME2)

    # Check if we are on time
    if get_game_time() != action.get_game_time():
        logger.warning(
            f"Game time mismatch, performed action at {get_game_time()} instead of {action.get_game_time()}"
        )
        on_time = False

    # Do the rest of the deploy
    mousemove(action.view_pos_side)
    time.sleep(actionconfig.DEPLOY_WAITTIME3)
    mouseup(action.view_pos_side)
    time.sleep(actionconfig.GENERAL_WAITTIME)

    # Set the direction
    dir_pos = None
    if action.direction == DirectionType.LEFT:
        dir_pos = (
            max(0, action.view_pos_side[0] - ratioconfig.DIRECTION_RATIO),
            action.view_pos_side[1],
        )
    elif action.direction == DirectionType.RIGHT:
        dir_pos = (
            min(1, action.view_pos_side[0] + ratioconfig.DIRECTION_RATIO),
            action.view_pos_side[1],
        )
    elif action.direction == DirectionType.UP:
        dir_pos = (
            action.view_pos_side[0],
            max(0, action.view_pos_side[1] - ratioconfig.DIRECTION_RATIO),
        )
    elif action.direction == DirectionType.DOWN:
        dir_pos = (
            action.view_pos_side[0],
            min(1, action.view_pos_side[1] + ratioconfig.DIRECTION_RATIO),
        )
    if dir_pos:
        mousedown(action.view_pos_side)
        time.sleep(actionconfig.GENERAL_WAITTIME)
        mousemove(dir_pos)
        time.sleep(actionconfig.GENERAL_WAITTIME)
        mouseup(dir_pos)
        time.sleep(actionconfig.GENERAL_WAITTIME)

    # Note: Pause invariant: Here the game is paused
    return on_time


def perform_skill_or_retreat(action: Action):
    on_time = True
    # Note: Pause invariant: Here the game is paused
    # First, Proceed until we reach the bullet threshold
    if get_game_time() + BULLET_THRESHOLD < action.get_game_time():
        # When we have too much time, first resume, then enter bullet time when appropriate
        pause()
        while get_game_time() + BULLET_THRESHOLD < action.get_game_time():
            pass
        mouseclick(action.view_pos_front)
        time.sleep(actionconfig.GENERAL_WAITTIME)
        while get_game_time() + FRAME_THRESHOLD < action.get_game_time():
            pass
        esc()
        time.sleep(actionconfig.GENERAL_WAITTIME)
    elif get_game_time() + FRAME_THRESHOLD < action.get_game_time():
        # When we are within the bullet threshold, resume and enter bullet time, quickly
        pause()
        mouseclick(action.view_pos_front)
        time.sleep(actionconfig.GENERAL_WAITTIME)
        while get_game_time() + FRAME_THRESHOLD < action.get_game_time():
            pass
        esc()
        time.sleep(actionconfig.GENERAL_WAITTIME)
    else:
        # When we are already within the frame threshold, enter side view first, then try to click
        # Note: Here the click may fail, since it is not guaranteed that the operator can be selected from side view
        # Ex. the leftmost deployable position in the middle row of 1-7
        mouseclick(ratioconfig.LAST_OPER_RATIO)
        pause()
        mouseclick(action.view_pos_side)
        time.sleep(actionconfig.GENERAL_WAITTIME)
        esc()
        time.sleep(actionconfig.GENERAL_WAITTIME)

    # Note: Pause invariant: Here the game is paused
    # and also, we have selected the target operator to be under bullet time
    # Now, proceed frame by frame until we reach the target time
    while get_game_time() < action.get_game_time():
        pause()
        time.sleep(actionconfig.FRAME_WAITTIME1)
        esc()
        time.sleep(actionconfig.FRAME_WAITTIME2)

    # Check if we are on time
    if get_game_time() != action.get_game_time():
        logger.warning(
            f"Game time mismatch, performed action at {get_game_time()} instead of {action.get_game_time()}"
        )
        on_time = False

    # Finally, do the action
    if action.action_type == ActionType.SKILL:
        mouseclick(ratioconfig.SKILL_RATIO)
        time.sleep(actionconfig.GENERAL_WAITTIME)
    elif action.action_type == ActionType.RETREAT:
        mouseclick(ratioconfig.RETREAT_RATIO)
        time.sleep(actionconfig.GENERAL_WAITTIME)
    else:
        raise ValueError(f"Invalid action type: {action.action_type}")

    # Note: Pause invariant: Here the game is paused
    return on_time


def perform_action(action: Action):
    logger.debug(f"Performing action: {action}")
    # Note: Pause invariant: Here the game is paused

    on_time = True
    if action.action_type == ActionType.DEPLOY:
        on_time = perform_deploy(action)
    elif (
        action.action_type == ActionType.SKILL
        or action.action_type == ActionType.RETREAT
    ):
        on_time = perform_skill_or_retreat(action)
    else:
        raise ValueError(f"Invalid action type: {action.action_type}")

    # Note: Pause invariant: Here the game is paused
    logger.info(f"Performed action: {action}")

    if not on_time:
        raise PerformActionError(f"Performed action: {action} (not on time)")


if __name__ == "__main__":
    # Usage and testing
    from src.cache import get_map_by_code
    from src.logic.calc_view import transform_map_to_view
    from src.logic.action import DirectionType

    map = get_map_by_code("1-7")
    view_map_front = transform_map_to_view(map, False)
    view_map_side = transform_map_to_view(map, True)
    action = Action(
        14,
        0,
        ActionType.DEPLOY,
        "山",
        1,
        3,
        DirectionType.RIGHT,
        "",
        None,
        view_map_front[3][1],
        view_map_side[3][1],
    )
    start_time = time.time()
    perform_action(action)
    end_time = time.time()
    logger.info(
        f"Action performed: {action} (time elapsed: {end_time - start_time:.3f} seconds)"
    )
