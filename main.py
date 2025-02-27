import asyncio
from aiogram.exceptions import TelegramNetworkError

from bot import set_commands
from db import initialize_database
from handlers import start, admin_panel
from bot import bot, dp
from logger import logger



async def main():
    """
    Основная функция приложения.
    Настраивает маршрутизатор, запускает бота в режиме поллинга или вебхука
    в зависимости от конфигурации.
    """
    await initialize_database()
    await set_commands()
    dp.include_router(start.router)
    dp.include_router(admin_panel.router)# Подключение маршрутизатора

    try:
        logger.info("Бот запущен")

        await dp.start_polling(bot)  # Запуск поллинга
    except TelegramNetworkError as e:
        logger.error(f"Network error: {e}")
        await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())  # Запуск основной функции
    except Exception as e:
        logger.error(f"Ошибка при запуске приложения:\n{e}")  # Логирование ошибок при запуске приложения