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

from db_model import Account, Message, User, Properties, get_user_str, send_message_bot, get_prop_str, prop_abr
import bot_prop
from emoji import emojize

from threading import Thread
import os

import datetime
import time
import re
import json

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


def print_stat(acc_id: str) -> str:
    cnt_fail = 0
    black_list_matches = 0
    cnt_fork_success = 0
    min_profit = 0
    max_profit = 0
    sale_profit = 0

    try:
        with open(acc_id + '_id_forks.txt', 'r') as f:
            for line in f:
                js = json.loads(line)
                for key, val in js.items():
                    bk1 = val.get('olimp')
                    bk2 = val.get('fonbet')
                    err_bk1, err_bk2 = bk1.get('err'), bk2.get('err')
                    bet_skip = False

                    if err_bk1 and err_bk2:
                        if 'BkOppBetError' in err_bk1 and 'BkOppBetError' in err_bk2:
                            bet_skip = True

                    if err_bk1 != 'ok' or err_bk2 != 'ok':
                        if not bet_skip:
                            cnt_fail += 1
                            black_list_matches += 1
                            sale_profit = sale_profit + bk1.get('sale_profit') + bk2.get('sale_profit')


                    elif not bet_skip:
                        cnt_fork_success += 1

                        sum_bet1, sum_bet2 = bk1.get('new_bet_sum'), bk2.get('new_bet_sum')
                        k1, k2 = bk1.get('new_bet_kof'), bk2.get('new_bet_kof')
                        if sum_bet1 and sum_bet2 and k1 and k2:
                            total_sum = sum_bet1 + sum_bet2
                            min_profit = min_profit + round(min((sum_bet1 * k1 - total_sum), (sum_bet2 * k2 - total_sum)))
                            max_profit = max_profit + round(max((sum_bet1 * k1 - total_sum), (sum_bet2 * k2 - total_sum)))

            res_str = ''
            res_str = res_str + 'Успешных ставок: *' + str(cnt_fork_success) + '*\n'
            if cnt_fail >= 0:
                res_str = res_str + 'Кол-во выкупов: *' + str(cnt_fail) + '*\n'
            if min_profit >= 0:
                res_str = res_str + 'Минимальный профит: *' + '{:,}'.format(round(min_profit)).replace(',', ' ') + '*\n'
            if max_profit >= 0:
                res_str = res_str + 'Максимальный профит: *' + '{:,}'.format(round(max_profit)).replace(',', ' ') + '*\n'
            if max_profit >= 0 and min_profit >= 0:
                res_str = res_str + 'Средний профит: *' + '{:,}'.format(round((max_profit + min_profit) / 2)).replace(',', ' ') + '*\n'
            if sale_profit >= 0:
                res_str = res_str + 'Профит от продаж: *' + '{:,}'.format(round(sale_profit)).replace(',', ' ') + '*\n'

            res_str = res_str + '\n*Примерный доход: ' + '{:,}'.format(round((max_profit + min_profit) / 2) + round(sale_profit)).replace(',', ' ') + '*\n'

            return res_str.strip()

    except FileNotFoundError:
        return 'Нет данных'
    except Exception as e:
        return 'Возникла ошибка: ' + str(e)


def check_limits(val, type_, min_, max_, access_list):
    err_str = ''
    if max_:
        max_ = type_(max_)

    if min_:
        min_ = type_(min_)

    if access_list:
        access_list = list(map(type_, access_list))

    if min_ and val < min_:
        err_str = 'Нарушены границы пределов, min: {}'.format(min_) + '\n'
    if max_ and val > max_:
        err_str = 'Нарушены границы пределов, max: {}'.format(max_) + '\n'

    if access_list:
        if val not in access_list:
            err_str = err_str + 'Недопустимое значение, резрешено: {}'.format(access_list)

    return err_str


def check_type(val: str, type_: str, min_: str, max_: str, access_list):
    err_str = ''
    err_limits = ''

    try:
        if type_ == 'int':
            type_ = int
        elif type_ == 'float':
            type_ = float
            val = val
        else:
            type_ = str
        val = type_(val)
    except Exception:
        err_str = 'Неверный тип значения, ожидается: {}'.format(str(type_))

    try:
        err_limits = check_limits(val, type_, min_, max_, access_list)
    except TypeError as e:
        print(e)

    if err_limits:
        err_str = err_str + '\n' + err_limits

    return err_str.strip()


def set_prop(update, context):
    prop_val = update.message.text
    prop_name = context.user_data.get('choice')
    # TODO
    if prop_name:
        for key, val in prop_abr.items():
            if val.get('abr') == prop_name:
                err_msg = check_type(prop_val, val.get('type'), val.get('min'), val.get('max'), val.get('access_list'))
                if err_msg != '':
                    update.message.reply_text(
                        text=err_msg + '\n\nДля провторной попытки, выберите аккаунт из /botlist и нажмите : ' + bot_prop.BTN_SETTINGS,
                        parse_mode=telegram.ParseMode.MARKDOWN
                    )
                # set prop
                else:
                    acc_id = context.user_data.get('acc_id')
                    if acc_id:
                        if Properties.select().where((Properties.acc_id == acc_id) & (Properties.key == key)).count() > 0:
                            Properties.update(val=prop_val).where((Properties.acc_id == acc_id) & (Properties.key == key)).execute()
                        else:
                            data = [(acc_id, key, prop_val), ]
                            Properties.insert_many(data, fields=[Properties.acc_id, Properties.key, Properties.val]).execute()
                        update.message.reply_text(
                            text='Новое значение *' + prop_name +
                                 '* установлено:\n' + Properties.select().where((Properties.acc_id == acc_id) & (Properties.key == key)).get().val + '\n\n' +
                                 'Если хотите задать еще настройки, выберите аккаунт из /botlist и нажмите : ' + bot_prop.BTN_SETTINGS,
                            parse_mode=telegram.ParseMode.MARKDOWN
                        )
        del context.user_data['choice']


def choose_prop(update, context):
    markup = ReplyKeyboardRemove()
    text = update.message.text
    for val in prop_abr.values():
        if val.get('abr') == text:
            str_r = ''
            if val.get('min'):
                str_r = str_r + 'min: ' + val.get('min')
            if val.get('min'):
                str_r = str_r + ', max: ' + val.get('max')
            dop_indo = str_r
            if val.get('access_list'):
                if dop_indo:
                    dop_indo + ', '
                dop_indo = 'допустимые значения: ' + str(val.get('access_list')).replace("'", '')

    update.message.reply_text(
        text='*' + text + '*\n\n''*Ограничения по настройке*:\n' + dop_indo + '\n\n' + bot_prop.MSG_PUT_VAL,
        reply_markup=markup,
        parse_mode=telegram.ParseMode.MARKDOWN
    )
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
    def prnt_acc_stat():
        keyboard = []
        if acc_info.get().work_stat == 'stop':
            start_stop = emojize(":arrow_forward:", use_aliases=True) + ' Запустить'
        else:
            start_stop = emojize(":stop_button:", use_aliases=True) + 'Остановить'

        keyboard.append([InlineKeyboardButton(text=start_stop, callback_data=query.data)])
        keyboard.append([InlineKeyboardButton(text=bot_prop.BTN_SETTINGS, callback_data='pror_edit')])
        # if acc_info.get().user_id in bot_prop.ADMINS:
        keyboard.append([InlineKeyboardButton(text=bot_prop.BTN_GET_STAT, callback_data='get_stat')])
        keyboard.append([InlineKeyboardButton(text=bot_prop.BTN_BACK, callback_data='botlist')])

        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.edit_text(
            text='*' + bot_prop.MSG_START_STOP + '\nID=' + str(acc_info.get().id) + '*\n' +
                 get_prop_str(acc_info.get().id),
            reply_markup=reply_markup,
            parse_mode=telegram.ParseMode.MARKDOWN
        )

    query = update.callback_query

    if query:
        if query.data == 'botlist':
            botlist(update, context, 'Edit')
        if query.data == 'pror_edit':
            acc_into = Account.select().where(Account.id == context.user_data.get('acc_id'))
            if acc_into.get().work_stat != 'stop' and acc_into.get().pid != 0:
                update.callback_query.answer(show_alert=True, text="Для настройки остановите аккаунт!")
            else:
                prop_btn = [[bot_prop.BTN_CLOSE]]
                for val in prop_abr.values():
                    abr = val.get('abr')
                    if abr:
                        prop_btn.append([abr])
                reply_keyboard = prop_btn
                markup = ReplyKeyboardMarkup(reply_keyboard)
                query.message.reply_text(bot_prop.MSG_PROP_LIST, reply_markup=markup)
        if query.data == 'get_stat':
            markup = ReplyKeyboardRemove()
            acc_id_str = str(context.user_data.get('acc_id'))
            query.message.reply_text(acc_id_str + ': ' + print_stat(acc_id_str), reply_markup=markup, parse_mode=telegram.ParseMode.MARKDOWN)

        acc_info = Account.select().where(Account.key == query.data)
        if acc_info:
            context.user_data['acc_id'] = acc_info.get().id
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
                        context.bot.send_message(msg.to_user, msg.text[0:4000], parse_mode=telegram.ParseMode.MARKDOWN)
                        Message.update(date_send=round(time.time())).where(Message.id == msg.id).execute()
                    except Exception as e:
                        Message.update(date_send=-1).where(Message.id == msg.id).execute()
                        for admin in bot_prop.ADMINS:
                            if str(e) == 'Chat not found':
                                try:
                                    context.bot.send_message(
                                        admin, 'Возникла ошибка:{}, msg:{} - сообщение исключено'.format(str(e), 'msg_id: ' + str(msg.id) + ', user_id:' + str(msg.to_user)))
                                except Exception as e:
                                    print(e)
            except Exception as e:
                Message.update(date_send=-1).where(Message.id == msg.id).execute()
                for admin in bot_prop.ADMINS:
                    if str(e) == 'Chat not found':
                        try:
                            context.bot.send_message(
                                admin, 'Возникла ошибка:{}, msg:{} - сообщение исключено'.format(str(e), 'msg_id: ' + str(msg.id) + ', user_id:' + str(msg.to_user)))
                        except Exception as e:
                            print(e)
        time.sleep(1)


def close_prop(update, context):
    markup = ReplyKeyboardRemove()
    update.message.reply_text(text='Настройка завершена.\n\nЕсли хотите задать еще настройки, выберите аккаунт из /botlist и нажмите : ' + bot_prop.BTN_SETTINGS, reply_markup=markup)


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
