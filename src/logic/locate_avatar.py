import cv2

from src.cache import get_avatars, replace_avatar
from src.logic.action import Action
from src.mumu.mumu_vision import capture_game_window
from src.logger import logger
from src.config import GameRatioConfig as ratioconfig
from src.config import ImageProcessingConfig as imgconfig
from src.utils.error_to_log import ErrorToLog

def locate_avatar(action: Action) -> None:
    """
    Locate the exact location of the avatar on game screen. Modify the action object in place.
    """
    avatars = get_avatars(action.oper)
    oper_area_img = capture_game_window(ratioconfig.OPERATOR_AREA_RATIO)

    max_val, max_pos, max_avatar = 0, None, None
    for avatar in avatars:
        matched = cv2.matchTemplate(oper_area_img, avatar, cv2.TM_CCOEFF_NORMED)
        _, val, _, pos = cv2.minMaxLoc(matched)
        if val > max_val:
            max_val, max_pos, max_avatar = val, pos, avatar
    
    if max_val < imgconfig.TEMPLATE_MATCH_THRESHOLD:
        logger.error(f"Could not find a good matching avatar for {action.oper}, with max_val: {max_val}")
        raise ErrorToLog(f"未在待部署区找到干员{action.oper}。")
    
    if len(avatars) > 1:
        logger.info(f"Found best matching avatar for {action.oper}")
        replace_avatar(action.oper, max_avatar)
    
    # Add the avatar position to the action, in ratio
    avatar_ratio_x = ratioconfig.OPERATOR_AREA_RATIO[0] + (max_pos[0] + max_avatar.shape[1] / 2) / imgconfig.SCREEN_STANDARD_SIZE[0]
    avatar_ratio_y = ratioconfig.OPERATOR_AREA_RATIO[1] + (max_pos[1] + max_avatar.shape[0] / 2) / imgconfig.SCREEN_STANDARD_SIZE[1]
    action.avatar_pos = (avatar_ratio_x, avatar_ratio_y)
    logger.info(f"Avatar position of {action.oper} found at: {max_pos}, max_val: {max_val}")

if __name__ == "__main__":
    # Usage and testing
    from time import time

    start_time = time()
    action = Action(oper='令')
    locate_avatar(action)
    end_time = time()
    logger.info(f"Avatar position found at: {action.avatar_pos}, time taken: {end_time - start_time:.4f} seconds")