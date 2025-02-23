import asyncio
from aiogram.exceptions import TelegramNetworkError

from handlers import start
from bot import bot, dp
# from handlers.notifications import notify_expiring_keys
# from middlewares.registration_users import RegistrationMiddleware
# from middlewares.database import DatabaseMiddleware
# from middlewares.delete import DeleteMessageMiddleware
# from middlewares.logging import LoggingMiddleware
from logger import logger



async def main():
    """
    Основная функция приложения.
    Настраивает маршрутизатор, запускает бота в режиме поллинга или вебхука
    в зависимости от конфигурации.
    """

    dp.include_router(start.router)  # Подключение маршрутизатора

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