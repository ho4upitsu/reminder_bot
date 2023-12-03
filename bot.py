import threading
import os

import telebot
from telebot import types
from datetime import datetime, timedelta
import time

from dotenv import load_dotenv
load_dotenv()
TOKEN = os.environ.get("TOKEN")
bot = telebot.TeleBot(token=TOKEN)

reminders = []


@bot.message_handler(commands=['start'])
def get_start_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    new_reminder_btn = types.KeyboardButton('Нове нагадування')
    delete_reminder_btn = types.KeyboardButton('Видалити нагадування')
    all_reminders_btn = types.KeyboardButton('Всі нагадування')

    markup.add(new_reminder_btn, delete_reminder_btn ,all_reminders_btn)
    bot.send_message(message.from_user.id, 'Що ти хочеш зробити?', reply_markup=markup)


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text == 'Нове нагадування':
        create_reminder(message.from_user.id)

    elif message.text == 'Всі нагадування':
        get_all_reminders(message.from_user.id)

    elif message.text == 'Видалити нагадування':
        ask_for_delete_reminder_name(message.from_user.id)

def create_reminder(user_id):
    bot.send_message(user_id, "Дай нагадуванню ім'я")
    bot.register_next_step_handler_by_chat_id(user_id, process_name_step)


def process_name_step(message):
    name = message.text
    bot.send_message(message.from_user.id, f"Обране ім'я нагадування - {name}")

    bot.send_message(message.from_user.id, 'Через скільки днів нагадати')
    bot.register_next_step_handler_by_chat_id(message.from_user.id, process_days_step, name)


def process_days_step(message, name):
    try:
        days = int(message.text)
        if days < 0:
            raise ValueError()

        elif days == 0:
            bot.send_message(message.from_user.id, f'Нагадування "{name}" буде сьогодні.')

        else:
            bot.send_message(message.from_user.id, f'Нагадування "{name}" буде через {days} днів.')

        # Розрахунок дати нагадування
        reminder_date = (datetime.now() + timedelta(days=days)).strftime('%d.%m')

        bot.send_message(message.from_user.id, 'Введи час нагадування (наприклад, 15:30):')
        bot.register_next_step_handler(message, process_time_step, name, reminder_date, message.from_user.id)

    except ValueError:
        bot.send_message(message.from_user.id, 'Неправильний формат кількості днів. Введи ціле не від\'ємне число:')
        bot.register_next_step_handler(message, process_days_step, name)


def process_time_step(message, name, reminder_date, user_id):
    time = message.text

    try:
        # Перевірка формату часу
        datetime.strptime(time, '%H:%M')
        bot.send_message(user_id, f'Обраний час нагадування: {time}')

        # Зберегти нагадування в список
        new_reminder = Reminder(name, reminder_date, time, user_id)
        reminders.append(new_reminder)

        bot.send_message(user_id, 'Нагадування створено!')

    except ValueError:
        bot.send_message(user_id, 'Неправильний формат часу. Введи час в форматі "година:хвилина" (наприклад, 15:30):')
        bot.register_next_step_handler_by_chat_id(user_id, process_time_step, name, reminder_date, user_id)


def get_all_reminders(user_id):
    if not reminders:
        bot.send_message(user_id, "Нагадувань ще немає, але можна створити нові :)")
    else:
        all_reminders_text = 'Всі нагадування: \n'
        for reminder in reminders:
            all_reminders_text += f'{reminder.name} на {reminder.day} о {reminder.time} \n'
        bot.send_message(user_id, all_reminders_text, parse_mode='Markdown')


def ask_for_delete_reminder_name(user_id):
    if not reminders:
        bot.send_message(user_id, "Ще немає чого видаляти :)")
    else:
        bot.send_message(user_id, "Введи ім'я нагадування, яке треба видалити?")
        bot.register_next_step_handler_by_chat_id(user_id, delete_reminder)


def delete_reminder(message):
    reminder_name = message.text
    found = False

    for reminder in reminders:
        if reminder.name == reminder_name:
            reminders.remove(reminder)
            found = True
            bot.send_message(message.from_user.id, 'Нагадування видалено')
            break

    if not found:
        bot.send_message(message.from_user.id, 'Нагадування не знайдено')

def check_reminders():
    while True:
        current_time = datetime.now().strftime('%H:%M')

        for reminder in reminders:
            if current_time == reminder.time:
                bot.send_message(reminder.user_id, f"Нагадування: {reminder.name}")
                reminders.remove(reminder)

        time.sleep(30)  # Почекати 60 секунд перед наступною перевіркою

class Reminder:
    def __init__(self, name, day, time, user_id):
        self.name = name
        self.day = day
        self.time = time
        self.user_id = user_id


if __name__ == "__main__":
    # Запустити фоновий процес для перевірки нагадувань
    check_thread = threading.Thread(target=check_reminders)
    check_thread.start()

    # Запустити бота
    bot.polling(none_stop=True, interval=0)
