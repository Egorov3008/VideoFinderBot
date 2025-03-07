import asyncio
from aiogram.exceptions import TelegramNetworkError
from bot import bot, dp
from bot import set_commands
from db import initialize_database
from handlers import start, admin_panel
from logger import logger
from middlewares.delet_msg import DeleteMessageMiddleware
from middlewares.subscribe_channel import SubscribeChannel


# def run_flask():
#     """Запускает Flask-приложение в фоновом режиме."""
#     app.run(host='0.0.0.0', port=5000)

async def main():
    """
    Основная функция приложения.
    Настраивает маршрутизатор, запускает бота в режиме поллинга или вебхука
    в зависимости от конфигурации.
    """
    await initialize_database()
    await set_commands()

    # dp.message.middleware(SubscribeChannel())
    # dp.callback_query.middleware(SubscribeChannel())
    dp.message.middleware(DeleteMessageMiddleware())
    dp.callback_query.middleware(DeleteMessageMiddleware())
    dp.include_router(admin_panel.router)
    dp.include_router(start.router)

    try:
        logger.info("Бот запущен")
        await dp.start_polling(bot)  # Запуск поллинга
    except TelegramNetworkError as e:
        logger.error(f"Network error: {e}")
        await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        # Запуск Flask-сервера в отдельном потоке
        # flask_thread = threading.Thread(target=run_flask, daemon=True)
        # flask_thread.start()

        # Запуск основной функции бота
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Ошибка при запуске приложения:\n{e}")  # Логирование ошибок при запуске приложения
