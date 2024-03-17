import logging
from enum import Enum

class LogLevelColor(Enum):
    DEBUG = '\033[94m'  # Blue
    INFO = '\033[0m'   # White
    WARNING = '\033[93m' # Yellow
    ERROR = '\033[91m'  # Red
    CRITICAL = '\033[95m' # Purple
    RESET = '\033[0m'    # Reset color

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        levelname = record.levelname
        message = logging.Formatter.format(self, record)
        color = LogLevelColor[levelname].value if levelname in LogLevelColor.__members__ else LogLevelColor.RESET.value
        return f'{color}{message}{LogLevelColor.RESET.value}'

logger = logging.getLogger("DebugLogger")
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

formatter = ColoredFormatter('%(asctime)s - %(levelname)-7s - %(message)s')
ch.setFormatter(formatter)

logger.addHandler(ch)

if __name__ == "__main__":
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")