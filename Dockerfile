FROM python:3.10-slim

# Установка необходимых пакетов
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    chromium \
    chromium-driver \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Установка Python-зависимостей
RUN mkdir /bot
COPY requirements.txt /bot/
RUN python -m pip install --no-cache-dir -r /bot/requirements.txt

# Копирование кода приложения
COPY . /bot

# Установка переменной окружения для Chrome
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROME_DRIVER=/usr/bin/chromium-driver

# Установка рабочей директории
WORKDIR /bot

# Запуск приложения
CMD ["python3", "main.py"]