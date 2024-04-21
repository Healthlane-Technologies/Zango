import logging
from loguru import logger

class LoguruHandler(logging.Handler):
    def emit(self, record):
        # Translate the log record level to Loguru's levels
        level = logger.level(record.levelname).name
        logger.log(level, record.getMessage())

# Add this handler to the root logger
logging.getLogger().addHandler(LoguruHandler())
