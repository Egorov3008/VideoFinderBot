import ast
import os
from dotenv import load_dotenv, find_dotenv
from logger import logger

if not find_dotenv():
    logger.info("Переменные окружения не загружены т.к отсутствует файл .env")
else:
    load_dotenv()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN = os.getenv("ADMIN_ID")
ADMIN_ID = ast.literal_eval(ADMIN)

PROXY = os.getenv("PROXY")
SUPPORT_CHAT_URL = os.getenv("SUPPORT_CHAT_URL")
