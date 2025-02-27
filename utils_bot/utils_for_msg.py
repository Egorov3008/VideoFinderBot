from urllib.parse import urlparse
from logger import logger
import subprocess
import ffmpeg
import os


def is_valid_url(url: str) -> bool:
    """
    Проверяет, является ли строка валидным URL.
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])  # Проверяем наличие схемы и домена
    except ValueError:
        return False


def compress_video(input_path, output_path, crf=23):
    """
    Сжимает видео с помощью ffmpeg и удаляет исходный файл.
    :param input_path: Путь к исходному видео.
    :param output_path: Путь к сжатому видео.
    :param crf: Параметр качества (меньше значение = лучше качество, но больше размер файла).
    """
    try:
        # Сжимаем видео
        (
            ffmpeg
            .input(input_path)
            .output(output_path, crf=crf)
            .run()
        )
        logger.info(f"Видео успешно сжато и сохранено в {output_path}")

        # Удаляем исходный файл
        os.remove(input_path)
        logger.info(f"Исходный файл {input_path} удален.")
        return output_path
    except Exception as e:
        logger.info(f"Произошла ошибка при сжатии видео: {e}")
        return None



def split_video(file_path, max_size_mb):
    logger.info("Получаем информацию о видео")
    # Получаем информацию о видео
    list_video = []
    result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    duration = float(result.stdout)
    logger.info("Рассчитываем количество частей")
    # Рассчитываем количество частей
    max_size_bytes = max_size_mb * 1024 * 1024
    bitrate = (os.path.getsize(file_path) * 8) / duration  # битрейт в битах в секунду
    part_duration = (max_size_bytes * 8) / bitrate  # длительность каждой части в секундах
    num_parts = int(duration // part_duration) + 1
    logger.info("Разделяем видео на части")
    #
    for i in range(num_parts):
        start_time = i * part_duration
        output_file = f"{file_path}_part{i + 1}.mp4"
        subprocess.run(['ffmpeg', '-i', file_path, '-ss', str(start_time), '-t', str(part_duration), '-c', 'copy', output_file])
        list_video.append(output_file)

