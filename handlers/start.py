import os
import traceback
from typing import Any, Union

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    Message, InputFile, FSInputFile,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from logger import logger
from utils.utils_for_msg import is_valid_url
from utils.youtube import get_videos

router = Router()


@router.message(CommandStart())
async def start_command(message: Message):
    await message.answer("<b>🎉 Добро пожаловать в VideoFinderBot! 🎥</b>\n\n"
                         "Я — ваш помощник в мире видео! С моей помощью вы можете:\n"
                         "✅ Скачивать видео с YouTube, Instagram, TikTok и других платформ по ссылке.\n"
                         "✅ Выбирать качество и формат для скачивания.\n"
                         "🎬 Как начать?\n"
                         "Просто отправьте мне ссылку на видео, и я скачаю его для вас.\n\n"
                         "🚀 Я поддерживаю:\n"
                         "YouTube\n"
                         "Instagram (реels)\n"
                         "TikTok\n\n"
                         "Если у вас есть вопросы или что-то не работает, просто напишите /help, и я помогу!\n"
                         "Давайте начнём! Отправьте мне ссылку, и я сделаю всё остальное. 😊")

@router.message()
async def handle_message(message: Message):
    text = message.text
    if is_valid_url(text):
        try:
            path_vidio = await get_videos(text)  # Скачиваем видео
            if os.path.exists(path_vidio):  # Проверяем, существует ли файл
                video_file = FSInputFile(path_vidio)  # Используем FSInputFile
                await message.answer_video(video=video_file, caption="Ваше видео 🤗")
                os.remove(path_vidio)  # Удаляем файл после отправки
            else:
                await message.answer("Не удалось скачать видео. Попробуйте ещё раз.")
        except Exception as e:
            await message.answer("Не удалось скачать видео. Попробуйте ещё раз.")
            logger.error(f"Произошла ошибка: {e}")

    else:
        await message.answer("Это не валидный URL. Пожалуйста, отправьте корректный URL.")