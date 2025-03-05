import traceback

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram.types import ErrorEvent

from config import API_TOKEN
from logger import logger

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)


@dp.error()
async def error_handler(event: ErrorEvent):
    logger.error(
        "Ошибка в боте:\n"
        f"Исключение: {event.exception}\n"
        f"Тип: {type(event.exception)}\n"
        f"Update: {event.update}\n"
        f"Трассировка:\n{traceback.format_exc()}"
    )


async def set_commands():
    # Создаем список команд, которые будут доступны пользователям

    commands = [BotCommand(command='start', description='Старт')]
    # Устанавливаем эти команды как дефолтные для всех пользователей
    await bot.set_my_commands(commands, BotCommandScopeDefault())
