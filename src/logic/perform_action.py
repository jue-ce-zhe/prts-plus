import time
from typing import Callable

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


class PerformLateError(Exception):
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


class UserPausedError(Exception):
    pass


def wait_until_threshold(
    target_time: GameTime, threshold: GameTime, user_paused: Callable[[], bool]
) -> None:
    while get_game_time() + threshold < target_time:
        if user_paused():
            # Pause the game first
            esc()
            raise UserPausedError()


def perform_deploy(
    action: Action,
    user_paused: Callable[[], bool],
    BULLET_THRESHOLD: GameTime,
    FRAME_THRESHOLD: GameTime,
) -> GameTime:
    target_time = action.get_game_time()
    # Note: Pause invariant: Here the game is paused
    # First, Proceed until we reach the frame threshold
    if get_game_time() + BULLET_THRESHOLD < target_time:
        # When we have too much time, first resume, then enter bullet time when appropriate
        logger.debug(f"Too much time, resuming and entering bullet time")
        pause()
        wait_until_threshold(target_time, BULLET_THRESHOLD, user_paused)
        mouseclick(ratioconfig.LAST_OPER_RATIO)
        time.sleep(actionconfig.GENERAL_WAITTIME)
        wait_until_threshold(target_time, FRAME_THRESHOLD, user_paused)
        esc()
        time.sleep(actionconfig.GENERAL_WAITTIME)
    elif get_game_time() + FRAME_THRESHOLD < target_time:
        # When we are within the bullet threshold, directly enter bullet time, then resume
        logger.debug(f"Within bullet threshold, entering bullet time")
        mouseclick(ratioconfig.LAST_OPER_RATIO)
        time.sleep(actionconfig.GENERAL_WAITTIME)
        pause()
        wait_until_threshold(target_time, FRAME_THRESHOLD, user_paused)
        esc()
        time.sleep(actionconfig.GENERAL_WAITTIME)
    else:
        # When we are already within the frame threshold, directly enter bullet time, and don't resume at all
        logger.debug(f"Within frame threshold, entering bullet time")
        mouseclick(ratioconfig.LAST_OPER_RATIO)
        time.sleep(actionconfig.GENERAL_WAITTIME)

    # Note: Pause invariant: Here the game is paused
    # and also, we have selected the last operator to be under bullet time
    # Now, proceed frame by frame until we reach the target time
    while get_game_time() < target_time:
        pause()
        time.sleep(actionconfig.FRAME_WAITTIME)
        esc()
        if user_paused():
            raise UserPausedError()
        time.sleep(actionconfig.GENERAL_WAITTIME)

    # Finally, do the action
    # Find the avatar position
    locate_avatar(action)

    # Check if we have actually already selected the operator
    # This may happen when the target operator is the last operator
    if action.avatar_pos[1] < ratioconfig.OPERATOR_SELECTED_RATIO:
        logger.debug(f"Operator {action.oper} is already selected")
    else:
        # Select the operator
        mouseclick(action.avatar_pos)
        time.sleep(actionconfig.GENERAL_WAITTIME)

        # Now the operator is selected, find avatar position again since it may have changed
        locate_avatar(action)

    # Calculate the middle position for dragging
    middle_pos = (
        action.avatar_pos[0],
        action.avatar_pos[1] - ratioconfig.DEPLOY_DRAG_RATIO,
    )

    # Note: Pause invariant: Here the game is paused

    # Final check if user paused
    if user_paused():
        raise UserPausedError()

    # Deploy the operator
    pause()
    mousedown(action.avatar_pos)
    mousemove(middle_pos)
    time.sleep(actionconfig.MINIMUM_WAITTIME)
    esc()
    time.sleep(actionconfig.GENERAL_WAITTIME)

    # Check if we are on time
    actual_time = get_game_time()
    if actual_time != target_time:
        logger.warning(
            f"Game time mismatch, performed action at {actual_time} instead of {target_time}"
        )

    # Do the rest of the deploy
    mousemove((action.view_pos_side[0], action.view_pos_side[1] + ratioconfig.DEPLOY_DELTA_RATIO))
    time.sleep(actionconfig.GENERAL_WAITTIME)
    mouseup((action.view_pos_side[0], action.view_pos_side[1] + ratioconfig.DEPLOY_DELTA_RATIO))
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
    return actual_time


def perform_skill_or_retreat(
    action: Action,
    user_paused: Callable[[], bool],
    BULLET_THRESHOLD: GameTime,
    FRAME_THRESHOLD: GameTime,
) -> GameTime:
    target_time = action.get_game_time()
    # Note: Pause invariant: Here the game is paused
    # First, Proceed until we reach the bullet threshold
    if get_game_time() + BULLET_THRESHOLD < target_time:
        # When we have too much time, first resume, then enter bullet time when appropriate
        logger.debug(f"Too much time, resuming and entering bullet time")
        pause()
        wait_until_threshold(target_time, BULLET_THRESHOLD, user_paused)
        mouseclick(action.view_pos_front)
        time.sleep(actionconfig.GENERAL_WAITTIME)
        wait_until_threshold(target_time, FRAME_THRESHOLD, user_paused)
        esc()
        time.sleep(actionconfig.GENERAL_WAITTIME)
    elif get_game_time() + FRAME_THRESHOLD < target_time:
        # When we are within the bullet threshold, resume and enter bullet time, quickly
        logger.debug(f"Within bullet threshold, entering bullet time")
        pause()
        mouseclick(action.view_pos_front)
        time.sleep(actionconfig.GENERAL_WAITTIME)
        wait_until_threshold(target_time, FRAME_THRESHOLD, user_paused)
        esc()
        time.sleep(actionconfig.GENERAL_WAITTIME)
    else:
        # When we are already within the frame threshold, enter side view first, then try to click
        # Note: Here the click may fail, since it is not guaranteed that the operator can be selected from side view
        # Ex. the leftmost deployable position in the middle row of 1-7
        logger.debug(f"Within frame threshold, entering side view")
        mouseclick(ratioconfig.LAST_OPER_RATIO)
        time.sleep(actionconfig.GENERAL_WAITTIME)
        pause()
        mouseclick(action.view_pos_side)
        time.sleep(actionconfig.MINIMUM_WAITTIME)
        esc()
        time.sleep(actionconfig.GENERAL_WAITTIME)

    # Note: Pause invariant: Here the game is paused
    # and also, we have selected the target operator to be under bullet time
    # Now, proceed frame by frame until we reach the target time
    while get_game_time() < target_time:
        pause()
        time.sleep(actionconfig.FRAME_WAITTIME)
        esc()
        if user_paused():
            raise UserPausedError()
        time.sleep(actionconfig.GENERAL_WAITTIME)

    # Check if we are on time
    actual_time = get_game_time()
    if actual_time != target_time:
        logger.warning(
            f"Game time mismatch, performed action at {actual_time} instead of {target_time}"
        )

    # Final check if user paused
    if user_paused():
        raise UserPausedError()

    # Finally, do the action
    # time.sleep(actionconfig.GENERAL_WAITTIME)
    if action.action_type == ActionType.SKILL:
        mouseclick(ratioconfig.SKILL_RATIO)
        time.sleep(actionconfig.GENERAL_WAITTIME)
    elif action.action_type == ActionType.RETREAT:
        mouseclick(ratioconfig.RETREAT_RATIO)
        time.sleep(actionconfig.GENERAL_WAITTIME)
    else:
        raise ValueError(f"Invalid action type: {action.action_type}")

    # Note: Pause invariant: Here the game is paused
    return actual_time


def perform_action(action: Action, user_paused: Callable[[], bool]) -> None:
    logger.debug(f"Performing action: {action}")
    # Note: Pause invariant: Here the game is paused

    BULLET_THRESHOLD = GameTime(0, actionconfig.BULLET_THRESHOLD)
    FRAME_THRESHOLD = GameTime(0, actionconfig.FRAME_THRESHOLD)

    actual_time = action.get_game_time()
    if action.action_type == ActionType.DEPLOY:
        actual_time = perform_deploy(action, user_paused, BULLET_THRESHOLD, FRAME_THRESHOLD)
    elif (
        action.action_type == ActionType.SKILL
        or action.action_type == ActionType.RETREAT
    ):
        actual_time = perform_skill_or_retreat(
            action, user_paused, BULLET_THRESHOLD, FRAME_THRESHOLD
        )
    else:
        raise ValueError(f"Invalid action type: {action.action_type}")

    # Note: Pause invariant: Here the game is paused
    if actual_time == action.get_game_time():
        logger.info(f"Performed action: {action}")
    elif actual_time > action.get_game_time():
        logger.warning(f"Performed action: {action} (not on time)")
        raise PerformLateError(actual_time, action.get_game_time())
    else:
        logger.error(f"Performed action: {action} (unexpected time)")
        raise PerformLateError(actual_time, action.get_game_time())


if __name__ == "__main__":
    # Usage and testing
    from src.cache import get_map_by_code
    from src.logic.calc_view import transform_map_to_view
    from src.logic.action import DirectionType

    map = get_map_by_code("1-7")
    view_map_front = transform_map_to_view(map, False)
    view_map_side = transform_map_to_view(map, True)
    action = Action(
        15,
        0,
        ActionType.DEPLOY,
        "斑点",
        "D2",
        DirectionType.RIGHT,
        "",
        (1, 3),
        None,
        view_map_front[3][1],
        view_map_side[3][1],
    )
    start_time = time.time()
    perform_action(action, lambda: False)
    end_time = time.time()
    logger.info(
        f"Action performed: {action} (time elapsed: {end_time - start_time:.3f} seconds)"
    )
