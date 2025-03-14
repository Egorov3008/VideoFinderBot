from collections.abc import Awaitable, Callable
from typing import Any
from logger import logger
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

class DeleteMessageMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            try:
                logger.debug(f"ID удаляемого сообщения: {event.message_id}")
                if event.message_id > 1:
                    if event.text.startswith("Ищу и скачиваю") and not event.video:  # Проверяем, что сообщение не является видео
                        await event.delete()  # Удаляем текущее сообщение
            except Exception as e:
                logger.error(f"Ошибка при удалении сообщения: {e}")  # Логируем ошибку
        elif isinstance(event, CallbackQuery):
            await event.answer()
            try:
                await event.message.delete()
            except Exception as e:
                logger.error(f"Ошибка при удалении сообщения: {e}")  # Логируем ошибку
        return await handler(event, data)