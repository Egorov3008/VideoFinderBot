import asyncio
import os

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError, GeoRestrictedError

from logger import logger
from utils.cookies import get_params_for_ssesion


# Настройка логгера


async def get_videos(video_url: str, retry: bool = True):
    """
    Загружает видео с указанного URL.

    Параметры:
    ----------
    video_url : str
        URL видео, которое необходимо загрузить.
    retry : bool
        Флаг для повторной попытки загрузки после обновления кук и User-Agent.

    Возвращает:
    ----------
    str
        Путь к загруженному видеофайлу.
    """
    logger.info("Старт программы")

    # Создаем папку для видео, если её нет
    os.makedirs('videos', exist_ok=True)

    proxy = 'http://127.0.0.1:12334'  # Убедитесь, что прокси работает

    logger.info("Приступаю к скачиванию видео")

    ydl_opts = {
            'format': 'bv*[ext=mp4]',
            'outtmpl': 'videos/%(title)s.%(ext)s',
            'proxy': proxy,  # Убедитесь, что файл существует
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            file_path = ydl.prepare_filename(info)

        if os.path.exists(file_path):
            logger.info(f"Видео успешно загружено: {file_path}")
            return file_path
        else:
            logger.error("Файл не был загружен")
            return None

    except (DownloadError, GeoRestrictedError) as e:
        logger.error(f"Ошибка загрузки видео: {e}")
        if retry:
            logger.info("Попытка обновить куки и User-Agent...")
            # Вызываем функцию для получения новых кук и User-Agent
            params = await get_params_for_ssesion()

            # Проверяем, что куки и User-Agent получены
            if not params['cookies_file'] or not params['user_agent']:
                logger.error("Не удалось получить куки или User-Agent.")
                return None

            # Обновляем параметры запроса
            ydl_opts['cookiefile'] = params['cookies_file']
            ydl_opts['http_headers']['User-Agent'] = params['user_agent']

            await asyncio.sleep(5)
            # Повторно вызываем get_videos с обновленными параметрами
            logger.info("Повторная попытка загрузки видео...")
            return await get_videos(video_url, retry=False)
        else:
            logger.error("Повторная попытка загрузки не удалась.")
            return None
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
        return None

#
# video = "https://youtu.be/jcCurJBfjIc?si=hztqxrsRhQz_Wt6b"
# asyncio.run(get_videos(video))
