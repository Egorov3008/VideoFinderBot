from collections.abc import Awaitable, Callable
from typing import Any
from  logger import logger
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from db import add_user


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if user := data.get("event_from_user"):
            logger.debug(f"user: {user}")
            await self._process_user(user)
        return await handler(event, data)

    async def _process_user(self, user: User) -> None:
        await add_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name
        )
