# coding:utf-8
import logging

from db_model import *
from tg_prop import *

import telebot
from telebot import types
from telebot import apihelper

bot = telebot.TeleBot(TOKEN)
print('set proxy: ' + str(PROXY2))
apihelper.proxy = PROXY2
USER_ID = None


# logger = telebot.logger
# telebot.logger.setLevel(logging.DEBUG) # Outputs debug messages to console.

@bot.message_handler(commands=['start'])
def send_welcome(message):
    print('chat_id: ' + str(message.chat.id))
    bot.reply_to(message, prnt_user_str(message.from_user.id), parse_mode='Markdown')


@bot.message_handler(commands=['botlist'])
def send_bot_list(message):
    keyboard = types.InlineKeyboardMarkup()
    acc_list = Account.select().where(Account.user == message.from_user.id).order_by(Account.id)
    n = 1
    for acc in acc_list:
        if acc.status == 'active':
            status = acc.status + ' ✅'
        else:
            status = acc.status + ' ❌'
        callback_button = types.InlineKeyboardButton(text=str(n) + ' - ' + status, callback_data=acc.key)
        keyboard.add(callback_button)
        n = n + 1
    bot.send_message(message.chat.id, "Выберите ваш аккаунт", reply_markup=keyboard)


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    print(message.text)
    bot.reply_to(message, message.text)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    # Если сообщение из чата с ботом
    if call.message:
        if call.data:  # == "test":
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Пыщь")
    # # Если сообщение из инлайн-режима
    # elif call.inline_message_id:
    #     if call.data == "test":
    #         bot.edit_message_text(inline_message_id=call.inline_message_id, text="Бдыщь")


if __name__ == '__main__':
    bot.polling(none_stop=True, timeout=20)
