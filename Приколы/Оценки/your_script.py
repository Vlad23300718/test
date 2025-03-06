import requests
from bs4 import BeautifulSoup
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Данные для авторизации на Moodle
MOODLE_LOGIN_URL = "https://moodle.inueco.ru/login/index.php"
MOODLE_GRADES_URL = "https://moodle.inueco.ru/blocks/lk_inueco/lk_pages/current_grades.php?returnurl=https%3A%2F%2Fmoodle.inueco.ru%2Fmy%2Findex.php"
USERNAME = "23300718"  # Замените на ваш логин
PASSWORD = "DH265Eyp"  # Замените на ваш пароль

# Список предметов для учебного года 2024-2025
SUBJECTS_2024_2025 = [
    "Администрирование в информационных системах",
    "Алгоритмизация и технологии программирования",
    "Архитектура информационных систем",
    "Бизнес-процессы и основы организационного управления",
    "Высшая математика",
    "Деловые коммуникации",
    "Дискретная математика и математическая логика",
    "Корпоративные информационные системы",
    "Методы и средства проектирования информационных систем и технологий",
    "Моделирование процессов и систем",
    "Мультимедиа технологии и компьютерная графика",
    "Оздоровительная рекреационная двигательная активность",
    "Прикладное программирование",
    "Теория информационных процессов и систем",
    "Физика",
    "Электронный документооборот",
]

# Функция для авторизации на Moodle
def login_to_moodle():
    session = requests.Session()
    payload = {
        "username": USERNAME,
        "password": PASSWORD,
    }
    response = session.post(MOODLE_LOGIN_URL, data=payload)
    if response.status_code == 200:
        print("Авторизация на Moodle успешна")
        # Проверяем, что мы действительно авторизовались
        profile_response = session.get("https://moodle.inueco.ru/my/")
        if "Мой профиль" in profile_response.text:  # Ищем текст, который есть только после авторизации
            print("Успешная проверка авторизации")
            return session
        else:
            print("Ошибка: авторизация не прошла")
            return None
    else:
        print("Ошибка авторизации на Moodle")
        return None

# Функция для парсинга оценок
def parse_grades(session, subject=None):
    response = session.get(MOODLE_GRADES_URL)
    soup = BeautifulSoup(response.text, "html.parser")

    # Пример извлечения оценок (зависит от структуры HTML)
    grades = []
    for item in soup.find_all("tr"):  # Ищем строки таблицы
        if subject and subject.lower() in item.text.lower():
            grades.append(item.text.strip())
        elif not subject:
            grades.append(item.text.strip())
    return grades

# Команда /start для Telegram-бота
async def start(update: Update, context: CallbackContext):
    keyboard = [["Учебный год 2023-2024", "Учебный год 2024-2025"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Выберите учебный год:", reply_markup=reply_markup)

# Обработка выбора учебного года
async def handle_year(update: Update, context: CallbackContext):
    year = update.message.text
    if year == "Учебный год 2024-2025":
        keyboard = [SUBJECTS_2024_2025[i:i + 2] for i in range(0, len(SUBJECTS_2024_2025), 2)]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        await update.message.reply_text("Выберите предмет:", reply_markup=reply_markup)
    else:
        session = login_to_moodle()
        if session:
            grades = parse_grades(session)
            if grades:
                await update.message.reply_text("\n".join(grades))
            else:
                await update.message.reply_text("Оценки не найдены.")
        else:
            await update.message.reply_text("Ошибка авторизации на Moodle.")

# Обработка выбора предмета
async def handle_subject(update: Update, context: CallbackContext):
    subject = update.message.text
    session = login_to_moodle()
    if session:
        grades = parse_grades(session, subject)
        if grades:
            await update.message.reply_text(f"Оценки по предмету {subject}:\n" + "\n".join(grades))
        else:
            await update.message.reply_text(f"Оценки по предмету {subject} не найдены.")
    else:
        await update.message.reply_text("Ошибка авторизации на Moodle.")

# Запуск Telegram-бота
def main():
    application = Application.builder().token("8161327450:AAEzkWMM4zgcPfzJ2Sng5IfiV73ZbwfqQUU").build()  # Замените на ваш токен

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Text(["Учебный год 2023-2024", "Учебный год 2024-2025"]), handle_year))
    application.add_handler(MessageHandler(filters.Text(SUBJECTS_2024_2025), handle_subject))

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()