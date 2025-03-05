import asyncio
import os
import re

from config import PROXY
from logger import logger


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

        if any(name in url for name in ('https://youtu.be', 'youtu.be', 'https://www.youtube.com/', 'youtube')):
            format = 'bestvideo[vcodec^=avc1][width<=720][height<=1280]+bestaudio/bestvideo[vcodec^=avc1][width<=1280][height<=720]+bestaudio'
            command = [
                'yt-dlp',
                '--proxy', proxy,
                '--cookies', 'cookies.txt',
                '-o', output_template,
                '-f', format,
                '--merge-output-format', 'mp4',
                '--print', 'after_move:filepath',
                url
            ]

        elif any(name in url for name in ('instagram', 'https://www.instagram')):
            format = await fetch_formats(url, proxy)

            command = [
                'yt-dlp',
                '--proxy', proxy,
                '--cookies', 'cookies.txt',
                '-o', output_template,
                '-f', format,
                '--merge-output-format', 'mp4',
                '--print', 'after_move:filepath',
                url
            ]
        else:
            command = [
                'yt-dlp',
                '--proxy', proxy,
                '--cookies', 'cookies.txt',
                '-o', output_template,
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
