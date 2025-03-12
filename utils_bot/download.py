import asyncio
import os
import re
import yt_dlp
from fake_useragent import UserAgent

from config import PROXY, BASE_PATH
from logger import logger
from utils_bot.cookies import open_page_with_cookies


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




# async def video(url):
#     try:
#         proxy = PROXY
#         logger.info(f"Передаю прокси для скачивания: {proxy}")
#         output_template = os.path.expanduser('~/Videos/%(title)s.%(ext)s')
#         if not os.path.exists(output_template):
#             # Если папка не существует, создаем её
#             os.makedirs(output_template)
#
#         logger.info(f"Скачиваю видео {url}")
#
#         if any(name in url for name in ('https://youtu.be', 'youtu.be', 'https://www.youtube.com/', 'youtube')):
#             format = 'bestvideo[vcodec^=avc1][width<=720][height<=1280]+bestaudio/bestvideo[vcodec^=avc1][width<=1280][height<=720]+bestaudio'
#             command = [
#                 'yt-dlp',
#                 '--proxy', proxy,
#                 '--cookies', 'cookies.txt',
#                 '-o', output_template,
#                 '-f', format,
#                 '--merge-output-format', 'mp4',
#                 '--print', 'after_move:filepath',
#                 url
#             ]
#
#         elif any(name in url for name in ('instagram', 'https://www.instagram')):
#             format = await fetch_formats(url, proxy)
#
#             command = [
#                 'yt-dlp',
#
#                 '--proxy', proxy,
#                 '--cookies', 'cookies.txt',
#                 '-o', output_template,
#                 '-f', format,
#                 '--merge-output-format', 'mp4',
#                 '--print', 'after_move:filepath',
#                 url
#             ]
#         else:
#             command = [
#                 'yt-dlp',
#                 '--proxy', proxy,
#                 '--cookies', 'cookies.txt',
#                 '-o', output_template,
#                 '--merge-output-format', 'mp4',
#                 '--print', 'after_move:filepath',
#                 url
#             ]
#
#         process = await asyncio.create_subprocess_exec(
#             *command,
#             stdout=asyncio.subprocess.PIPE,
#             stderr=asyncio.subprocess.PIPE
#         )
#
#         stdout, stderr = await process.communicate()
#
#         if process.returncode != 0:
#             logger.error(f"Ошибка при скачивании видео: {stderr.decode()}")
#             return None
#
#         file_path = stdout.decode().strip()
#         if not file_path:
#             logger.error("Путь к файлу не был получен.")
#             return None
#
#         logger.info(f"Путь к файлу: {file_path}")
#         return file_path
#     except Exception as e:
#         logger.error(f"Произошла ошибка в функции video: {e}")
#         return None



VIDEOS_DIR = os.path.join(BASE_PATH, 'Videos')
cookies_file = os.path.join(BASE_PATH, 'cookies/cookies.txt')

async def video(url, cookies=cookies_file, max_retries=3):
    ua = UserAgent()
    user_agent = ua.random
    attempt = 0  # Счетчик попыток

    while attempt < max_retries:
        try:
            proxy = f'http://{PROXY}'
            logger.info(f"Передаю прокси для скачивания: {proxy}")
            output_template = os.path.join(VIDEOS_DIR, '%(title)s.%(ext)s')

            os.makedirs(VIDEOS_DIR, exist_ok=True)
            os.makedirs(os.path.dirname(output_template), exist_ok=True)

            logger.info(f"Скачиваю видео {url}")

            ydl_opts = {
                'proxy': proxy,
                'cookiefile': cookies,
                'socket_timeout': 30,
                'outtmpl': output_template,
                'merge_output_format': 'mp4',
                'format': 'bestvideo[vcodec^=avc1][width<=720][height<=1280]+bestaudio/bestvideo[vcodec^=avc1][width<=1280][height<=720]+bestaudio' if 'youtube' in url else 'best',
                'user_agent': user_agent,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                downloaded_file_path = ydl.prepare_filename(info_dict)

            logger.info(downloaded_file_path)
            if downloaded_file_path and os.path.exists(downloaded_file_path):
                logger.info(f"Видео успешно скачано: {downloaded_file_path}")
                return downloaded_file_path
            else:
                logger.error("Не удалось получить путь к скачанному файлу.")
                return None

        except Exception as e:
            logger.error(f"Произошла ошибка в функции video: {e}")
            attempt += 1  # Увеличиваем счетчик попыток
            logger.info(f"Попытка {attempt} из {max_retries}. Повторная попытка...")
            # Пытаемся обновить куки и повторить загрузку
            cookies = await open_page_with_cookies(url, user_agent, proxy=PROXY)

    logger.error("Все попытки завершились неудачей.")
    return None

