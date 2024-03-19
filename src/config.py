class MuMuEmulatorConfig:
    DEFAULT_COORDINATES = 0x00640064
    WINDOW_NAME = "MuMu模拟器12"
    SUB_WINDOW_NAME = "MuMuPlayer"
    WM_XBUTTONDOWN = 0x020B
    WM_XBUTTONUP = 0x020C
    XBUTTON1 = 0x00010000
    XBUTTON2 = 0x00020000

class GameRatioConfig:
    COST_AREA_RATIO = (0.906, 0.685, 1, 0.755) # (left, top, right, bottom)
    COST_NUMBER_AREA_RATIO = (0.33, 0, 1, 0.9) # (left, top, right, bottom)
    OPERATOR_AREA_RATIO = (0, 0.8, 1, 1) # (left, top, right, bottom)
    LAST_OPER_RATIO = (0.95, 0.9) # (x, y)
    RETREAT_RATIO = (0.46, 0.3) # (x, y)
    SKILL_RATIO = (0.7, 0.6) # (x, y)
    DIRECTION_RATIO = 0.2
    DEPLOY_DRAG_RATIO = 0.03

class ImageProcessingConfig:
    WHITE_THRESHOLD = 160
    SCREEN_STANDARD_SIZE = (1280, 720)
    AVATAR_STANDARD_SIZE = (120, 120)
    AVATAR_CROP_SIZE = (60, 60)

class ViewCalculationConfig:
    FROM_RATIO = 9 / 16
    TO_RATIO = 3 / 4
    NEAR = 0.3
    FAR = 1000

class GameTimeConfig:
    TICK_MAX_DEFAULT = 30 # default 1 second = 30 ticks

class PerformActionConfig:
    BULLET_THRESHOLD = 20
    FRAME_THRESHOLD = 2
    MINIMUM_WAITTIME = 0.02
    FRAME_WAITTIME = 0.1
    GENERAL_WAITTIME = 0.3