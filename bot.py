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

from db_model import Account, Message, User, prnt_user_str, send_message_bot
from bot_prop import *
from emoji import emojize

from threading import Thread
import os

import datetime
import time
from utils import prop_abr

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
    for acc in acc_list:

        if acc.date_end:
            date_end = datetime.datetime.fromtimestamp(acc.date_end)
            date_end_str = '(до ' + date_end.strftime('%d.%m.%Y') + ')'
        else:
            date_end_str = '(бессрочно)'

        if acc.status == 'inactive':
            work_stat = emojize(':x:', use_aliases=True) + ' Не активен' + ' ' + date_end_str
        elif acc.work_stat == 'start':
            work_stat = emojize(':arrow_forward:', use_aliases=True) + ' Работает ' + date_end_str
        else:
            work_stat = emojize(':stop_button:', use_aliases=True) + ' Остановлен ' + date_end_str
        keyboard.append([InlineKeyboardButton(text=str(acc.id) + ': ' + work_stat, callback_data=acc.key)])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if not edit:
        update.message.reply_text(text=MSG_CHANGE_ACC, reply_markup=reply_markup)
    else:
        update.message.edit_text(text=MSG_CHANGE_ACC, reply_markup=reply_markup)


ACC_ACTIVE = 0


def button(update, context):
    global ACC_ACTIVE

    def prnt_acc_stat():
        keyboard = []
        if acc_info.get().work_stat == 'stop':
            start_stop = emojize(":arrow_forward:", use_aliases=True) + ' Запустить'
        else:
            start_stop = emojize(":stop_button:", use_aliases=True) + 'Остановить'

        keyboard.append([InlineKeyboardButton(text=start_stop, callback_data=query.data)])
        keyboard.append([InlineKeyboardButton(text=emojize(':wrench:', use_aliases=True) + ' Настройки', callback_data='pror_edit')])
        keyboard.append([InlineKeyboardButton(text=emojize(':back:', use_aliases=True) + ' Back to Bots List', callback_data='botlist')])

        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.edit_text(text=MSG_START_STOP, reply_markup=reply_markup)

    query = update.callback_query

    # query.edit_message_text(text="Selected option: {}".format(query.data))

    if query:
        if query.data == 'botlist':
            botlist(update, context, 'Edit')
        acc_info = Account.select().where(Account.key == query.data)
        if query.data == 'pror_edit':
            print('pror_edit: ' + str(query))
        if acc_info:
            ACC_ACTIVE = acc_info.get().id
            print('ACC_ACTIVE: ' + str(ACC_ACTIVE))
            if query.message.text == MSG_START_STOP:
                if acc_info.get().work_stat == 'start':
                    Account.update(work_stat='stop').where(Account.key == query.data).execute()
                    send_message_bot(
                        acc_info.get().user_id,
                        str(acc_info.get().id) + ': Аккаунт в процессе остановки, это может занять несколько минут, пожалуйста подождите... ',
                        ADMINS
                    )
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


def sender(context):
    try:
        while True:
            for msg in Message.select().where(Message.date_send.is_null()):
                try:
                    if msg.file_type == 'document':
                        if msg.blob:

                            if not os.path.isfile(msg.file_name):
                                with open(msg.file_name, 'w', encoding='utf-8') as b:
                                    b.write(msg.blob.decode())

                            doc = open(msg.file_name, 'rb')
                            context.bot.send_document(msg.to_user, doc)
                            doc.close()

                            # if os.path.isfile(msg.file_name):
                            #     os.remove(msg.file_name)
                            Message.update(date_send=round(time.time())).where(Message.id == msg.id).execute()
                    elif msg.file_type == 'message':
                        context.bot.send_message(msg.to_user, msg.text[0:4000])
                        Message.update(date_send=round(time.time())).where(Message.id == msg.id).execute()
                except Exception as e:
                    for admin in ADMINS:
                        if str(e) == 'database is locked':
                            context.bot.send_message(admin,
                                                     'Возникла ошибка:{}, msg:{} - сообщение будет отправлено повторно'
                                                     .format(str(e), 'msg_id: ' + str(msg.id) + ', user_id:' + str(msg.to_user)))
                        elif str(e) == 'Chat not found':
                            context.bot.send_message(admin,
                                                     'Возникла ошибка:{}, msg:{} - сообщение исключено'
                                                     .format(str(e), 'msg_id: ' + str(msg.id) + ', user_id:' + str(msg.to_user)))
                            Message.update(date_send=-1).where(Message.id == msg.id).execute()
            time.sleep(1)
    except Exception as e:
        for admin in ADMINS:
            try:
                context.bot.send_message(admin, 'Возникла ошибка, рассыльщик продолжит работу через минуту: ' + str(e))
            except Exception as e:
                if str(e) == 'Chat not found':
                    print('Chat not found: ' + str(e) + ', admin: ' + str(admin))
        time.sleep(60)


if __name__ == '__main__':
    updater = Updater(TOKEN, use_context=True, request_kwargs=REQUEST_KWARGS)
    dispatcher = updater.dispatcher
    context = CallbackContext(dispatcher)

    prc_sender = Thread(target=sender, args=(context,))
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
