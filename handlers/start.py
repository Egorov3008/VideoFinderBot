import os
import re

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, FSInputFile, CallbackQuery, )

from bot import bot
from config import kb_list
from db import get_user_by_id, add_user, update_bot_open_status
from kb import main_contact_kb, channels_kb
from logger import logger
from utils_bot.utils import is_user_subscribed
from utils_bot.utils_for_msg import is_valid_url, compress_video, split_video
from utils_bot.youtube import get_videos

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    telegram_id = message.from_user.id
    user_data = await get_user_by_id(telegram_id)

    if user_data is None:
        # Если пользователь не найден, добавляем его в базу данных
        await add_user(
            telegram_id=telegram_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name
        )
        bot_open = False
    else:
        # Получаем статус bot_open для пользователя
        bot_open = user_data.get('bot_open', False)  # Второй параметр по умолчанию False

    if not bot_open:
        # Иначе показываем клавиатуру с каналами для подписки
        await message.answer(
            "Для пользования ботом необходимо подписаться на следующие каналы:",
            reply_markup=channels_kb(kb_list)
        )
    else:
        await start_msg(message)



URL_REGEX = r'^(https?://[^\s]+)$'

@router.message(lambda message: re.match(URL_REGEX, message.text))
async def handle_message(message: Message):
    text = message.text
    path_vidio = None
    if is_valid_url(text):
        try:
            await message.answer("Скачиваю видео...")
            path_vidio = await get_videos(text)
            # Скачиваем видео
            if os.path.exists(path_vidio):
                file_size = os.path.getsize(path_vidio)
                logger.info(f"Размер файла {file_size}")
                if file_size >= 50 * 1024 * 1024:
                    logger.info("Файл больше 50 мб")
                    await message.answer("Ваше видео слишком большое, я разделил его на несколько частей 🙌")
                    # output_path = path_vidio[:-2] + '_output_path.mp4'
                    # if compress_video(path_vidio, output_path):
                    list_video: list[str] = split_video(path_vidio, 50)
                    # os.remove(output_path)
                    for index in range(len(list_video)):
                            video_file = FSInputFile(list_video[index])
                            await message.answer_video(video=video_file, caption=f"часть {index + 1} 🤗")
                            os.remove(list_video[index])

                else:
                    logger.info("Файл меньше либо равен 50 мб")
                    video_file = FSInputFile(path_vidio)
                    await message.answer_video(video=video_file, caption=f"Ваше видео 🤗")
            else:
                await message.answer("Не удалось скачать видео. Попробуйте ещё раз.")
        except Exception as e:
            await message.answer("Не удалось скачать видео. Попробуйте ещё раз.")
            logger.error(f"Произошла ошибка: {e}")
        finally:
            if os.path.exists(path_vidio):
                os.remove(path_vidio)

    else:
        await message.answer("Это не валидный URL. Пожалуйста, отправьте корректный URL.")

@router.callback_query(F.data == 'check_subscription')
async def check_subs_func(call: CallbackQuery):
    await call.answer('Запускаю проверку подписок на каналы')

    for channel in kb_list:
        label = channel.get('label')
        channel_url = channel.get('url')
        telegram_id = call.from_user.id
        check = await is_user_subscribed(channel_url, telegram_id)
        if check is False:
            await call.message.answer(f"❌ вы не подписались на канал 👉 {label}",
                                      reply_markup=channels_kb(kb_list))
            return False

    await update_bot_open_status(telegram_id=call.from_user.id, bot_open=True)
    await call.message.answer("Спасибо за подписки на все каналы! Теперь можете воспользоваться функционалом бота",
                              reply_markup=await main_contact_kb(call.from_user.id))


async def start_msg(message: Message):
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
    logger.info(f"Определяю права пользования пользователя: {message.from_user.id}")
    await main_contact_kb(message.from_user.id)

