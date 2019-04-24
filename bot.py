# disable: InsecureRequestWarning: Unverified HTTPS request is being made.
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import sys
import traceback

import logging

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, RegexHandler
from telegram.error import BadRequest
from telegram.ext.callbackcontext import CallbackContext

from db_model import Account, Message, User, get_user_str, send_message_bot, get_prop_str, prop_abr
import bot_prop
from emoji import emojize

from threading import Thread
import os

import datetime
import time
import re

logging.basicConfig(filename='bot.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

patterns = ''
for val in prop_abr.values():
    abr = re.escape(val.get('abr'))
    if abr:
        if patterns:
            patterns += '|' + abr
        else:
            patterns += '(' + abr
if patterns:
    patterns += ')'
    

def check_limits(val, type_, min_, max_, access_list):
    err_str = ''
    if max_:
        max_ = type_(max_)
            
    if min_:
        min_ = type_(min_)
        
    if access_list:
        access_list = list(map(type_, access_list))
        
    if val < min_ or val > max_:
        err_str = 'Нарушены границы пределов, min: {}, max: {}, вы указали: {}'.format(min_, max_, val) + '\n'
        
    if access_list:
        if val not in access_list:
            err_str = err_str + 'Недопустимое значение: {}, резрешено: {}'.format(val, access_list)
        
    return err_str

def check_type(val:str, type_:str, min_:str, max_:str, access_list):
    err_str = ''
    
    try:
        
        if type_ == 'int':
            type_ = int
        elif type_ == 'float':
            type_ = float
            
        val = type_(val)
    except Exception:
        err_str = 'Неверный тип значения, val:{}, type:{}'.format(val, type_)
       
    err_limits = check_limits(val, type_, min_, max_, access_list) 
    if err_limits:
        err_str = err_str + '\n' + err_limits
    
    return err_str.strip()
    


def set_prop(update, context):
    prop_val = update.message.text
    prop_name = context.user_data['choice']
    print(context.user_data, update.message.text)
    # TODO
    for val in prop_abr.values():
        print(val.get('abr'), prop_name)
        if val.get('abr') == prop_name:
            print('ok')
            err_msg = check_type(val, val.get('type'), val.get('min'), val.get('max'), val.get('access_list'))
            print('err_msg: ' + err_msg)
            if err_msg != '':
                print('send')
                markup = ReplyKeyboardMarkup()
                update.message.reply_text(text=err_msg, parse_mode=telegram.ParseMode.MARKDOWN)
                
            
    # set prop
    # clean context.user_data['choice']
    # send ms
    # upd # ? button(update, context)


def choose_prop(update, context):
    close_prop(update, context)

    markup = ReplyKeyboardRemove()
    text = update.message.text
    update.message.reply_text(text='Редактируется *' + text + '*\n' + bot_prop.MSG_PUT_VAL,
                              reply_markup=markup,
                              parse_mode=telegram.ParseMode.MARKDOWN)
    context.user_data['choice'] = text
    # TODO DISP ACCESS VALUE AND MAX MIN


def start(update, context):
    update.message.reply_text(get_user_str(update.message.chat.id), parse_mode=telegram.ParseMode.MARKDOWN)


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
        update.message.reply_text(text=bot_prop.MSG_CHANGE_ACC, reply_markup=reply_markup)
    else:
        update.message.edit_text(text=bot_prop.MSG_CHANGE_ACC, reply_markup=reply_markup)


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
        keyboard.append([InlineKeyboardButton(text=bot_prop.BTN_BACK, callback_data='botlist')])

        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.edit_text(text='*' + bot_prop.MSG_START_STOP + '*\n' + get_prop_str(acc_info.get().id),
                                reply_markup=reply_markup,
                                parse_mode=telegram.ParseMode.MARKDOWN)

    query = update.callback_query

    if query:
        if query.data == 'botlist':
            botlist(update, context, 'Edit')
        acc_info = Account.select().where(Account.key == query.data)
        if query.data == 'pror_edit':
            prop_btn = [[bot_prop.BTN_CLOSE]]
            for val in prop_abr.values():
                abr = val.get('abr')
                if abr:
                    prop_btn.append([abr])
            reply_keyboard = prop_btn
            markup = ReplyKeyboardMarkup(reply_keyboard)
            query.message.reply_text(bot_prop.MSG_PROP_LIST, reply_markup=markup)
        if acc_info:
            ACC_ACTIVE = acc_info.get().id
            context.user_data['acc_id'] = ACC_ACTIVE
            if bot_prop.MSG_START_STOP in query.message.text:
                if acc_info.get().work_stat == 'start':
                    Account.update(work_stat='stop').where(Account.key == query.data).execute()
                    update.callback_query.answer(text=bot_prop.MSG_ACC_STOP_WAIT)
                    send_message_bot(acc_info.get().user_id, str(acc_info.get().id) + ': ' + bot_prop.MSG_ACC_STOP_WAIT_EXT)
                else:
                    Account.update(work_stat='start').where(Account.key == query.data).execute()
                    update.callback_query.answer(text=bot_prop.MSG_ACC_START_WAIT)
                prnt_acc_stat()
            elif query.message.text == bot_prop.MSG_CHANGE_ACC:
                if acc_info.get().status == 'active':
                    prnt_acc_stat()
                else:
                    update.callback_query.answer(show_alert=True, text="Аккаунт не активен")


def help(update, context):
    update.message.reply_text("Use /start to run bot.")


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def error_callback(bot, update, error):
    try:
        raise error
    # except Unauthorized:
    #     # remove update.message.chat_id from conversation list
    except BadRequest as e:
        print('BadRequest: ' + str(e))
        # handle malformed requests - read more below!
    # except TimedOut:
    #     # handle slow connection problems
    # except NetworkError:
    #     # handle other connection problems
    # except ChatMigrated as e:
    #     # the chat_id of a group has changed, use e.new_chat_id instead
    # except TelegramError:
    #     # handle all other telegram related errors


def sender(context):
    while True:
        for msg in Message.select().where(Message.date_send.is_null()).order_by(Message.id):
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
                    try:
                        context.bot.send_message(msg.to_user, msg.text[0:4000])
                        Message.update(date_send=round(time.time())).where(Message.id == msg.id).execute()
                    except Exception as e:
                        Message.update(date_send=-1).where(Message.id == msg.id).execute()
                        for admin in bot_prop.ADMINS:
                            if str(e) == 'Chat not found':
                                try:
                                    context.bot.send_message(admin,
                                                             'Возникла ошибка:{}, msg:{} - сообщение исключено'
                                                             .format(str(e), 'msg_id: ' + str(msg.id) + ', user_id:' + str(msg.to_user)))
                                except Exception as e:
                                    print(e)
            except Exception as e:
                Message.update(date_send=-1).where(Message.id == msg.id).execute()
                for admin in bot_prop.ADMINS:
                    if str(e) == 'Chat not found':
                        try:
                            context.bot.send_message(admin,
                                                     'Возникла ошибка:{}, msg:{} - сообщение исключено'
                                                     .format(str(e), 'msg_id: ' + str(msg.id) + ', user_id:' + str(msg.to_user)))
                        except Exception as e:
                            print(e)
        time.sleep(1)


def close_prop(update, context):
    markup = ReplyKeyboardRemove()
    update.message.reply_text(text='Настройка завершена', reply_markup=markup)
    # ? button(update, context)


if __name__ == '__main__':
    updater = Updater(bot_prop.TOKEN, use_context=True, request_kwargs=bot_prop.REQUEST_KWARGS)
    dispatcher = updater.dispatcher
    context = CallbackContext(dispatcher)

    prc_sender = Thread(target=sender, args=(context,))
    prc_sender.start()

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('hello', send_text))
    updater.dispatcher.add_handler(CommandHandler('botlist', botlist))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    updater.dispatcher.add_handler(RegexHandler(patterns, choose_prop))
    updater.dispatcher.add_handler(RegexHandler('^(' + bot_prop.BTN_CLOSE + ')$', close_prop))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, set_prop))
    updater.dispatcher.add_handler(CommandHandler('help', help))
    updater.dispatcher.add_error_handler(error_callback)

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()
