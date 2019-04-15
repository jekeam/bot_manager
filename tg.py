# coding:utf-8
import logging

from db_model import *
from tg_prop import *

import telebot
from telebot import apihelper


bot = telebot.TeleBot(TOKEN)
print('set proxy: ' + str(PROXY))
apihelper.proxy = PROXY

#logger = telebot.logger
#telebot.logger.setLevel(logging.DEBUG) # Outputs debug messages to console.

@bot.message_handler(commands=['start'])
def send_welcome(message):
    global ROLE
    
    user_id = message.from_user.id
    ROLE = get_user(user_id).rules
    print('user_id: {}, set role:{}'.format(user_id, ROLE))
    bot.reply_to(message, prnt_user_str(user_id), parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def echo_all(message):
	bot.reply_to(message, message.text)

if __name__ == '__main__':
    bot.polling(none_stop=True, timeout=123)