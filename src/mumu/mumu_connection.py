import win32gui
import win32con
import ctypes
import time

from src.logger import logger
from src.config import MuMuEmulatorConfig as config

__all__ = ["HANDLE"]

class WindowNotFoundException(Exception):
    """Exception raised when the game window is not found."""
    pass

# Global variables
PARENT_HANDLE: int = win32gui.FindWindow(None, config.WINDOW_NAME)
HANDLE: int = win32gui.FindWindowEx(PARENT_HANDLE, 0, None, config.SUB_WINDOW_NAME)
if PARENT_HANDLE == 0 or HANDLE == 0:
    logger.error(f"Failed to find the game window. Please open {config.WINDOW_NAME} and try again.")
    raise WindowNotFoundException("Failed to find the game window.")
else:
    logger.info(f"Found the game window with handle {HANDLE}, parent handle {PARENT_HANDLE}.")

# Restore the window if it is minimized
if win32gui.IsIconic(PARENT_HANDLE):
    win32gui.ShowWindow(PARENT_HANDLE, win32con.SW_RESTORE)
    time.sleep(0.01)

# Attempt to set the program to be DPI aware to get correct window dimensions
try:
    # Set the process to be system DPI aware (2: Per-monitor DPI aware)
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception as e:
    # Ignore the error if the function call is not supported
    logger.warning(f"Failed to set the program to be DPI aware: {e}")
