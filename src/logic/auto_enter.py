import time
from typing import Callable

from src.logger import logger
from src.config import GameRatioConfig as ratioconfig
from src.config import PerformActionConfig as actionconfig
from src.logic.game_time import GameTime
from src.logic.analyze_time import get_game_time
from src.mumu.mumu_controller import mouseclick
import time

def auto_enter() -> None:
    logger.info("Auto enter started")
    # First click the start button
    mouseclick(ratioconfig.START_BUTTON_RATIO)
    time.sleep(actionconfig.GENERAL_WAITTIME)

    # Try to pause as long as the time started to flow
    while True:
        try:
            game_time = get_game_time()
            if game_time.tick > 0:
                break
        except Exception as e:
            pass

    # Now pause
    mouseclick(ratioconfig.PAUSE_BUTTON_RATIO)
    logger.info(f"Sent pause signal at time {game_time}")
    time.sleep(actionconfig.GENERAL_WAITTIME)
    logger.info(f"Successfully paused at time {get_game_time()}")

    # Switch game speed to 2x
    mouseclick(ratioconfig.SPEED_BUTTON_RATIO)
    time.sleep(actionconfig.GENERAL_WAITTIME)
    logger.info(f"Switched game speed to 2x")

if __name__ == "__main__":
    auto_enter()
