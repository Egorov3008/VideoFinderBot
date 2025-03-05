import asyncio

from aiogram.enums import ContentType, ChatMemberStatus
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot import bot
from logger import logger


async def check_bot_status(channel_username: str) -> bool | str:
    try:
        # Получаем ID бота
        bot_id = (await bot.get_me()).id
        logger.info(f"ID бота: {bot_id}")

        member = await bot.get_chat_member(chat_id=f"@{channel_username}", user_id=bot_id)

        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
            logger.info(f"Бот является администратором канала {channel_username}.")
            return True
        else:
            logger.info(f"Бот не является участником канала {channel_username}.")
            return False
    except Exception as e:
        logger.error(f"Ошибка при проверке статуса бота: {e}")
        return False


async def is_user_subscribed(channel_url: str, telegram_id: int) -> bool:
    channel_username = channel_url.split('/')[-1]
    logger.info(f"username канала: {channel_username}")
    chech_bot = await check_bot_status(channel_username)
    if chech_bot:
        try:

            logger.debug(f"Проверка подписки пользователя {telegram_id} на канал: {channel_username}")

            # Получаем информацию о пользователе в канале
            member = await bot.get_chat_member(chat_id=f"@{channel_username}", user_id=telegram_id)
            logger.info(f"Статус подписки пользователя {telegram_id} для канала {channel_username}: {member.status}")

            # Проверяем статус пользователя
            if member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR]:
                return True
            else:
                return False
        except Exception as e:
            # Если возникла ошибка (например, пользователь не найден или бот не имеет доступа к каналу)
            logger.error(
                f"Ошибка при проверке подписки для пользователя {telegram_id} на канал {channel_username}: {e}")
            return False


async def broadcast_message(users_data: list, text: str = None, photo_id: int = None, document_id: int = None,
                            video_id: int = None, audio_id: int = None, caption: str = None, content_type: str = None):
    good_send = 0
    bad_send = 0

    for user in users_data:
        try:
            chat_id = user.get('telegram_id')
            if content_type == ContentType.TEXT:
                await bot.send_message(chat_id=chat_id, text=text)
            elif content_type == ContentType.PHOTO:
                await bot.send_photo(chat_id=chat_id, photo=photo_id, caption=caption)
            elif content_type == ContentType.DOCUMENT:
                await bot.send_document(chat_id=chat_id, document=document_id, caption=caption)
            elif content_type == ContentType.VIDEO:
                await bot.send_video(chat_id=chat_id, video=video_id, caption=caption)
            elif content_type == ContentType.AUDIO:
                await bot.send_audio(chat_id=chat_id, audio=audio_id, caption=caption)
            good_send += 1
        except Exception as e:
            print(e)
            bad_send += 1
        finally:
            await asyncio.sleep(1)
    return good_send, bad_send
