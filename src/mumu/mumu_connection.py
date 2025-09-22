import win32gui
import win32con
import ctypes
import time
import re

from src.logger import logger
from src.config import MuMuEmulatorConfig as config

__all__ = ["HANDLE"]

class WindowNotFoundException(Exception):
    """Exception raised when the game window is not found."""
    pass


def find_window_by_regex(pattern):
    matched = []
    def enum_windows_proc(hwnd, _):
        title = win32gui.GetWindowText(hwnd)
        if re.match(pattern, title):
            matched.append(hwnd)
    win32gui.EnumWindows(enum_windows_proc, None)
    return matched

def print_child_windows(parent_handle):
    def callback(hwnd, _):
        title = win32gui.GetWindowText(hwnd)
        class_name = win32gui.GetClassName(hwnd)
        rect = win32gui.GetWindowRect(hwnd)
        print(f"Child HWND: {hwnd}, Title: '{title}', Class: '{class_name}', Rect: {rect}")
    win32gui.EnumChildWindows(parent_handle, callback, None)


# 匹配以“MuMu”开头的窗口
parent_handles = find_window_by_regex(r"^MuMu(模拟器12|安卓设备)")
if not parent_handles:
    logger.error("Failed to find the game window. Please open MuMu emulator and try again.")
    raise WindowNotFoundException("Failed to find the game window.")
PARENT_HANDLE = parent_handles[0]

# 查找子窗口
HANDLE = win32gui.FindWindowEx(PARENT_HANDLE, 0, None, "MuMuPlayer")
if HANDLE == 0:
    HANDLE = win32gui.FindWindowEx(PARENT_HANDLE, 0, None, "MuMuNxDevice")

if HANDLE == 0:
    logger.error("Failed to find the sub window 'MuMuPlayer' or 'MuMuNxDevice'.")
    # 打印所有子窗口标题，方便排查
    try:
        print_child_windows(PARENT_HANDLE)
    except Exception as e:
        print(f"打印子窗口时出错: {e}")
    raise WindowNotFoundException("Failed to find the sub window.")
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

if __name__ == "__main__":
    print_child_windows(PARENT_HANDLE)
    print(f"PARENT_HANDLE: {PARENT_HANDLE}")
    print(f"HANDLE: {HANDLE}")
