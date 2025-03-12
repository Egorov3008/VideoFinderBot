import asyncio
import os
import re
import yt_dlp
from config import PROXY
from logger import logger
from config import BASE_DIR
from utils_bot.cookies import get_params_for_session


VIDEOS_DIR = os.path.join(BASE_DIR, 'Videos')


async def fetch_formats(url, proxy):
    # Получаем список форматов
    process = await asyncio.create_subprocess_exec(
        'yt-dlp',
        '--proxy', proxy,
        '--list-formats',
        url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # Читаем вывод
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        logger.error(f"Ошибка при выполнении команды: {stderr.decode().strip()}")
        return None

    # Получаем вывод
    output = stdout.decode()

    # Регулярное выражение для поиска форматов с ID, состоящими только из цифр
    pattern = r'^\s*(\d+)\s+mp4\s+\d+x\d+\s+\|\s+.*\s+https\s+.*$'

    # Находим все подходящие форматы
    matches = re.findall(pattern, output, re.MULTILINE)
    logger.info(f"Полученные форматы: {matches}")

    return matches[0]


async def video(url):
    try:
        proxy = PROXY
        logger.info(f"Передаю прокси для скачивания: {proxy}")
        output_template = os.path.expanduser('~/Videos/%(title)s.%(ext)s')
        if not os.path.exists(output_template):
            # Если папка не существует, создаем её
            os.makedirs(output_template)

        logger.info(f"Скачиваю видео {url}")

        command = [
            'yt-dlp',
            '--proxy', proxy,
            '--cookies', 'cookies.txt',
            '-o', output_template,
            '-f',
            'bestvideo[vcodec^=avc1][width<=720][height<=1280]+bestaudio/bestvideo[vcodec^=avc1][width<=1280][height<=720]+bestaudio' if 'youtu' in url else 'best',
            '--merge-output-format', 'mp4',
            '--print', 'after_move:filepath',
            url
        ]

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            logger.error(f"Ошибка при скачивании видео: {stderr.decode()}")
            return None

        file_path = stdout.decode().strip()
        if not file_path:
            logger.error("Путь к файлу не был получен.")
            return None

        logger.info(f"Путь к файлу: {file_path}")
        return file_path

    except Exception as e:
        logger.error(f"Произошла ошибка в функции video: {e}")
    return None




# async def video(url):
#     try:
#         proxy = PROXY
#         logger.info(f"Передаю прокси для скачивания: {proxy}")
#         # Указываем путь к выходному файлу
#         output_template = os.path.join(VIDEOS_DIR, '%(title)s.%(ext)s')
#
#         # Если папка не существует, создаем её
#         os.makedirs(VIDEOS_DIR, exist_ok=True)
#         # Если папка не существует, создаем её
#         os.makedirs(os.path.dirname(output_template), exist_ok=True)
#
#         logger.info(f"Скачиваю видео {url}")
#
#         params = await get_params_for_session(url)
#
#         downloaded_file_path = None  # Инициализируем переменную для хранения пути к скачанному файлу
#
#         ydl_opts = {
#             'proxy': proxy,
#             'cookiefile': params['cookies_file'],
#             'socket_timeout': 30,
#             'outtmpl': output_template,
#             'merge_output_format': 'mp4',
#             'format': 'bestvideo[vcodec^=avc1][width<=720][height<=1280]+bestaudio/bestvideo[vcodec^=avc1][width<=1280][height<=720]+bestaudio' if 'youtube' in url else 'best',
#             'user_agent': params['user_agent'],
#         }
#
#         # Используем yt-dlp для загрузки видео
#         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#             # Сначала извлекаем информацию о видео
#             info_dict = ydl.extract_info(url, download=True)
#             # Получаем путь к загруженному файлу
#             downloaded_file_path = ydl.prepare_filename(info_dict)
#
#         logger.info(downloaded_file_path)
#         if downloaded_file_path and os.path.exists(downloaded_file_path):
#             logger.info(f"Видео успешно скачано: {downloaded_file_path}")
#             return downloaded_file_path
#         else:
#             logger.error("Не удалось получить путь к скачанному файлу.")
#             return None
#
#     except Exception as e:
#         logger.error(f"Произошла ошибка в функции video: {e}")
#         return None
