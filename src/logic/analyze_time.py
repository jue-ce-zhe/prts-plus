import cv2
from PIL import Image
import numpy as np
import tesserocr
from functools import lru_cache

from src.config import GameRatioConfig as ratioconfig
from src.config import ImageProcessingConfig as imgconfig
from src.logic.game_time import GameTime
from src.mumu.mumu_vision import capture_game_window
from src.utils.error_to_log import ErrorToLog
from src.logger import logger

@lru_cache(maxsize=120)
def get_tick(cost_bar_area_bytes: bytes) -> int:
    """
    Calculate the current game tick based on the ratio of white pixels in the cost bar image.
    
    This function assumes that the game represents time progression by filling a bar with white color in the cost area.
    The 'tick' is then the proportion of the bar that is filled.
    
    Args:
        cost_bar_area_bytes (bytes): A byte string representing a black and white image of the cost bar.
    
    Returns:
        int: The current game tick, scaled to be between 0 and GameTime.TICK_MAX - 1.
    """
    # Convert the byte string back to a numpy array
    cost_bar_area = np.frombuffer(cost_bar_area_bytes, dtype=np.uint8)

    # Calculate the ratio of white pixels (value 255) in the cost bar image
    white_ratio = np.mean(cost_bar_area == 255)

    # Scale the white_ratio to the range 0 to GameTime.TICK_MAX - 1 and round to the nearest integer
    return round(white_ratio * (GameTime.TICK_MAX - 1))

@lru_cache(maxsize=120)
def get_cost(cost_number_area_bytes: bytes, width: int, height: int) -> int:
    """
    Extract the current cost from the game window using OCR.
    
    This function assumes that the cost is displayed as a number in a specific area of the game window.
    It uses Tesseract to perform OCR and extract the cost number.
    
    Args:
        cost_number_area_bytes (bytes): A byte string representing a black and white image of the cost number area.
        width (int): The width of the cost number area.
        height (int): The height of the cost number area.
    
    Returns:
        int: The current cost. Returns -1 if the OCR operation fails.
    """
    # Convert the byte string back to an image
    cost_number_area = Image.frombytes('L', (width, height), cost_number_area_bytes)

    # Use Tesseract to perform OCR on the cost number area with a pretrained model for Arknights digit recognition
    with tesserocr.PyTessBaseAPI(lang='arknights_digit', psm=tesserocr.PSM.SINGLE_WORD) as api:
        api.SetImage(cost_number_area)
        cost = api.GetUTF8Text()
        confidence = api.MeanTextConf()
        if confidence < imgconfig.OCR_CONFIDENCE_THRESHOLD:
            raise ErrorToLog(f"无法识别当前费用。")

    # Filter out any non-digit characters from the OCR result
    cost = "".join(filter(str.isdigit, cost))

    # Convert the OCR result to an integer, or return -1 if it's not a valid number
    try:
        cost = int(cost)
    except ValueError:
        raise ErrorToLog(f"无法识别当前费用。")

    return cost

def get_game_time() -> GameTime:
    """
    Get the current game time from the game window.
    
    Returns:
        GameTime: The current game time.
    """
    # Capture the game window and convert to grayscale and then to black and white
    cost_area_img = capture_game_window(ratio=ratioconfig.COST_AREA_RATIO)
    _, cost_area_img = cv2.threshold(cost_area_img, imgconfig.WHITE_THRESHOLD, 255, cv2.THRESH_BINARY)

    # Get the tick count from the last row of pixels in the cost bar area
    # Convert the image data to bytes for caching in get_tick function
    cost_bar_area = cost_area_img[-1, :]
    tick = get_tick(cost_bar_area.tobytes())

    # Get the cost from the number displayed in the cost number area
    # Convert the image data to bytes for caching in get_cost function
    left = int(cost_area_img.shape[1] * ratioconfig.COST_NUMBER_AREA_RATIO[0])
    upper = int(cost_area_img.shape[0] * ratioconfig.COST_NUMBER_AREA_RATIO[1])
    right = int(cost_area_img.shape[1] * ratioconfig.COST_NUMBER_AREA_RATIO[2])
    lower = int(cost_area_img.shape[0] * ratioconfig.COST_NUMBER_AREA_RATIO[3])

    cost_number_area = cost_area_img[upper:lower, left:right]
    cost = get_cost(cost_number_area.tobytes(), cost_number_area.shape[1], cost_number_area.shape[0])
    
    return GameTime(cost, tick)

if __name__ == "__main__":
    # Usage and testing
    import time
    from src.logger import logger
    start_time = time.time()
    game_time = get_game_time()
    end_time = time.time()
    logger.info(f"Game time: {game_time} (time elapsed: {end_time - start_time:.3f} seconds)")

    # Test caching
    start_time = time.time()
    game_time = get_game_time()
    end_time = time.time()
    logger.info(f"Game time: {game_time} (time elapsed: {end_time - start_time:.3f} seconds)")