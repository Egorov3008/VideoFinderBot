import re

from aiogram.filters import BaseFilter
from aiogram.types import Message
from logger import logger


class IsValidUrl(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        try:
            url = message.text
            logger.debug(f"Проверяю ссылку {url}")
            pattern = r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/[\w-]{11}|instagram\.com/[\w.-]+|vk\.com/[\w.-]+|tiktok\.com/@[\w.-]+|pinterest\.com/[\w.-]+)(/)?$'
            return bool(re.match(pattern, url))
        except Exception as e:
            logger.error(f"Произошла ошибка: {e}")