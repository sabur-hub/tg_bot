import os
import telebot
from telebot import types
import logging
import psycopg2
from config import *
from flask import Flask, request

bot = telebot.TeleBot(BOT_TOKEN)
server = Flask(__name__)
logger = telebot.logger
logger.setLevel(logging.DEBUG)

db_connection = psycopg2.connect(DB_URI, sslmode="require")
db_object = db_connection.cursor()


def update_messages_count(user_id):
    db_object.execute(f"UPDATE users SET messages = messages + 1 WHERE id = {user_id}")
    db_connection.commit()


@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username
    db_object.execute(f"SELECT id FROM users WHERE id = {user_id}")
    result = db_object.fetchone()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton('🇷🇺 Русский')
    item2 = types.KeyboardButton('🇺🇸 English')
    item3 = types.KeyboardButton('🇪🇬 عربي')

    markup.add(item2, item1, item3)

    bot.send_message(message.chat.id, 'Привет выберите язык для продолжения взаимодействия.'
                                      'Hi, select a language to continue the interaction.'
                                      ' اَلسَّلَامُ عَلَيْكُم حدد اللغة لمواصلة التفاعل.'.format(message.from_user),
                     reply_markup=markup)

    if not result:
        db_object.execute("INSERT INTO users(id, username, messages) VALUES (%s, %s, %s)", (user_id, username, 0))
        db_connection.commit()

    update_messages_count(user_id)


@bot.message_handler(commands=["text"])
def choise_lang(message):
    if message.chat.type == 'private':
        if message.text == '🇺🇸 English':
            bot.send_message(message.chat.id, 'Enter you name pleace')
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item1 = types.KeyboardButton('for russian language course')
            item2 = types.KeyboardButton('Medical')
            item3 = types.KeyboardButton('tech Univercity')
            markup.add(item2, item1, item3)
            bot.send_message(message.chat.id, '🇺🇸 English', reply_markup=markup)
        elif message.text == '🇷🇺 Русский':
            bot.send_message(message.chat.id, 'Введите своё имя')
        elif message.text == '🇪🇬 عربي':
            bot.send_message(message.chat.id, 'أدخل أسمك')


@bot.message_handler(commands=["stats"])
def get_stats(message):
    db_object.execute("SELECT * FROM users ORDER BY messages DESC LIMIT 10")
    result = db_object.fetchall()

    if not result:
        bot.reply_to(message, "No data...")
    else:
        reply_message = "- Top flooders:\n"
        for i, item in enumerate(result):
            reply_message += f"[{i + 1}] {item[1].strip()} ({item[0]}) : {item[2]} messages.\n"
        bot.reply_to(message, reply_message)

    update_messages_count(message.from_user.id)


@bot.message_handler(func=lambda message: True, content_types=["text"])
def message_from_user(message):
    user_id = message.from_user.id
    update_messages_count(user_id)


@server.route(f"/{BOT_TOKEN}", methods=["POST"])
def redirect_message():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200


if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL)
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
