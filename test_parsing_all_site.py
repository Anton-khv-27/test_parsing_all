from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import os
from time import time
import requests
import csv
from dotenv import load_dotenv
import tempfile

load_dotenv()

# Настройка опций для Chrome в headless-режиме
options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1920,1080')

# Уникальный профиль пользователя для каждой сессии
service = Service("/usr/bin/chromedriver")  # путь в GitHub Actions
driver = webdriver.Chrome(service=service, options=options)
options.add_argument(f'--user-data-dir={tempfile.mkdtemp()}')

# Запуск драйвера
driver = webdriver.Chrome(options=options)
start_time = time()

# Переход на сайт
driver.get("https://testing.rozentalgroup.ru/demo/authorization/")

# Ожидание загрузки поля логина
wait = WebDriverWait(driver, 10)
username_input = wait.until(EC.presence_of_element_located((By.NAME, "login")))
password_input = driver.find_element(By.NAME, "password")

# Заполняем переменные из Secrets
username_input.send_keys(os.environ["login"])
password_input.send_keys(os.environ["password"])
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# Нажимаем кнопку входа
login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
login_button.click()

# Ждём редиректа/результата
wait.until(EC.url_changes("https://testing.rozentalgroup.ru/demo/authorization/"))

# 🔗 Статически заданные ссылки (можно заменить на кортеж)
URLS = [
    "https://dev.rozentalgroup.ru/demo/dispetcher/executors/",
    "https://dev.rozentalgroup.ru/demo/dispetcher/executors/absence-schedule/",
    "https://dev.rozentalgroup.ru/demo/dispetcher/users/",
    "https://dev.rozentalgroup.ru/demo/dispetcher/handbook/companies/",
    "https://dev.rozentalgroup.ru/demo/dispetcher/houses/",
    "https://dev.rozentalgroup.ru/demo/dispetcher/activeTreatments/",
    "https://dev.rozentalgroup.ru/demo/dispetcher/messenger/?section=active",
    "https://dev.rozentalgroup.ru/demo/dispetcher/treatments/paid/#/?section=paid",
    "https://dev.rozentalgroup.ru/demo/dispetcher/task-schedule/journal/?s=in_progress",
    "https://dev.rozentalgroup.ru/demo/dispetcher/task-schedule/",
    "https://dev.rozentalgroup.ru/demo/dispetcher/task-schedule/types/",
    "https://dev.rozentalgroup.ru/demo/dispetcher/easy-life/journal/?section=all",
    "https://dev.rozentalgroup.ru/demo/dispetcher/easy-life/messenger/?section=active",
    "https://dev.rozentalgroup.ru/demo/dispetcher/debtors/dashboard/",
    "https://dev.rozentalgroup.ru/demo/dispetcher/debtors/?list=all",
    "https://dev.rozentalgroup.ru/demo/dispetcher/debtors/analytics/",
    "https://dev.rozentalgroup.ru/demo/dispetcher/debtors/gis/",
    "https://dev.rozentalgroup.ru/demo/dispetcher/passes/?section=one-time",
    "https://dev.rozentalgroup.ru/demo/dispetcher/notifications/?s=active",
    "https://dev.rozentalgroup.ru/demo/dispetcher/inventory/",
    "https://dev.rozentalgroup.ru/demo/dispetcher/module_vote/?page=1&section=all#/",
    "https://dev.rozentalgroup.ru/demo/dispetcher/settings/?section=treatments",
    "https://dev.rozentalgroup.ru/demo/dispetcher/data_loading/",
    "https://testing.rozentalgroup.ru/demo/dispetcher/inventory/",
    "https://test.rozentalgroup.ru/demo/dispetcher/personal_accounts/?page=1&per_page=30",
    "https://abracadabra.vvv"
]

# 📁 Файл для сохранения ошибок
CSV_FILE = "bad_links.csv"

# 🧾 Храним найденные ошибки
bad_pages = []

# Отправка текстового сообщения в Telegram
def send_telegram_message(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("[⚠️] BOT_TOKEN или CHAT_ID не заданы.")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print(f"[Telegram ❌] Ошибка отправки: {response.text}")
    except Exception as e:
        print(f"[Telegram ❗] Исключение при отправке: {e}")

# Отправка файла в Telegram
def send_telegram_file(file_path, caption="Файл"):
    if not BOT_TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    try:
        with open(file_path, "rb") as f:
            response = requests.post(
                url,
                data={"chat_id": CHAT_ID, "caption": caption},
                files={"document": f}
            )
        if response.status_code != 200:
            print(f"[Telegram ❌] Ошибка отправки файла: {response.text}")
    except Exception as e:
        print(f"[Telegram ❗] Ошибка при отправке файла: {e}")

 Проверка всех URL
#for url in URLS:
#    try:
#        driver.get(url)
#        if (
#            "404" in driver.title or
#            "ошибка" in driver.title.lower() or
#            "not found" in driver.page_source.lower()
#        ):
#            bad_pages.append([url, "Обнаружена ошибка на странице", "Ключевое слово в title/page"])
#    except WebDriverException as e:
#        bad_pages.append([url, "Ошибка загрузки страницы", str(e)])

for url in URLS:
    try:
        driver.get(url)
        page_source = driver.page_source.lower()
        title = driver.title.lower()

        # Проверка по содержимому страницы
        if (
            "404" in title
            or "ошибка" in title
            or "not found" in page_source
            or "error" in title
            or "500" in title
            or "502" in title
            or "503" in title
            or "bad gateway" in page_source
            or "service unavailable" in page_source
            or "internal server error" in page_source
            or "maintenance" in page_source
            or "under construction" in page_source
        ):
            bad_pages.append([url, "Обнаружена ошибка на странице", "Ключевое слово в контенте"])

        # Проверка на пустую или подозрительно короткую страницу
        elif len(page_source.strip()) < 500:
            bad_pages.append([url, "Пустая или слишком короткая страница", f"Длина: {len(page_source)} символов"])

        # Проверка на редирект в URL
        elif "error" in driver.current_url.lower() or "404" in driver.current_url.lower():
            bad_pages.append([url, "Редирект на страницу ошибки", driver.current_url])

    except TimeoutException:
        bad_pages.append([url, "Таймаут при загрузке страницы", "TimeoutException"])
    except WebDriverException as e:
        bad_pages.append([url, "Ошибка загрузки страницы", str(e)])
    except Exception as e:
        bad_pages.append([url, "Неизвестная ошибка", str(e)])

# Запись результатов в CSV
try:
    with open(CSV_FILE, mode="w", newline="", encoding="Windows-1251") as f:
        writer = csv.writer(f)
        writer.writerow(["URL", "Описание ошибки", "Тип ошибки"])
        writer.writerows(bad_pages)
except PermissionError:
    print(f"[❗] Нет доступа к файлу {CSV_FILE}. Закройте его, если он открыт.")

# Подготовка текста для Telegram
total_checked = len(URLS)
total_errors = len(bad_pages)
total_ok = total_checked - total_errors
duration = round(time() - start_time, 2)

summary = f"""✅ Проверка завершена

⏱ Время: {duration} сек
🔗 Всего ссылок: {total_checked}
✅ Успешных: {total_ok}
❌ Ошибок: {total_errors}
"""

for i, (url, _, error_type) in enumerate(bad_pages[:10], start=1):
    summary += f"\n{i}. {url}\n   ⛔ {error_type}"

if total_errors > 10:
    summary += f"\n...и ещё {total_errors - 10} ошибок скрыто."

# Отправка результатов
send_telegram_message(summary)
if total_errors > 0:
    send_telegram_file(CSV_FILE, caption="📄 Проблемные страницы")

driver.quit()


