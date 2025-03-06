import telebot
import threading
from datetime import datetime, timedelta
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from config import *

# Ваш токен бота
TOKEN = TG
bot = telebot.TeleBot(TOKEN)

# Файл для хранения расписания
SCHEDULE_FILE = 'schedule.json'

# Загрузка расписания из файла
def load_schedule():
    try:
        with open(SCHEDULE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Сохранение расписания в файл
def save_schedule(schedule):
    with open(SCHEDULE_FILE, 'w') as f:
        json.dump(schedule, f)

# Инициализация расписания
schedule = load_schedule()

# Функция для отправки напоминания
def send_reminder(chat_id, subject, location):
    message = f'Напоминание: У вас скоро занятие по {subject} в {location}!'
    bot.send_message(chat_id=chat_id, text=message)

# Функция для проверки занятий и отправки напоминаний
def check_schedule():
    while True:
        now = datetime.now()
        for chat_id, classes in schedule.items():
            for class_info in classes:
                start_time = datetime.strptime(class_info['start_time'], '%Y-%m-%d %H:%M')
                if now >= start_time - timedelta(minutes=30) and now < start_time:
                    send_reminder(chat_id, class_info['subject'], class_info['location'])
                    classes.remove(class_info)  # Удаляем занятие после отправки напоминания
                    break  # Выходим из цикла, чтобы избежать изменения списка во время итерации
            save_schedule(schedule)  # Сохраняем расписание после изменений
        time.sleep(60)  # Проверять каждую минуту

# Функция для извлечения данных о занятиях с сайта с использованием Selenium
def fetch_classes():
    options = Options()
    options.headless = True  # Запуск в фоновом режиме без GUI
    service = Service('path/to/chromedriver')  # Укажите путь к chromedriver, если он не в PATH
    driver = webdriver.Chrome(service=service, options=options)

    url = 'URL_ВАШЕГО_САЙТА'  # Замените на реальный URL
    driver.get(url)

    classes = []
    try:
        # Замените селекторы на соответствующие вашему сайту
        time_elements = driver.find_elements(By.CSS_SELECTOR, '._itemLessons__period_couth_')
        subject_elements = driver.find_elements(By.CSS_SELECTOR, '._itemLessons__desc_couth_')

        for time_element, subject_element in zip(time_elements, subject_elements):
            time_info = time_element.text.strip()
            subject_info = subject_element.text.strip()

            # Здесь вам нужно будет добавить логику для парсинга времени и предмета.
            # Пример:
            start_time = datetime.strptime(time_info, '%Y-%m-%d %H:%M')  # Приведите к нужному формату

            classes.append({
                'subject': subject_info,
                'start_time': start_time.strftime('%Y-%m-%d %H:%M'),  # Приведение к строке
                'location': 'Ваше местоположение'  # Замените на реальное местоположение или добавьте логику для его извлечения
            })
    finally:
        driver.quit()  # Закрываем браузер

    return classes

# Команда для добавления занятия
@bot.message_handler(commands=['add_class'])
def add_class(message):
    chat_id = message.chat.id
    try:
        classes = fetch_classes()  # Получаем занятия с сайта
        for class_info in classes:
            subject = class_info['subject']
            start_time = class_info['start_time']  # Убедитесь, что это в формате 'YYYY-MM-DD HH:MM'
            location = class_info['location']

            if str(chat_id) not in schedule:
                schedule[str(chat_id)] = []
            schedule[str(chat_id)].append({
                'subject': subject,
                'start_time': start_time,
                'location': location
            })
            save_schedule(schedule)  # Сохраняем расписание после добавления занятия
            bot.reply_to(message, f'Занятие по {subject} добавлено на {start_time} в {location}.')
    except Exception as e:
        bot.reply_to(message, f'Ошибка: {str(e)}')

# Команда для проверки времени до следующей пары
@bot.message_handler(commands=['timedonext'])
def time_to_next_class(message):
    chat_id = message.chat.id
    now = datetime.now()
    
    if str(chat_id) not in schedule or not schedule[str(chat_id)]:
        bot.reply_to(message, "У вас нет запланированных занятий.")
        return

    next_class = None
    
    for class_info in schedule[str(chat_id)]:
        start_time = datetime.strptime(class_info['start_time'], '%Y-%m-%d %H:%M')
        if start_time > now:
            if next_class is None or start_time < next_class['start_time']:
                next_class = class_info

    if next_class:
        time_diff = next_class['start_time'] - now
        hours, remainder = divmod(time_diff.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        bot.reply_to(message, f"Следующая пара по {next_class['subject']} в {next_class['location']} через {int(hours)} ч {int(minutes)} мин.")
    else:
        bot.reply_to(message, "У вас больше нет занятий на сегодня.")

# Запуск фонового потока для проверки расписания
threading.Thread(target=check_schedule, daemon=True).start()

# Запуск бота
bot.polling(none_stop=True)