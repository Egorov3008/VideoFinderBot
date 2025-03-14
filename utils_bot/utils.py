import asyncio

from aiogram import Bot
from aiogram.enums import ContentType, ChatMemberStatus
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InputMediaDocument, InputMediaVideo, InputMediaPhoto, InputMediaAudio
from bot import bot
from config import ADMIN_ID
from db import get_users_sub, add_count_users_sub, check_user_set_active
from logger import logger


async def check_bot_status(channel_username) -> bool | str:
    try:
        # Получаем ID бота
        bot_id = (await bot.get_me()).id
        logger.info(f"ID бота: {bot_id}")
        if channel_username.startswith('+'):

            logger.debug(f"Получаю ссылку канала: {channel_username}")
            chat_id: int = await get_chat_id(bot, channel_username)

        else:
            chat_id: str = f"@{channel_username}"
        member = await bot.get_chat_member(chat_id=chat_id, user_id=bot_id)

        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
            logger.info(f"Бот является администратором канала {channel_username}.")
            return True
        else:
            logger.info(f"Бот не является участником канала {channel_username}.")
            # await bot.send_message(chat_id=ADMIN_ID[0], text=f'Бот не является админом группы: {channel_username}')
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
            list_users: list[int] = await get_users_sub(channel_url)
            logger.debug(f"Cписок пользователей для {channel_url} : {list_users}")
            is_sub_chekc = await check_user_set_active(user_active=len(list_users), url_subscription=channel_url)

            if not is_sub_chekc:

                logger.debug(f"Проверка подписки пользователя {telegram_id} на канал: {channel_username}")
                # Получаем информацию о пользователе в канале
                member = await bot.get_chat_member(chat_id=f"@{channel_username}", user_id=telegram_id)
                logger.info(
                    f"Статус подписки пользователя {telegram_id} для канала {channel_username}: {member.status}")

                # Проверяем статус пользователя
                if member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR]:

                    if telegram_id not in list_users:
                        await add_count_users_sub(channel_url, telegram_id)
                    return True

                else:
                    return False
            return True
        except Exception as e:
            # Если возникла ошибка (например, пользователь не найден или бот не имеет доступа к каналу)
            logger.error(
                f"Ошибка при проверке подписки для пользователя {telegram_id} на канал {channel_username}: {e}")
            return False




async def msg_post(message: Message, state: FSMContext, chat_id):
    media_list = []
    data = await state.get_data()
    media_group_id = data.get("media_group", [])
    for media in media_group_id:
        if media.photo:
            media_list.append(InputMediaPhoto(media=media.photo[-1].file_id))
        elif media.video:
            media_list.append(InputMediaVideo(media=media.video.file_id))
        elif media.document:
            media_list.append(InputMediaDocument(media=media.document.file_id))
        elif media.audio:
            media_list.append(InputMediaAudio(media=media.audio.file_id))

    await bot.send_media_group(chat_id=chat_id, media=media_list)
    await asyncio.sleep(1)
    await message.copy_to(chat_id=chat_id)


async def get_chat_id(bot: Bot, invite_link: str):
    try:
        # Если ссылка начинается с https://t.me/+, извлекаем уникальный идентификатор
        if invite_link.startswith("+"):
            invite_hash = invite_link.lstrip("+")
            logger.debug(f'invite_hash: {invite_hash}')
            chat = await bot.get_chat(chat_id=invite_hash)
        else:
            # Если это username, используем его напрямую
            chat = await bot.get_chat(chat_id=invite_link)

        # Возвращаем chat_id
        return chat.id
    except Exception as e:
        logger.error(f"Ошибка при получении chat_id: {e}")
        return None