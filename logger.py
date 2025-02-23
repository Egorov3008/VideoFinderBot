import logging
import os
import sys
import traceback
from datetime import timedelta
from loguru import logger


log_folder = "logs"

# Создаем папку для логов, если она не существует
if not os.path.exists(log_folder):
    os.makedirs(log_folder)

# Удаляем стандартный обработчик логов
logger.remove()

# Уровни логирования
level_mapping = {
    50: "CRITICAL",
    40: "ERROR",
    30: "WARNING",
    20: "INFO",
    10: "DEBUG",
    0: "NOTSET",
}

class InterceptHandler(logging.Handler):
    def emit(self, record):
        logger_opt = logger.opt(depth=6, exception=record.exc_info)
        message = record.getMessage()

        # Добавляем информацию об исключении, если она есть
        if record.exc_info:
            # Получаем трассировку ошибки с помощью traceback
            exception_traceback = ''.join(traceback.format_exception(*record.exc_info))
            message += f"\n<red>Exception:</red> {exception_traceback}"  # Добавляем текст исключения

        logger_opt.log(level_mapping.get(record.levelno, "DEBUG"), message)


# Настройка базового логирования
logging.basicConfig(handlers=[InterceptHandler()], level=0)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Настройка логирования в консоль
logger.add(
    sys.stderr,
    level="DEBUG",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{module}:{function}:{line}</cyan> | <level>{message}</level>",
    colorize=True,
)

# Настройка логирования в файл
log_file_path = os.path.join(log_folder, "logging.log")
logger.add(
    log_file_path,
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} | {message}",
    rotation=timedelta(minutes=60),
    retention=timedelta(days=3),
)