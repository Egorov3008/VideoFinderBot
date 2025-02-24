from urllib.parse import urlparse
import ffmpeg


def is_valid_url(url: str) -> bool:
    """
    Проверяет, является ли строка валидным URL.
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])  # Проверяем наличие схемы и домена
    except ValueError:
        return False






