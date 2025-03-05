import os
import re

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, FSInputFile, InlineKeyboardButton, CallbackQuery, )
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import SUPPORT_CHAT_URL, ADMIN_ID
from db import get_subscription, get_all_users, add_user
from logger import logger
from text_msg import start_message
from utils_bot.utils import is_user_subscribed
from utils_bot.youtube import video

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    builder = InlineKeyboardBuilder()
    is_admin = message.from_user.id in ADMIN_ID
    users = await get_all_users()
    if message.from_user.id in [user_id["telegram_id"] for user_id in users]:
        await add_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name
        )
    if is_admin:
        builder.row(InlineKeyboardButton(text="Админ панель🚨", callback_data="admin_panel"))
    builder.row(InlineKeyboardButton(text="Админ", url=SUPPORT_CHAT_URL))
    await start_msg(message, builder)


URL_REGEX = r'^(https?://[^\s]+)$'


@router.message(lambda message: re.match(URL_REGEX, message.text))
async def handle_message(message: Message):
    tg_id = message.from_user.id
    if await check_substraction(tg_id, message):
        text = message.text
        await message.answer("Ищу и скачиваю видео... 🔍")
        # Инициализируем переменную
        path_vidio = None
        try:
            path_vidio = await video(text)
            # Проверяем, был ли установлен путь к видео
            if path_vidio is not None and os.path.exists(path_vidio):
                file_size = os.path.getsize(path_vidio)
                logger.info(f"Видео весит: {file_size}")
                if file_size <= 50 * 1024 * 1024:
                    # await bot.delete_messages(chat_id=msg_del.chat.id, message_ids=msg_del.message_id)
                    video_file = FSInputFile(path_vidio)

                    await message.answer_document(document=video_file, caption="Ваше видео 🤗")
                else:
                    await message.answer("Такое большое видео я еще не умею скачивать 🤕")
            else:
                await message.answer("Не удалось скачать видео. Попробуйте ещё раз.")

        except Exception as e:
            await message.answer("Не удалось скачать видео. Попробуйте ещё раз.")
            logger.error(f"Произошла ошибка: {e}")
        finally:
            if os.path.exists(path_vidio):
                os.remove(path_vidio)


@router.callback_query(F.data == 'check_subscription')
async def check_subs_func(call: CallbackQuery):
    tg_id = call.from_user.id
    if await check_substraction(tg_id, call):
        await call.answer('Спасибо за подписку 🙏\n'
                          '📥 Отправь ссылку на видео из\n'
                          'Instagram, TikTok, YouTube, VK или Pinterest\n '
                          'И бот скачает видео без водяного знака.')


async def start_msg(message: Message, kb: InlineKeyboardBuilder):
    text = start_message
    path_gif = "./img/aspose_video_133855528872978473_out.mp4"
    logger.info(f"Путь к гифке: {os.path.exists(path_gif)}")
    if os.path.exists(path_gif):
        gif = FSInputFile(path_gif)
        await message.answer_animation(animation=gif, caption=text, reply_markup=kb.as_markup())
        return
    await message.answer(text, reply_markup=kb.as_markup())


async def check_substraction(tg_id, message: Message | CallbackQuery):
    logger.debug(f"Проверяю подписку пользователя: {tg_id} на каналы")
    dict_sub = await get_subscription()
    logger.info(f"Получены подписки: {dict_sub}")

    if dict_sub:
        dict_sub_users = {
            (channel, url_sub): await is_user_subscribed(channel_url=url_sub, telegram_id=tg_id) for channel, url_sub
            in dict_sub.items()
        }
        logger.debug(f"Статусы подписок пользователей: {dict_sub_users}")

        if not any(v for v in dict_sub_users.values() if v):
            logger.warning(f"Пользователь {tg_id} не подписан на один или несколько каналов.")
            builder = InlineKeyboardBuilder()
            for channel, subscribed in dict_sub_users.items():

                if not subscribed:
                    builder.row(InlineKeyboardButton(text=channel[0], url=channel[1]))
            builder.row(InlineKeyboardButton(text="Проверить подписку 📍", callback_data='check_subscription'))
            if isinstance(message, Message):
                await message.answer(f"😊 Чтобы использовать бота, подпишитесь на каналы,\n перечисленные ниже"
                                     f"и нажмите кнопку 'Проверить подписку 📍',\n как только вы подпишетесь.",
                                     reply_markup=builder.as_markup())
                logger.info(f"Отправлено сообщение о подписке на канал пользователю {tg_id}")
            if isinstance(message, CallbackQuery):
                await message.message.answer(f"Вы не подписаны на каналы",
                                             reply_markup=builder.as_markup())
                logger.info(f"Отправлено сообщение о подписке на канал пользователю {tg_id} через callback_query")
            return False
        elif any(v for v in dict_sub_users.values() if v) or tg_id in ADMIN_ID:
            logger.info(f"Пользователь {tg_id} подписан на все каналы или является администратором.")
            return True
    else:
        logger.info("Обязательных подписок нет")
        return True
