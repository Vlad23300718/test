import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from telebot import TeleBot, types
from config import *

# Замените на ваш токен бота
TOKEN = TG
bot = TeleBot(TOKEN)

# Словарь для хранения названий групп пользователей
user_groups = {}

def parse_schedule(group_name):
    # Настройка браузера для работы в фоновом режиме
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')

    # Инициализация драйвера
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(URL)

    # Ввод группы в поле с id=allGroups
    group_input = driver.find_element(By.ID, 'allGroups')
    group_input.clear()  # Очистка поля ввода перед вводом нового значения
    group_input.send_keys(group_name)

    # Здесь необходимо добавить код для отправки формы или обновления расписания,
    # если это требуется на сайте. Возможно, потребуется нажать кнопку или выполнить JavaScript.

    # Ожидание загрузки расписания (можно использовать WebDriverWait для более надежного ожидания)
    time.sleep(3)  # Увеличьте время, если страница загружается медленно

    # Извлечение расписания из элемента с классом _itemSchedule_couth_4
    schedule_items = driver.find_elements(By.CLASS_NAME, '_itemSchedule_couth_4')
    
    schedule = '\n'.join(item.text for item in schedule_items)  # Объединяем текст всех элементов

    # Закрытие браузера
    driver.quit()

    return schedule

@bot.message_handler(commands=['start'])
def start_message(message):
    # Создаем клавиатуру с кнопкой "Получить расписание"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Получить расписание"))
    
    # Отправляем сообщение с клавиатурой
    bot.send_message(message.chat.id, "Привет! Нажмите кнопку 'Получить расписание', чтобы начать.", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Получить расписание")
def ask_for_group(message):
    # Запрашиваем у пользователя название группы
    bot.send_message(message.chat.id, "Введите название вашей группы.")

@bot.message_handler(func=lambda message: True)
def get_group_name(message):
    chat_id = message.chat.id
    group_name = message.text.strip()
    
    # Сохраняем название группы для пользователя
    user_groups[chat_id] = group_name

    # Уведомляем пользователя о начале загрузки расписания
    bot.send_chat_action(chat_id, 'typing')  # Показываем, что бот "печатает"
    loading_message = bot.send_message(chat_id, "Расписание загружается...")  # Сообщение о загрузке

    # Получаем расписание
    schedule = parse_schedule(group_name)

    # Удаляем сообщение "Расписание загружается..."
    bot.delete_message(chat_id, loading_message.message_id)

    if schedule:
        bot.send_message(chat_id, f"Расписание для группы {group_name}:\n{schedule}")
    else:
        bot.send_message(chat_id, "Не удалось получить расписание. Попробуйте другую группу.")

if __name__ == '__main__':
    bot.polling(none_stop=True)