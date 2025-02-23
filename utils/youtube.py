import asyncio

from yt_dlp import YoutubeDL

from logger import logger


async def get_videos(video_url: str):
    """
    Загружает видео с указанного URL с заданным качеством.

    Параметры:
    ----------
    video_url : str
        URL видео, которое необходимо загрузить.
    quality : str
        Максимальная высота видео в пикселях (например, '720' для 720p).
        Загружается лучшее видео и аудио, соответствующее указанному качеству.

    Возвращает:
    ----------
    str
        Путь к загруженному видеофайлу.

    Примечания:
    ----------
    - Используется библиотека youtube-dl для загрузки видео.
    - Файл будет сохранен в папке 'videos' с именем, основанным на заголовке видео.
    - Для загрузки может потребоваться файл с куками (cookies.txt) и прокси-сервер.
    - Убедитесь, что у вас установлены необходимые зависимости и правильно настроены параметры.
    """

    # quality = input("Введите желаемое качество (например, 720, 1080, best): ")
    logger.info("Старт программы")

    proxy = 'http://127.0.0.1:12334'

    logger.info("Приступаю к скачиванию видео")
    try:
        ydl_opts = {
            'outtmpl': 'videos/%(title)s.%(ext)s',
            # Указываем файл с куками
            'proxy': f'{proxy}',
            'cookiefile': 'cookies.txt'
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            file_path = ydl.prepare_filename(info)
        return file_path
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")


