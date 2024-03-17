"""
mumu_controller.py
This module provides functions simulate mouse events directly to the game window (mumu emulator).
"""

import win32api
import win32con
import win32gui
import functools
from typing import Tuple

from src.config import MuMuEmulatorConfig as config
from src.mumu.mumu_connection import HANDLE

# Public interface
__all__ = ['pause', 'esc', 'mouseclick', 'mousedown', 'mouseup', 'mousemove']

def handle_coordinates(func):
    """
    A decorator that converts ratio coordinates to pixel coordinates and checks their validity.
    """
    @functools.wraps(func)
    def wrapper(pos: Tuple[float, float]) -> None:
        x, y = pos
        if x < 0 or x > 1 or y < 0 or y > 1:
            raise ValueError(f"Mouse coordinates ratios ({x}, {y}) are out of bounds.")
        window_rect = win32gui.GetWindowRect(HANDLE)
        w, h = window_rect[2] - window_rect[0], window_rect[3] - window_rect[1]
        return func((int(x * w), int(y * h)))
    return wrapper

def pause() -> None:
    """
    Pause the game by sending a specific message to the game window.
    """
    win32api.SendMessage(HANDLE, config.WM_XBUTTONDOWN, config.XBUTTON2, config.DEFAULT_COORDINATES)
    win32api.SendMessage(HANDLE, config.WM_XBUTTONUP, config.XBUTTON2, config.DEFAULT_COORDINATES)

def esc() -> None:
    """
    Send the ESC key to the game by sending a specific message to the game window.
    """
    win32api.SendMessage(HANDLE, config.WM_XBUTTONDOWN, config.XBUTTON1, config.DEFAULT_COORDINATES)
    win32api.SendMessage(HANDLE, config.WM_XBUTTONUP, config.XBUTTON1, config.DEFAULT_COORDINATES)

@handle_coordinates
def mouseclick(pos: Tuple[float, float]) -> None:
    """
    Simulate a mouse click at the given coordinates or ratio of window size.
    """
    win32api.SendMessage(HANDLE, win32con.WM_LBUTTONDOWN, 0, win32api.MAKELONG(*pos))
    win32api.SendMessage(HANDLE, win32con.WM_LBUTTONUP, 0, win32api.MAKELONG(*pos))

@handle_coordinates
def mousedown(pos: Tuple[float, float]) -> None:
    """
    Simulate a mouse down event at the given coordinates or ratio of window size.
    """
    win32api.SendMessage(HANDLE, win32con.WM_LBUTTONDOWN, 0, win32api.MAKELONG(*pos))

@handle_coordinates
def mouseup(pos: Tuple[float, float]) -> None:
    """
    Simulate a mouse up event at the given coordinates or ratio of window size.
    """
    win32api.SendMessage(HANDLE, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, win32api.MAKELONG(*pos))

@handle_coordinates
def mousemove(pos: Tuple[float, float]) -> None:
    """
    Simulate a mouse move event to the given coordinates or ratio of window size.
    """
    win32api.SendMessage(HANDLE, win32con.WM_MOUSEMOVE, win32con.MK_LBUTTON, win32api.MAKELONG(*pos))

if __name__ == "__main__":
    # Usage and testing
    from src.config import GameRatioConfig
    esc()
    mouseclick(GameRatioConfig.LAST_OPER_RATIO)