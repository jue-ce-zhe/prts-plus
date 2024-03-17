import win32gui
import win32ui
import win32con
import cv2
import numpy as np
from typing import Tuple, Optional

from src.config import ImageProcessingConfig as imgconfig
from src.mumu.mumu_connection import HANDLE

__all__ = ["capture_game_window"]

def capture_game_window(ratio: Optional[Tuple[float, float, float, float]] = None) -> np.array:
    """
    Take a screenshot of a specific window and a specific area.
    
    Args:
        ratio (Tuple[float, float, float, float], optional): Relative coordinates (ratios) of the area to capture.
                                                            [left_ratio, top_ratio, right_ratio, bottom_ratio]

    Returns:
        np.array: Captured image.

    Raises:
        ValueError: If the title is empty, rect dimensions are invalid, or both rect and ratio are provided.
        WindowNotFoundException: If the window is not found.
    """
    # Default to capturing the entire window
    if ratio is None:
        ratio = (0, 0, 1, 1)

    # Check if ratio is valid
    if len(ratio) != 4:
        raise ValueError(f"Ratio must be a tuple of 4 floats, given as (left, top, right, bottom). However, {ratio} was given.")
    if not all(0 <= x <= 1 for x in ratio):
        raise ValueError(f"Ratio values must be between 0 and 1. However, {ratio} was given.")
    if ratio[0] >= ratio[2] or ratio[1] >= ratio[3]:
        raise ValueError(f"Invalid ratio values. Left and top must be less than right and bottom. However, {ratio} was given.")

    # Calculate the area to capture
    left, top, right, bottom = win32gui.GetWindowRect(HANDLE)
    window_width = right - left
    window_height = bottom - top
    rect = (int(window_width * ratio[0]), int(window_height * ratio[1]), 
            int(window_width * ratio[2]), int(window_height * ratio[3]))

    try:
        # Get the window's device context
        window_dc = win32gui.GetWindowDC(HANDLE)
        mfcDC = win32ui.CreateDCFromHandle(window_dc)
        saveDC = mfcDC.CreateCompatibleDC()

        # Calculate the dimensions and position of the area to capture
        capture_left, capture_top, capture_right, capture_bottom = rect
        capture_width, capture_height = capture_right - capture_left, capture_bottom - capture_top

        # Create a bitmap to hold the screenshot
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, capture_width, capture_height)
        saveDC.SelectObject(saveBitMap)

        # Capture the specified area
        saveDC.BitBlt((0, 0), (capture_width, capture_height), mfcDC, (capture_left, capture_top), win32con.SRCCOPY)

        # Convert the bitmap to a NumPy array
        bmpinfo = saveBitMap.GetInfo()
        signedIntsArray = saveBitMap.GetBitmapBits(True)
        img = np.frombuffer(signedIntsArray, dtype='uint8')
        img.shape = (bmpinfo['bmHeight'], bmpinfo['bmWidth'], 4)

        # Note: Decide to use grayscale for better performance and image processing
        # Convert from BGRA to grayscale
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)

        # Resize the image to standard size
        standardized_width = capture_width * imgconfig.SCREEN_STANDARD_SIZE[0] // window_width
        standardized_height = capture_height * imgconfig.SCREEN_STANDARD_SIZE[1] // window_height
        img = cv2.resize(img, (standardized_width, standardized_height))
    finally:
        # Free resources
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(HANDLE, window_dc)

    # Return the image
    return img

if __name__ == "__main__":
    # Usage and testing
    from time import time
    from src.config import GameRatioConfig as ratioconfig
    from src.logger import logger

    start_time = time()
    img = capture_game_window(ratio=ratioconfig.COST_AREA_RATIO)
    end_time = time()
    logger.info(f"Time taken: {end_time - start_time:.4f} seconds")
    
    # Display the image
    cv2.imshow("Game Window", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
