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

    Параметры:
    - tg_id (int): Идентификатор пользователя в Telegram.
    - message (Message | CallbackQuery): Сообщение или обратный вызов, который инициировал проверку подписки.

    Возвращает:
    - bool: True, если пользователь подписан на все необходимые каналы или является администратором,
            False, если пользователь не подписан на один или несколько каналов.

    Логика работы:
    1. Если пользователь является администратором (tg_id находится в ADMIN_ID), функция сразу возвращает True.
    2. Логирует проверку подписки пользователя.
    3. Получает список обязательных подписок с помощью функции get_subscription().
    4. Если есть обязательные подписки:
        - Проверяет, подписан ли пользователь на каждый из каналов.
        - Если пользователь не подписан на один или несколько каналов:
            - Формирует клавиатуру с кнопками для подписки на недостающие каналы.
            - Отправляет сообщение пользователю с просьбой подписаться.
            - Логирует информацию о том, что сообщение было отправлено.
        - Если пользователь подписан на все каналы:
            - Логирует информацию о том, что пользователь подписан на все каналы или является администратором.
            - Возвращает True.
    5. Если нет обязательных подписок, логирует это и возвращает True.
    """

    if tg_id in ADMIN_ID:
        return True

    logger.debug(f"Проверяю подписку пользователя: {tg_id} на каналы")
    list_sub: Optional[List[Dict]] = await get_subscription()
    logger.info(f"Получены подписки: {list_sub}")

    if list_sub:
        dict_sub_users = {
            (channel, url_sub): await is_user_subscribed(channel_url=url_sub, telegram_id=tg_id)
            for dict_sub in list_sub  # Перебираем каждый словарь в списке
            for channel, url_sub in dict_sub.items()  # Перебираем пары channel: url_sub в каждом словаре
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
                await message.answer(f"Чтобы получить доступ к функциям бота,\n<b>нужно подписаться на ресурсы:</b>",
                                     reply_markup=builder.as_markup())
                logger.info(f"Отправлено сообщение о подписке на канал пользователю {tg_id}")
            if isinstance(message, CallbackQuery):
                await message.message.answer(f"Вы не подписаны на каналы",
                                             reply_markup=builder.as_markup())
                logger.info(f"Отправлено сообщение о подписке на канал пользователю {tg_id} через callback_query")
            return False
        elif any(v for v in dict_sub_users.values() if v):
            logger.info(f"Пользователь {tg_id} подписан на все каналы или является администратором.")
            return True
    else:
        logger.info("Обязательных подписок нет")
        return True
