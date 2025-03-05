from aiogram.filters import BaseFilter
from aiogram.types import Message
from config import ADMIN_ID
from logger import logger


class IsAdminFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        try:
            user = message.from_user.id
            logger.debug(f"Определяю принадлежность пользователя {user}")
            admin_ids: list[int] = ADMIN_ID
            if user in admin_ids:
                logger.info(f'Пользователь с id {message.from_user.id} является администратором')
                return True

            logger.info(f"Пользователя с id: {user} нет в списке aдминистраторов")
            return False
        except Exception as e:
            logger.error(f"Произошла ошибка: {e}")
