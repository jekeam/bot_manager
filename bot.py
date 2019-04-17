# coding:utf-8
import urllib3

# disable: InsecureRequestWarning: Unverified HTTPS request is being made.
# See: https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warningsInsecureRequestWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import logging
import sys
import traceback

from db_model import *
from bot_prop import *

import telebot
from telebot import types
from telebot import apihelper
from emoji import emojize

from multiprocessing import Process
import subprocess
import os

bot = telebot.TeleBot(TOKEN)
print('set proxy: ' + str(PROXY2))
apihelper.proxy = PROXY2
USER_ID = None


logging.basicConfig(filename='bot.log', level=logging.DEBUG)
logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG) # Outputs debug messages to console.

@bot.message_handler(commands=['start'])
def send_user_info(message):
    print('chat_id: ' + str(message.chat.id))
    bot.reply_to(message, prnt_user_str(message.from_user.id))


@bot.message_handler(commands=['hello'])
def send_message(msg: str = 'Привет админ, я работаю!'):
    acc_list = User.select().where(User.role == 'admin')
    for admin in acc_list:
        bot.send_message(admin.id, msg)


@bot.message_handler(commands=['botlist'])
def send_bot_list(message, msg: str = 'Выберите ваш аккаунт', edit=False):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    acc_list = Account.select().where(Account.user == message.from_user.id).order_by(Account.id)
    n = 1
    for acc in acc_list:
        if acc.status == 'inactive':
            work_stat = 'Не активен ❌'
        elif acc.work_stat == 'start':
            work_stat = 'Работает ' + emojize(":arrow_forward:", use_aliases=True)
        else:
            work_stat = 'Остановлен ' + emojize(":stop_button:", use_aliases=True)
        callback_button = types.InlineKeyboardButton(text=str(n) + ': ' + work_stat, callback_data=acc.key)
        keyboard.add(callback_button)
        n = n + 1
    if not edit:
        bot.send_message(message.from_user.id, msg, reply_markup=keyboard)
    else:
        bot.edit_message_text(
            chat_id=message.from_user.id,
            message_id=message.message.message_id,
            text=msg,
            reply_markup=keyboard
        )


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    print(message.text)
    # bot.reply_to(message, message.text)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    def prnt_acc_stat():
        keyboard_acc = types.InlineKeyboardMarkup(row_width=2)
        if acc_info.get().work_stat == 'stop':
            start_stop = 'Запустить ' + emojize(":arrow_forward:", use_aliases=True)
        else:
            start_stop = 'Остановить ' + emojize(":stop_button:", use_aliases=True)
        callback_button = types.InlineKeyboardButton(text=start_stop, callback_data=call.data)
        keyboard_acc.row(callback_button)

        callback_bot_list = types.InlineKeyboardButton(text='« Back to Bots List', callback_data='botlist')
        keyboard_acc.row(callback_bot_list)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text='Запуск / Остановка',
            reply_markup=keyboard_acc
        )

    # Если сообщение из чата с ботом
    if call.message:
        if call.data == 'botlist':
            send_bot_list(call, edit=True)
        acc_info = Account.select().where(Account.key == call.data)
        if acc_info:
            if call.message.text == 'Запуск / Остановка':
                if acc_info.get().work_stat == 'start':
                    Account.update(work_stat='stop').where(Account.key == call.data).execute()
                    Account.update(work_stat='stop').where(Account.key == call.data).execute()
                else:
                    Account.update(work_stat='start').where(Account.key == call.data).execute()
                prnt_acc_stat()
            elif call.message.text == 'Выберите ваш аккаунт':
                if acc_info.get().status == 'active':
                    prnt_acc_stat()
                else:
                    bot.answer_callback_query(call.id, show_alert=True, text="Аккаунт не активен")


def starter():
    def start(key: str):  # abs_path:str
        # os.chdir(abs_path)
        if os.path.isfile('better.py'):
            call_str = 'python3.6 better.py --key ' + key
            print('dir: ' + str(os.getcwd()) + ', command: ' + call_str)
            subprocess.call(call_str, shell=True)
        else:
            print('file better.py not found in ' + str(os.getcwd()))
    
    Account.update(pid=0).where(Account.pid > 0).execute()
    while True:
        for acc in Account.select().where((Account.status == 'active') & (Account.work_stat == 'start') & (Account.pid == 0)):
            print(''.ljust(120, '*'))
            print('start: ', acc.key)  # acc.work_dir,
            acc_start = Process(target=start, args=(acc.key,))  # acc.work_dir,
            acc_start.start()
            while Account.select().where(Account.key == acc.key).get().pid == 0:
                print('wait start: ' + str(acc.key))
                time.sleep(2)
        time.sleep(2)


def sender():
    while True:
        for msg in Message.select().where(Message.date_send.is_null()):
            if msg.file_type == 'document':
                if msg.blob:

                    if not os.path.isfile(msg.file_name):
                        with open(msg.file_name, 'w', encoding='utf-8') as b:
                            b.write(msg.blob.decode())

                    doc = open(msg.file_name, 'rb')
                    bot.send_document(msg.to_user, doc)
                    doc.close()

                    #if os.path.isfile(msg.file_name):
                        #os.remove(msg.file_name)
                    Message.update(date_send=round(time.time())).where(Message.id == msg.id).execute()
        time.sleep(10)


if __name__ == '__main__':
    prc_acc = Process(target=starter)
    prc_acc.start()
    prc_sender = Process(target=sender)
    prc_sender.start()
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            err_str = str(e) + ' ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
            for admin in ADMINS:
                bot.send_message(admin, str(e))
        finally:
            time.sleep(15)
