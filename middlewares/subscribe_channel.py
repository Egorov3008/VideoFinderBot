from collections.abc import Awaitable, Callable
from typing import Any
from aiogram import BaseMiddleware, html
from aiogram.types import TelegramObject, Update, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db import get_subscription
from utils_bot.utils import is_user_subscribed
from logger import logger
from config import ADMIN_ID

class SubscribeChannel(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: Update,
            data: dict[str, Any],
    ) -> Any:
        if user := data.get("event_from_user"):
            logger.debug(f"Проверяю подписку пользователя: {user.id} на каналы")
            dict_sub = await get_subscription()
            logger.info(f"Получены подписки: {dict_sub}")

            if dict_sub:
                dict_sub_users = {
                    (channel, url_sub): await is_user_subscribed(channel_url=url_sub, telegram_id=user.id) for channel, url_sub in dict_sub.items()
                }
                logger.debug(f"Статусы подписок пользователей: {dict_sub_users}")
                len_sub = len([v for v in dict_sub_users.values() if v])
                if not any(v for v in dict_sub_users.values() if v):
                    logger.warning(f"Пользователь {user.id} не подписан на один или несколько каналов.")
                    builder = InlineKeyboardBuilder()
                    for channel, subscribed in dict_sub_users.items():

                        if not subscribed:
                            builder.row(InlineKeyboardButton(text=channel[0], url=channel[1]))
                    builder.row(InlineKeyboardButton(text="Проверить подписку 📍", callback_data="check_subscription"))
                    if event.message:
                        await event.message.answer(f"😊 Чтобы использовать бота, подпишитесь на каналы,\n перечисленные ниже"
                                                   f"и нажмите кнопку 'Проверить подписку 📍',\n как только вы подпишетесь.", reply_markup=builder.as_markup())
                        logger.info(f"Отправлено сообщение о подписке на канал пользователю {user.id}")
                    if event.callback_query:
                        await event.callback_query.message.answer(f"Вы не подписаны на каналы", reply_markup=builder.as_markup())
                        logger.info(f"Отправлено сообщение о подписке на канал пользователю {user.id} через callback_query")
                    return
                elif any(v for v in dict_sub_users.values() if v) or user.id in ADMIN_ID:
                    logger.info(f"Пользователь {user.id} подписан на все каналы или является администратором.")
                    return await handler(event, data)
            return await handler(event, data)

        logger.debug("Пользователь не найден или данные не содержат event_from_user.")


