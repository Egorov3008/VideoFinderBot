import os
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import random
from fake_useragent import UserAgent
from config import PROXY, BASE_PATH

from logger import logger

async def load_cookies_from_file(cookies_file):
    cookies = []
    with open(cookies_file, 'r', encoding='utf-8') as file:
        for line in file:
            if line.startswith('#') or not line.strip():
                continue
            parts = line.strip().split('\t')
            if len(parts) >= 7:
                cookie = {
                    'domain': parts[0],
                    'name': parts[5],
                    'value': parts[6],
                    'path': parts[2],
                    'secure': parts[3] == 'TRUE',
                    'expiry': int(parts[4]) if parts[4] != '0' else None
                }
                cookies.append(cookie)
    return cookies


async def open_page_with_cookies(url, user_agent, proxy=PROXY):
    try:

        # Настройки для браузера
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Фоновый режим
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument(f'--user-agent={user_agent}')

        # Настройки прокси (если указан)
        if proxy:
            options.add_argument(f'--proxy-server={proxy}')  # Указываем прокси

        # Автоматическая установка ChromeDriver
        service = Service(ChromeDriverManager().install())

        # Инициализация драйвера Chrome
        driver = webdriver.Chrome(service=service, options=options)

        # Открываем страницу
        driver.get(url)

        # Ждём, пока страница загрузится
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )

        cookies_file = os.path.join(BASE_PATH, 'cookies/cookies.txt')
        # Загружаем куки из файла
        cookies = await load_cookies_from_file(cookies_file)

        # Добавляем куки в браузер
        for cookie in cookies:
            # Убедимся, что домен куки соответствует текущему домену
            current_domain = driver.current_url.split('/')[2]  # Получаем текущий домен
            if not cookie['domain'].startswith('.'):
                cookie['domain'] = '.' + cookie['domain']  # Добавляем точку, если её нет

            # Проверяем, что домен куки соответствует текущему домену
            if current_domain.endswith(cookie['domain']) or cookie['domain'].endswith(current_domain):
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    logger.warning(f"Не удалось добавить куки {cookie['name']}: {e}")
            else:
                logger.warning(f"Домен куки {cookie['domain']} не соответствует текущему домену {current_domain}")

        # Обновляем страницу, чтобы применить куки
        driver.refresh()

        # Ждём, пока страница загрузится
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )

        # Получаем обновлённые куки
        updated_cookies = driver.get_cookies()

        # Сохраняем обновлённые куки в файл
        with open(cookies_file, 'w', encoding='utf-8') as file:
            for cookie in updated_cookies:
                domain = cookie.get('domain', '')
                if not domain.startswith('.'):
                    domain = '.' + domain
                domain_specified = 'TRUE' if domain.startswith('.') else 'FALSE'
                path = cookie.get('path', '/')
                secure = 'TRUE' if cookie.get('secure', False) else 'FALSE'
                expires = str(int(cookie.get('expiry', 0))) if 'expiry' in cookie else '0'
                name = cookie.get('name', '')
                value = cookie.get('value', '')
                file.write(f"{domain}\t{domain_specified}\t{path}\t{secure}\t{expires}\t{name}\t{value}\n")

        logger.info(f"Обновлённые куки сохранены в файл: {cookies_file}")
        logger.info("Закрываем браузер")
        driver.quit()

        # Возвращаем путь к файлу куки и пользовательский агент
        return cookies_file



    except Exception as e:
        logger.error(f"Ошибка в open_page_with_cookies: {e}")
        return None
