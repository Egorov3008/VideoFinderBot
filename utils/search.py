from yt_dlp import YoutubeDL


def search_youtube(query: str, max_results: int = 5):
    """
    Ищет видео на YouTube по заданному запросу и возвращает список результатов.

    Параметры:
    -----------
    query : str
        Поисковый запрос (например, "котики").
    max_results : int, optional
        Максимальное количество результатов для возврата (по умолчанию 5).

    Возвращает:
    -----------
    list of dict
        Список словарей, где каждый словарь содержит информацию о видео:
        - 'title': Название видео.
        - 'url': Ссылка на видео.
        - 'thumbnail': URL обложки видео.
        - 'duration': Длительность видео в секундах.
        - 'views': Количество просмотров.
    """
    # Настройки для yt-dlp
    proxy = 'http://127.0.0.1:12334'
    ydl_opts = {
        'extract_flat': True,  # Извлекать информацию без скачивания
        'quiet': False,  # Не выводить лишние сообщения в консоль
        'force_generic_extractor': True,
        'proxy': f'{proxy}'
        # Использовать общий экстрактор
    }

    # Используем yt-dlp для поиска видео
    with YoutubeDL(ydl_opts) as ydl:
        # Формируем URL для поиска (ytsearchX:query, где X — количество результатов)
        search_url = f"ytsearch{max_results}:{query}"

        # Извлекаем информацию о видео
        info = ydl.extract_info(search_url, download=False)

        # Обрабатываем результаты
        results = []
        for entry in info['entries']:
            results.append({
                'title': entry['title'],  # Название видео
                'url': entry['url'],  # Ссылка на видео
                'thumbnail': entry['thumbnails'][0]['url'] if entry.get('thumbnails') else None,  # Обложка видео
                'duration': entry.get('duration'),  # Длительность видео
                'views': entry.get('view_count')  # Количество просмотров
            })

        return results



