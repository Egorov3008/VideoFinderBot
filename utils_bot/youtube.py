import asyncio
import os

from yt_dlp import YoutubeDL

from logger import logger


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
    #
    # coockie: dict = await get_params_for_ssesion(video_url)
    #
    # if not coockie.get("cookies_file") or not coockie.get("user_agent"):
    #     logger.error("Не удалось получить куки или User-Agent")
    #     return None

    # logger.debug(f"Передавемые значения в запрос:\n"
    #              f"coockies : {coockie.get('cookies_file')}\n"
    #              f"User-Agent: {coockie.get('user_agent')}")

    format = 'bv*[ext=mp4][height<=720][height>=420]+bestaudio[ext=m4a]/best[ext=mp4][height<=720][height>=420]/best'
    logger.info("Приступаю к скачиванию видео")
    if any(name in video_url for name in ('insta', 'pin.it')):
        logger.debug("Не youtube")
        format = None

    ydl_opts = {
        'format': format,
        'outtmpl': 'videos/%(title)s.%(ext)s',
        'cookiefile': 'cookies.txt',
        # 'cookiesfrombrowser': ('chrome',),
        'proxy': proxy,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 14; moto g 5G - 2024 Build/U1UFNS34.41-98-3-13; ) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36 EdgA/124.0.2478.64'
        }
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            file_path = ydl.prepare_filename(info)

            return file_path

    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
        return None


#
# video = "https://youtu.be/wpfpey_0G5A?si=SNgc8nXrVOdec8VJ"
# asyncio.run(get_videos(video))
# # get_video_urls(video)
