# disable: InsecureRequestWarning: Unverified HTTPS request is being made.
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import sys
import traceback

import logging

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from telegram.ext.callbackcontext import CallbackContext

from db_model import *
from bot_prop import *
from emoji import emojize

from multiprocessing import Process
import subprocess
import os

import json

logging.basicConfig(filename='bot.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)


def start(update, context):
    update.message.reply_text(prnt_user_str(update.message.chat.id), parse_mode=telegram.ParseMode.MARKDOWN)


def send_text(update, context, msg: str = 'Привет мой господин!'):
    acc_list = User.select().where(User.role == 'admin')
    for admin in acc_list:
        try:
            context.bot.send_message(admin.id, msg)
        except:
            pass


def botlist(update, context, edit=False):
    keyboard = []

    if edit:
        update = update.callback_query
    user = update.message.chat
    acc_list = Account.select().where(Account.user == user.id).order_by(Account.id)
    n = 1
    for acc in acc_list:
        if acc.status == 'inactive':
            work_stat = 'Не активен ❌'
        elif acc.work_stat == 'start':
            work_stat = 'Работает ' + emojize(":arrow_forward:", use_aliases=True)
        else:
            work_stat = 'Остановлен ' + emojize(":stop_button:", use_aliases=True)
        keyboard.append([InlineKeyboardButton(text=str(n) + ': ' + work_stat, callback_data=acc.key)])
        n = n + 1

    reply_markup = InlineKeyboardMarkup(keyboard)

    if not edit:
        update.message.reply_text(text=MSG_CHANGE_ACC, reply_markup=reply_markup)
    else:
        update.message.edit_text(text=MSG_CHANGE_ACC, reply_markup=reply_markup)


def button(update, context):
    def prnt_acc_stat():
        keyboard = []
        if acc_info.get().work_stat == 'stop':
            start_stop = 'Запустить ' + emojize(":arrow_forward:", use_aliases=True)
        else:
            start_stop = 'Остановить ' + emojize(":stop_button:", use_aliases=True)

        keyboard.append([InlineKeyboardButton(text=start_stop, callback_data=query.data)])
        keyboard.append([InlineKeyboardButton(text='« Back to Bots List', callback_data='botlist')])

        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.edit_text(text=MSG_START_STOP, reply_markup=reply_markup)

    query = update.callback_query

    # query.edit_message_text(text="Selected option: {}".format(query.data))

    if query:
        if query.data == 'botlist':
            botlist(update, context, 'Edit')
        acc_info = Account.select().where(Account.key == query.data)
        if acc_info:
            if query.message.text == MSG_START_STOP:
                if acc_info.get().work_stat == 'start':
                    Account.update(work_stat='stop').where(Account.key == query.data).execute()
                else:
                    Account.update(work_stat='start').where(Account.key == query.data).execute()
                prnt_acc_stat()
            elif query.message.text == MSG_CHANGE_ACC:
                if acc_info.get().status == 'active':
                    prnt_acc_stat()
                else:
                    update.callback_query.answer(show_alert=True, text="Аккаунт не активен")


def help(update, context):
    update.message.reply_text("Use /start to run bot.")


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


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


def sender(context):
    while True:
        for msg in Message.select().where(Message.date_send.is_null()):
            if msg.file_type == 'document':
                if msg.blob:

                    if not os.path.isfile(msg.file_name):
                        with open(msg.file_name, 'w', encoding='utf-8') as b:
                            b.write(msg.blob.decode())

                    doc = open(msg.file_name, 'rb')
                    context.bot.send_document(msg.to_user, doc)
                    doc.close()

                    if os.path.isfile(msg.file_name):
                        os.remove(msg.file_name)
                    Message.update(date_send=round(time.time())).where(Message.id == msg.id).execute()
        time.sleep(60)


def main():
    updater = Updater(TOKEN, use_context=True, request_kwargs=REQUEST_KWARGS)
    dispatcher = updater.dispatcher
    context = CallbackContext(dispatcher)
    
    prc_acc = Process(target=starter)
    prc_acc.start()
    
    prc_sender = Process(target=sender, args=(context, ))
    prc_sender.start()

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('hello', send_text))
    updater.dispatcher.add_handler(CommandHandler('botlist', botlist))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    updater.dispatcher.add_handler(CommandHandler('help', help))
    updater.dispatcher.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()
