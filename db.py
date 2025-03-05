import logging
from typing import List, Dict

import aiosqlite

logger = logging.getLogger('aiosqlite')
logger.setLevel(logging.INFO)


async def initialize_database():
    """Инициализирует базу данных и создает необходимые таблицы, если они не существуют."""
    logger.info("Инициализация базы данных...")
    async with aiosqlite.connect("bot.db") as db:
        # Создаем таблицу users, если она не существует
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                subscription_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Создаем таблицу subscription, если она не существует
        await db.execute("""
            CREATE TABLE IF NOT EXISTS subscription (
                name_subscription TEXT,
                url_subscription TEXT
            );
        """)

        # Сохраняем изменения
        await db.commit()
    logger.info("База данных инициализирована.")


async def add_user(telegram_id: int, username: str, first_name: str):
    """Добавляет пользователя в таблицу users."""
    logger.info(f"Добавление пользователя: {telegram_id}, {username}, {first_name}")
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("""
            INSERT INTO users (telegram_id, username, first_name)
            VALUES (?, ?, ?)
            ON CONFLICT(telegram_id) DO NOTHING
        """, (telegram_id, username, first_name))
        await db.commit()
    logger.info("Пользователь добавлен.")


async def get_all_users() -> List[Dict]:
    """Получает всех пользователей из таблицы users."""
    logger.info("Получение всех пользователей...")
    async with aiosqlite.connect("bot.db") as db:
        cursor = await db.execute("SELECT * FROM users")
        rows = await cursor.fetchall()

        users = [
            {
                "telegram_id": row[0],
                "username": row[1],
                "first_name": row[2],
                "bot_open": bool(row[3]),
            }
            for row in rows
        ]
    logger.info(f"Найдено пользователей: {len(users)}")
    return users


async def update_bot_open_status(telegram_id: int, bot_open: bool):
    """Обновляет статус bot_open для пользователя по его telegram_id."""
    logger.info(f"Обновление статуса bot_open для пользователя {telegram_id} на {bot_open}")
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("""
            UPDATE users
            SET bot_open = ?
            WHERE telegram_id = ?
        """, (bot_open, telegram_id))
        await db.commit()
    logger.info("Статус обновлен.")


async def get_user_by_id(telegram_id: int):
    """Получает данные о пользователе по его telegram_id."""
    logger.info(f"Получение данных о пользователе {telegram_id}...")
    async with aiosqlite.connect("bot.db") as db:
        cursor = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cursor.fetchone()

        if row is None:
            logger.warning(f"Пользователь {telegram_id} не найден.")
            return None

        user = {
            "telegram_id": row[0],
            "username": row[1],
            "first_name": row[2],
            "bot_open": bool(row[3])
        }
    logger.info(f"Данные о пользователе {telegram_id} получены.")
    return user


async def get_subscription():
    """Получает данные о подписке из таблицы subscription."""
    logger.info("Получение данных о подписке...")
    async with aiosqlite.connect("bot.db") as db:
        cursor = await db.execute("SELECT * FROM subscription;")
        row = await cursor.fetchone()

        if row is None:
            logger.warning("Подписка не найдена.")
            return None

        subscription = {
            row[0]: row[1],
        }
    logger.info("Данные о подписке получены.")
    return subscription


async def delete_subscription(url_subscription: str):
    """Удаляет подписку из таблицы subscription по названию подписки."""
    logger.info(f"Удаление подписки: {url_subscription}")
    try:
        async with aiosqlite.connect("bot.db") as db:
            cursor = await db.execute("""
                DELETE FROM subscription
                WHERE url_subscription = ?
            """, (url_subscription,))
            await db.commit()
            logger.info(f"Удалено строк: {cursor.rowcount}")
    except Exception as e:
        logger.error(f"Ошибка при удалении подписки: {e}")
    logger.info("Подписка удалена.")


async def add_sub_url(name: str, url_sub: str):
    """Добавляет новую подписку в таблицу subscription."""
    logger.info(f"Добавление подписки: {name}, {url_sub}")
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("""
            INSERT INTO subscription (name_subscription, url_subscription)
            VALUES (?, ?)
        """, (name, url_sub))
        await db.commit()
    logger.info("Подписка добавлена.")


async def get_user_counts():
    async with aiosqlite.connect("bot.db") as db:
        async with db.execute("""
            SELECT 
                (SELECT COUNT(*) 
                 FROM users 
                 WHERE subscription_time >= datetime('now', '-7 days')) AS users_added_last_week,
                (SELECT COUNT(*) 
                 FROM users 
                 WHERE subscription_time >= datetime('now', '-1 month')) AS users_added_last_month;
        """) as cursor:
            result = await cursor.fetchone()
            return {
                "users_added_last_week": result[0],
                "users_added_last_month": result[1]
            }
