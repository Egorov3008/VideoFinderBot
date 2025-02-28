import aiosqlite


async def initialize_database():
    """Инициализирует базу данных и создает необходимые таблицы, если они не существуют."""
    async with aiosqlite.connect("bot.db") as db:
        # Создаем таблицу users, если она не существует
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            bot_open BOOLEAN DEFAULT FALSE,
            subscription_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS subscription (
            name_subscription TEXT,
            url_subscription TEXT
            )
        """)
        # Сохраняем изменения
        await db.commit()


async def add_user(telegram_id: int, username: str, first_name: str):
    """Добавляет пользователя в таблицу users. Если пользователь с таким telegram_id уже существует, ничего не происходит.

    Args:
        telegram_id (int): Уникальный идентификатор пользователя в Telegram.
        username (str): Имя пользователя в Telegram.
        first_name (str): Имя пользователя.
    """
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("""
            INSERT INTO users (telegram_id, username, first_name)
            VALUES (?, ?, ?)
            ON CONFLICT(telegram_id) DO NOTHING
        """, (telegram_id, username, first_name))
        await db.commit()


async def get_all_users():
    """Получает всех пользователей из таблицы users в виде списка словарей.

    Returns:
        List[Dict]: Список пользователей, где каждый пользователь представлен в виде словаря.
    """
    async with aiosqlite.connect("bot.db") as db:
        cursor = await db.execute("SELECT * FROM users")
        rows = await cursor.fetchall()

        # Преобразуем результаты в список словарей
        users = [
            {
                "telegram_id": row[0],
                "username": row[1],
                "first_name": row[2],
                "bot_open": bool(row[3]),
            }
            for row in rows
        ]
        return users


async def update_bot_open_status(telegram_id: int, bot_open: bool):
    """Обновляет статус bot_open для пользователя по его telegram_id.

    Args:
        telegram_id (int): Уникальный идентификатор пользователя в Telegram.
        bot_open (bool): Новый статус bot_open.
    """
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("""
            UPDATE users
            SET bot_open = ?
            WHERE telegram_id = ?
        """, (bot_open, telegram_id))
        await db.commit()


async def get_user_by_id(telegram_id: int):
    """Получает данные о пользователе по его telegram_id.

    Args:
        telegram_id (int): Уникальный идентификатор пользователя в Telegram.

    Returns:
        Dict или None: Данные пользователя в виде словаря или None, если пользователь не найден.
    """
    async with aiosqlite.connect("bot.db") as db:
        cursor = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cursor.fetchone()

        if row is None:
            return None

        # Преобразуем результат в словарь
        user = {
            "telegram_id": row[0],
            "username": row[1],
            "first_name": row[2],
            "bot_open": bool(row[3])
        }
        return user


async def get_subscription():
    """Получает данные о подписке из таблицы subscription.

    Returns:
        Dict или None: Данные подписки в виде словаря или None, если подписка не найдена.
    """
    async with aiosqlite.connect("bot.db") as db:
        cursor = await db.execute("SELECT * FROM subscription;")
        row = await cursor.fetchone()

        if row is None:
            return None

        # Преобразуем результат в словарь
        subscription = {
            "name_subscription": row[0],
            "url_subscription": row[1],
        }
        return subscription


async def delete_subscription(name_subscription: str):
    """Удаляет подписку из таблицы subscription по названию подписки.

    Args:
        name_subscription (str): Название подписки, которую нужно удалить.
    """
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("""
            DELETE FROM subscription
            WHERE name_subscription = ?
        """, (name_subscription,))
        await db.commit()