# disable: InsecureRequestWarning: Unverified HTTPS request is being made.
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import sys
import traceback

import logging

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

from db_model import *
from bot_prop import *
from emoji import emojize

from multiprocessing import Process
import subprocess
import os

import json

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)


def start(update, context):
    update.message.reply_text(prnt_user_str(update.message.chat.id), parse_mode=telegram.ParseMode.MARKDOWN)
    
def botlist(update, context, edit=False):
    keyboard = []
    
    if edit:
        update = update.callback_query
    user = update.message.chat
    acc_list = Account.select().where(Account.user == user.id).order_by(Account.id)
    n = 1
    print(''.ljust(150, '-'))
    print(update)
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
        update.message.edit_reply_markup(text=MSG_CHANGE_ACC, reply_markup=reply_markup)


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
        query.message.edit_reply_markup(text = MSG_START_STOP, reply_markup = reply_markup)
    
    query = update.callback_query

    #query.edit_message_text(text="Selected option: {}".format(query.data))
    
    if query:
        if query.data == 'botlist':
            botlist(update, context, 'Edit')
        acc_info = Account.select().where(Account.key == query.data)
        if acc_info:
            if query.message.text == MSG_START_STOP:
                if acc_info.get().work_stat == 'start':
                    Account.update(work_stat='stop').where(Account.key == query.data).execute()
                    Account.update(work_stat='stop').where(Account.key == query.data).execute()
                else:
                    Account.update(work_stat='start').where(Account.key == query.data).execute()
                prnt_acc_stat()
            elif query.message.text == MSG_CHANGE_ACC:
                if acc_info.get().status == 'active':
                    prnt_acc_stat()
                else:
                    pass
                    #bot.answer_callback_query(call.id, show_alert=True, text="Аккаунт не активен")


def help(update, context):
    update.message.reply_text("Use /start to run bot.")


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TOKEN2, use_context=True, request_kwargs=REQUEST_KWARGS)

    updater.dispatcher.add_handler(CommandHandler('start', start))
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