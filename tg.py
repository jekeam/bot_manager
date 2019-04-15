# coding:utf-8
import logging

from db_model import *
from tg_prop import *

import telebot
from telebot import types
from telebot import apihelper

bot = telebot.TeleBot(TOKEN)
print('set proxy: ' + str(PROXY))
apihelper.proxy = PROXY


# logger = telebot.logger
# telebot.logger.setLevel(logging.DEBUG) # Outputs debug messages to console.

@bot.message_handler(commands=['start'])
def send_welcome(message):
    global ROLE

    user_id = message.from_user.id
    ROLE = get_user(user_id).role
    print('user_id: {}, set role:{}'.format(user_id, ROLE))
    bot.reply_to(message, prnt_user_str(user_id), parse_mode='Markdown')


@bot.message_handler(commands=['botlist'])
def send_bot_list(message):
    keyboard = types.InlineKeyboardMarkup()
    callback_button = types.InlineKeyboardButton(text="Нажми меня", callback_data="test")
    keyboard.add(callback_button)
    bot.send_message(message.chat.id, "Я – сообщение из обычного режима", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    # Если сообщение из чата с ботом
    if call.message:
        if call.data == "test":
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Пыщь")
    # # Если сообщение из инлайн-режима
    # elif call.inline_message_id:
    #     if call.data == "test":
    #         bot.edit_message_text(inline_message_id=call.inline_message_id, text="Бдыщь")


if __name__ == '__main__':
    bot.polling(none_stop=True, timeout=123)
