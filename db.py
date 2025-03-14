import logging
from typing import List, Dict, Optional, Any

import aiosqlite

logger = logging.getLogger('aiosqlite')
logger.setLevel(logging.INFO)


async def initialize_database():
    """
    Инициализирует базу данных и создает необходимые таблицы, если они не существуют.
    Создает таблицы: users, subscription, count_users_sub.
    """
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
                name_subscription TEXT NOT NULL,
                url_subscription TEXT UNIQUE NOT NULL,
                active BOOLEAN DEFAULT FALSE, 
                users_set INTEGER,
                users_actual INTEGER DEFAULT 0
            );
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS count_users_sub (
            url_subscription TEXT,
            telegram_id INTEGER,
            UNIQUE (url_subscription, telegram_id)
        );
        """)

        # Сохраняем изменения
        await db.commit()
    logger.info("База данных инициализирована.")


async def add_user(telegram_id: int, username: str, first_name: str):
    """
    Добавляет пользователя в таблицу users.

    :param telegram_id: Уникальный идентификатор пользователя в Telegram.
    :param username: Имя пользователя в Telegram.
    :param first_name: Имя пользователя.
    """
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
    """
    Получает всех пользователей из таблицы users.

    :return: Список словарей с данными о пользователях.
    """
    logger.info("Получение всех пользователей...")
    async with aiosqlite.connect("bot.db") as db:
        cursor = await db.execute("SELECT * FROM users")
        rows = await cursor.fetchall()

        users = [
            {
                "telegram_id": row[0],
                "username": row[1],
                "first_name": row[2],
                "subscription_time": (row[3]),
            }
            for row in rows
        ]
    logger.info(f"Найдено пользователей: {len(users)}")
    return users


async def update_bot_open_status(telegram_id: int, bot_open: bool):
    """
    Обновляет статус bot_open для пользователя по его telegram_id.

    :param telegram_id: Уникальный идентификатор пользователя в Telegram.
    :param bot_open: Новое значение статуса bot_open.
    """
    logger.info(f"Обновление статуса bot_open для пользователя {telegram_id} на {bot_open}")
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("""
            UPDATE users
            SET bot_open = ?
            WHERE telegram_id = ?
        """, (bot_open, telegram_id))
        await db.commit()
    logger.info("Статус обновлен.")


async def get_user_by_id(telegram_id: int) -> Optional[Dict]:
    """
    Получает данные о пользователе по его telegram_id.

    :param telegram_id: Уникальный идентификатор пользователя в Telegram.
    :return: Словарь с данными о пользователе или None, если пользователь не найден.
    """
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


async def get_subscription() -> Optional[List[Dict]]:
    """
    Получает данные о подписке из таблицы subscription.

    :return: Словарь с данными о подписке или None, если подписка не найдена.
    """
    logger.info("Получение данных о подписке...")
    async with aiosqlite.connect("bot.db") as db:
        cursor = await db.execute("SELECT * FROM subscription;")
        row = await cursor.fetchall()

        if row is None:
            logger.warning("Подписка не найдена.")
            return None

        subscription = [{value[0]: value[1]} for value in row]
        logger.debug(f'Обязательные подписки: {subscription}')
    logger.info("Данные о подписке получены.")
    return subscription


async def get_info_subscription(url_subscription: str) -> Optional[Dict]:
    logger.info(f"Получение данных о подписке {url_subscription}")
    async with aiosqlite.connect("bot.db") as db:
        cursor = await db.execute("""SELECT * FROM subscription WHERE url_subscription = ?""", (url_subscription,))
        row = await cursor.fetchone()

        if row is None:
            logger.warning("Подписка не найдена.")
            return None

        subscription = {
            "name_subscription": row[0],
            "url_subscription": row[1],
            "active": bool(row[2]),
            "users_set": row[3],
            "users_actual": row[4]
        }
        logger.debug(f"name_subscription: {row[0]},\n"
                     f"url_subscription: {row[1]},\n"
                     f"active: {bool(row[2])},\n"
                     f"users_set: {row[3]},\n"
                     f"users_actual: {row[4]}")
        logger.info("Данные о подписке получены.")
        return subscription


async def delete_subscription(url_subscription: str):
    """
    Удаляет подписку из таблицы subscription по названию подписки.

    :param url_subscription: URL подписки для удаления.
    """
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


async def add_sub_url(name: str, url_sub: str, users_set: int):
    """
    Добавляет новую подписку в таблицу subscription или обновляет существующую.

    :param name: Название подписки.
    :param url_sub: URL подписки.
    :param users_set: Количество пользователей, необходимое для активации подписки.
    """
    logger.info(f"Добавление или обновление подписки: {name}, {url_sub}")
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("""
            INSERT INTO subscription (name_subscription, url_subscription, users_set)
            VALUES (?, ?, ?)
            ON CONFLICT(url_subscription) DO UPDATE SET
                name_subscription = excluded.name_subscription,
                users_set = excluded.users_set
        """, (name, url_sub, users_set))
        await db.commit()
    logger.info("Подписка добавлена или обновлена.")


async def get_user_counts() -> Dict[str, int]:
    """
    Получает количество пользователей, добавленных за последнюю неделю и месяц.

    :return: Словарь с количеством пользователей за последнюю неделю и месяц.
    """
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


async def add_count_users_sub(url_subscription: str, telegram_id: int):
    """
    Добавляет запись о подписке пользователя на канал.

    :param url_subscription: URL подписки.
    :param telegram_id: Уникальный идентификатор пользователя в Telegram.
    """
    try:
        async with aiosqlite.connect("bot.db") as db:
            # Используем контекстный менеджер для транзакции
            async with db.execute("""
                INSERT INTO count_users_sub (url_subscription, telegram_id)
                VALUES (?, ?)
                ON CONFLICT(url_subscription, telegram_id) DO NOTHING
            """, (url_subscription, telegram_id)) as cursor:
                await db.commit()
                logger.info(f"Добавлена запись: {url_subscription}, {telegram_id}")

            # Увеличиваем счётчик подписчиков
            await plus_users_sub(url_subscription)
    except aiosqlite.Error as e:
        logger.error(f"Ошибка при добавлении записи в базу данных: {e}")
        raise  # Повторно выбрасываем исключение для обработки на уровне выше

async def get_users_sub(url_subscription: str) -> Optional[list[int]]:
    """
    Получает список пользователей по каналу подписки.

    :param url_subscription: URL подписки.
    :return: Идентификатор пользователя или None, если пользователь не найден.
    """
    async with aiosqlite.connect("bot.db") as db:
        async with db.execute(
                """SELECT telegram_id
                FROM count_users_sub
                WHERE url_subscription = ?
                """, (url_subscription,)) as cursor:
            results = await cursor.fetchall()
            return [row[0] for row in results] if results else []


async def plus_users_sub(url_subscription: str) -> Any:
    """
    Увеличивает счетчик пользователей для подписки и возвращает новое значение.

    :param url_subscription: URL подписки.
    :return: Новое значение счетчика пользователей или None, если подписка не найдена.
    """
    logger.info(f"Добавляю +1 к счетчику пользователей для {url_subscription}")
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("""
            UPDATE subscription
            SET users_actual = users_actual + 1
            WHERE url_subscription = ?
        """, (url_subscription,))
        await db.commit()


async def get_user_set(url_subscription: str) -> Optional[int]:
    """
    Получает количество пользователей, необходимое для активации подписки.

    :param url_subscription: URL подписки.
    :return: Количество пользователей или None, если подписка не найдена.
    """
    async with aiosqlite.connect("bot.db") as db:
        async with db.execute("""
            SELECT users_set
            FROM subscription
            WHERE url_subscription = ?
        """, (url_subscription,)) as cursor:
            result = await cursor.fetchone()
            user_set = result[0] if result else None

    return user_set


async def check_user_set_active(user_active: int, url_subscription: str) -> bool:
    """
    Проверяет, активна ли подписка, и обновляет статус, если необходимо.


    :param user_active: Текущее количество пользователей.
    :param url_subscription: URL подписки.
    :return: True, если подписка активна, иначе False.
    """
    user_set = await get_user_set(url_subscription)
    logger.info(f"Для канала {url_subscription} набрано {user_active} из {user_set}")

    if user_set <= user_active:
        async with aiosqlite.connect("bot.db") as db:
            await db.execute("""
                UPDATE subscription
                SET active = TRUE
                WHERE url_subscription = ?
            """, (url_subscription,))
            await db.commit()
        return True
    return False
