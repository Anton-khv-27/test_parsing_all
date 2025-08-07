from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
import os
from time import time
import requests
import csv
from dotenv import load_dotenv

# Настройка драйвера (для Chrome)
driver = webdriver.Chrome()
#driver.maximize_window()
load_dotenv()

# Настройка Chrome в headless режиме
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

#driver = webdriver.Chrome(options=options)

start_time = time()

# Переход на сайт
driver.get("https://test.rozentalgroup.ru/demo/authorization/")

# Ожидание загрузки поля логина
wait = WebDriverWait(driver, 10)
username_input = wait.until(EC.presence_of_element_located((By.NAME, "login")))
password_input = driver.find_element(By.NAME, "password")

# Вводим логин и пароль
username_input.send_keys(os.environ["login"])  # Вставь свои данные
password_input.send_keys(os.environ["password"])  # Вставь свои данные

# Нажимаем кнопку входа
login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
login_button.click()

# Ждём редиректа/результата
wait.until(EC.url_changes("https://test.rozentalgroup.ru/demo/authorization/"))

# 🔗 Статически заданные ссылки (можно заменить на кортеж)
URLS = [
    "https://test.rozentalgroup.ru/demo/dispetcher/executors/",
    "https://test.rozentalgroup.ru/demo/dispetcher/executors/absence-schedule/",
    "https://test.rozentalgroup.ru/demo/dispetcher/users/",
    "https://test.rozentalgroup.ru/demo/dispetcher/handbook/companies/",
]

# 📁 Файл для сохранения ошибок
CSV_FILE = "bad_links.csv"

# 🧾 Храним найденные ошибки
bad_pages = []

# === Настройки Telegram ===
BOT_TOKEN = os.getenv("bot_token")
CHAT_ID = os.getenv("chat_id")

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

# Проверка всех URL
for url in URLS:
    try:
        driver.get(url)
        if (
            "404" in driver.title or
            "ошибка" in driver.title.lower() or
            "not found" in driver.page_source.lower()
        ):
            bad_pages.append([url, "Обнаружена ошибка на странице", "Ключевое слово в title/page"])
    except WebDriverException as e:
        bad_pages.append([url, "Ошибка загрузки страницы", str(e)])

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

# Не закрываем сразу, чтобы увидеть результат
#input("Нажмите Enter для выхода...")

driver.quit()

