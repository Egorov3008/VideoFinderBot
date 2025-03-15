import os
from typing import Optional, List, Dict

import validators
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message, FSInputFile, InlineKeyboardButton, CallbackQuery, )
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import SUPPORT_CHAT_URL, ADMIN_ID
from db import get_subscription, get_all_users, add_user
from logger import logger
from text_msg import start_message
from utils_bot.utils import is_user_subscribed
from utils_bot.download import video

router = Router()


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    is_admin = message.from_user.id in ADMIN_ID
    users = await get_all_users()
    if message.from_user.id not in [user_id["telegram_id"] for user_id in users]:
        await add_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name
        )
    if is_admin:
        builder.row(InlineKeyboardButton(text="Админ панель🚨", callback_data="admin_panel"))
    # builder.row(InlineKeyboardButton(text="Админ", url=SUPPORT_CHAT_URL))
    await start_msg(message, builder)


@router.message(lambda message: validators.url(message.text))
async def handle_message(message: Message):
    tg_id = message.from_user.id
    check_file_size = 200 * 1024 * 1024 if message.from_user.is_premium else 50 * 1024 * 1024
    if await check_substraction(tg_id, message):
        text = message.text
        await message.answer("Ищу и скачиваю видео... 🔍")
        # Инициализируем переменную
        path_vidio = None
        try:
            path_vidio = await video(text)
            # Проверяем, был ли установлен путь к видео
            if path_vidio and os.path.exists(path_vidio):
                file_size = os.path.getsize(path_vidio)
                logger.info(f"Видео весит: {file_size}")
                if file_size <= check_file_size:
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
        await call.message.answer('Спасибо за подписку 🙏\n'
                                  '📥 Теперь ты можешь отправь ссылку на видео из\n'
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
    """
    Проверяет, подписан ли пользователь на необходимые каналы.
    """
    if tg_id in ADMIN_ID:
        return True

    logger.debug(f"Проверяю подписку пользователя: {tg_id} на каналы")

    try:
        list_sub: Optional[List[Dict]] = await get_subscription()
        logger.info(f"Получены подписки: {list_sub}")

        if list_sub:
            dict_sub_users = {
                (channel, url_sub): await is_user_subscribed(channel_url=url_sub, telegram_id=tg_id)
                for dict_sub in list_sub
                for channel, url_sub in dict_sub.items()
            }
            logger.debug(f"Статусы подписок пользователя: {dict_sub_users}")

            # Проверяем, подписан ли пользователь на все каналы
            if not all(dict_sub_users.values()):  # Если хотя бы одна подписка ложная
                logger.warning(f"Пользователь {tg_id} не подписан на один или несколько каналов.")
                builder = InlineKeyboardBuilder()
                for (channel, url_sub), subscribed in dict_sub_users.items():
                    if not subscribed:
                        builder.row(InlineKeyboardButton(text=channel, url=url_sub))
                builder.row(InlineKeyboardButton(text="Проверить подписку 📍", callback_data='check_subscription'))

                response_text = "Чтобы получить доступ к функциям бота,\n<b>нужно подписаться на ресурсы:</b>"
                if isinstance(message, Message):
                    await message.answer(response_text, reply_markup=builder.as_markup())
                elif isinstance(message, CallbackQuery):
                    await message.message.answer("Вы не подписаны на каналы", reply_markup=builder.as_markup())

                logger.info(f"Отправлено сообщение о подписке на канал пользователю {tg_id}")
                return False

            logger.info(f"Пользователь {tg_id} подписан на все каналы.")
            return True

        logger.info("Нет обязательных подписок.")
        return True

    except Exception as e:
        logger.error(f"Ошибка при проверке подписки: {e}")
        return False