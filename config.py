import ast
import os
from dotenv import load_dotenv, find_dotenv
from logger import logger

if not find_dotenv():
    logger.info("Переменные окружения не загружены т.к отсутствует файл .env")
else:
    load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN = os.getenv("ADMIN_ID")
ADMIN_ID = ast.literal_eval(ADMIN)
kb_list = [{'label': 'Тестовый канал', 'url': 'https://t.me/test_grup_01111'}]
