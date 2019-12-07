# disable: InsecureRequestWarning: Unverified HTTPS request is being made.
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import requests

import sys
import traceback

import logging

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, RegexHandler
from telegram.error import BadRequest
from telegram.ext.callbackcontext import CallbackContext

from db_model import Account, Message, User, Properties, get_user_str, send_message_bot, get_prop_str, prop_abr, get_trunc_sysdate
import bot_prop
from emoji import emojize

from threading import Thread
import os

import datetime
import time
import re
import json
import ast
from utils import build_menu
from uuid import uuid1

type_user = ('user', 'junior', 'investor')


def prntb(vstr, filename='bot.log'):
    Outfile = open(filename, "a+", encoding='utf-8')
    Outfile.write(vstr + '\n')
    Outfile.close()


logging.basicConfig(filename='bot.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.ERROR)
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


def print_stat(acc_id: str, short=False) -> str:
    cnt_fail = 0
    cnt_fail_plus = 0
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
                            black_list_matches += 1
                            if bk1.get('sale_profit') != 0:
                                sale_profit = sale_profit + bk1.get('sale_profit')
                                if bk1.get('sale_profit') > 0:
                                    cnt_fail_plus += 1
                                else:
                                    cnt_fail += 1
                            elif bk2.get('sale_profit') != 0:
                                sale_profit = sale_profit + bk2.get('sale_profit')
                                if bk2.get('sale_profit') > 0:
                                    cnt_fail_plus += 1
                                else:
                                    cnt_fail += 1


                    elif not bet_skip:
                        cnt_fork_success += 1

                        sum_bet1, sum_bet2 = bk1.get('new_bet_sum'), bk2.get('new_bet_sum')
                        k1, k2 = bk1.get('new_bet_kof'), bk2.get('new_bet_kof')
                        if sum_bet1 and sum_bet2 and k1 and k2:
                            total_sum = sum_bet1 + sum_bet2
                            min_profit = min_profit + round(min((sum_bet1 * k1 - total_sum), (sum_bet2 * k2 - total_sum)))
                            max_profit = max_profit + round(max((sum_bet1 * k1 - total_sum), (sum_bet2 * k2 - total_sum)))

            res_str = ''
            res_str = res_str + 'Проставлено вилок: *' + str(cnt_fork_success) + '*\n'
            if not short:
                res_str = res_str + 'Кол-во минусовы выкупов: *' + str(cnt_fail) + '*\n'
                res_str = res_str + 'Кол-во плюсовых выкупов: *' + str(cnt_fail_plus) + '*\n'
                res_str = res_str + 'Профит от выкупов: *' + '{:,}'.format(round(sale_profit)).replace(',', ' ') + '*\n'
                res_str = res_str + 'Минимальный профит: *' + '{:,}'.format(round(min_profit)).replace(',', ' ') + '*\n'
                res_str = res_str + 'Максимальный профит: *' + '{:,}'.format(round(max_profit)).replace(',', ' ') + '*\n'
                res_str = res_str + 'Средний профит: *' + '{:,}'.format(round((max_profit + min_profit) / 2)).replace(',', ' ') + '*\n'
                res_str = res_str + '\n'
            res_str = res_str + '*Примерный доход: ' + '{:,}'.format(round((max_profit + min_profit) / 2) + round(sale_profit)).replace(',', ' ') + '*\n'

            return res_str.strip()

    except FileNotFoundError:
        return 'Нет данных'
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        err_str = str(e) + ' ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        prntb(str(err_str))
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

    type_exclude = ['mirror', 'proxi', 'account']

    try:
        if type_ in type_exclude:
            pass
        else:
            if type_ == 'int':
                type_ = int
            elif type_ == 'float':
                type_ = float
                val = val
            else:
                type_ = str

            val = type_(val)
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        err_str = str(e) + ' ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        prntb(str(err_str))
        err_str = 'Неверный тип значения, ожидается: {}'.format(str(type_))

    try:
        err_limits = check_limits(val, type_, min_, max_, access_list)
    except TypeError as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        err_str = str(e) + ' ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        prntb(str(err_str))

    if err_limits:
        err_str = err_str + '\n' + err_limits

    if 'proxi' in str(type_):
        if val.count(':') == 1 or (val.count(':') == 2 and val.count('@') == 1):
            pass
        else:
            err_str = 'Неверный формат прокси'
    if 'account' in str(type_):
        if val.count('/') != 1:
            err_str = 'Неверный формат аккаунта'
    if 'mirror' in str(type_):
        if val.count('.') != 1:
            err_str = 'Неверный формат зеркала, ожидается: fonbet-ХХХХХ.com'

    return err_str.strip()


def set_prop(update, context):
    prop_val = update.message.text
    prop_name = context.user_data.get('choice')
    # TODO
    if prop_name:
        for key, val in prop_abr.items():
            type_ = val.get('type', 'str')
            if val.get('abr') == prop_name:
                err_msg = check_type(prop_val, type_, val.get('min'), val.get('max'), val.get('access_list'))
                if err_msg != '':
                    update.message.reply_text(
                        text=err_msg + '\n\nДля провторной попытки, выберите аккаунт из /botlist и нажмите : ' + bot_prop.BTN_SETTINGS,
                        parse_mode=telegram.ParseMode.MARKDOWN
                    )
                # set prop
                else:
                    acc_id = context.user_data.get('acc_id')
                    if acc_id:

                        if 'proxi' in type_:
                            bk_name = type_.split(':')[1]
                            proxy_json = json.loads(Account.select().where(Account.id == acc_id).get().proxies.replace('`', '"'))
                            proxy_json[bk_name]['https'] = 'https://' + prop_val
                            proxy_json[bk_name]['http'] = 'http://' + prop_val
                            proxy_str = json.dumps(proxy_json).replace('"', '`')
                            Account.update(proxies=proxy_str).where((Account.id == acc_id)).execute()
                        elif 'account' in type_:
                            bk_name = type_.split(':')[1]
                            account_json = json.loads(Account.select().where(Account.id == acc_id).get().accounts.replace('`', '"'))

                            login = prop_val.split('/')[0].strip()
                            if re.match(r'^\d+$', login):
                                login = int(login)
                            else:
                                login = str(login)

                            account_json[bk_name]['login'] = login
                            prop_val = prop_val.split('/')[1].strip()
                            account_json[bk_name]['password'] = prop_val
                            account_str = json.dumps(account_json).replace('"', '`')
                            Account.update(accounts=account_str).where((Account.id == acc_id)).execute()
                        elif 'mirror' in type_:
                            bk_name = type_.split(':')[1]
                            account_json = json.loads(Account.select().where(Account.id == acc_id).get().accounts.replace('`', '"'))

                            prop_val = prop_val.strip().lower().replace('http://', '').replace('https://', '')
                            mirror = prop_val
                            account_json[bk_name]['mirror'] = mirror
                            account_str = json.dumps(account_json).replace('"', '`')
                            Account.update(accounts=account_str).where((Account.id == acc_id)).execute()

                        if Properties.select().where((Properties.acc_id == acc_id) & (Properties.key == key)).count() > 0:
                            Properties.update(val=prop_val).where((Properties.acc_id == acc_id) & (Properties.key == key)).execute()
                        else:
                            data = [(acc_id, key, prop_val), ]
                            Properties.insert_many(data, fields=[Properties.acc_id, Properties.key, Properties.val]).execute()

                        msg_main = str(acc_id) + ': Новое значение *' + prop_name + '*\nустановлено:\n' + Properties.select().where((Properties.acc_id == acc_id) & (Properties.key == key)).get().val

                        keyboard = []
                        keyboard.append([InlineKeyboardButton(text=bot_prop.BTN_SETTINGS, callback_data='pror_edit')])
                        keyboard.append([InlineKeyboardButton(text=bot_prop.BTN_BACK, callback_data=context.user_data.get('key'))])
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        update.message.reply_text(msg_main + '\n\nЕсли хотите задать еще настройки, нажмите : ', reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)

                        admin_list = User.select().where(User.role == 'admin')
                        for admin in admin_list:
                            if admin.id != update.message.chat.id:
                                context.bot.send_message(admin.id, msg_main, parse_mode=telegram.ParseMode.MARKDOWN)
        del context.user_data['choice']


def choose_prop(update, context):
    markup = ReplyKeyboardRemove()
    text = update.message.text
    v_key = ''
    proxy = ''
    account = ''
    for key, val in prop_abr.items():
        if val.get('abr') == text:
            v_key = key
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
            elif 'proxi:' in val.get('type'):
                proxy = val.get('type').split(':')[1]
                dop_indo = 'только https прокси формата user:password@ip:port или ip:port'
            elif 'account:' in val.get('type'):
                account = val.get('type').split(':')[1]
                dop_indo = 'логин и пароль через / (слеш) в формате: login/password'
    acc_id = context.user_data.get('acc_id')
    cur_val = 'auto'
    try:
        if proxy == '':
            cur_val = Properties.select().where((Properties.acc_id == acc_id) & (Properties.key == v_key)).get().val
        elif proxy:
            proxy_str = Account.select().where(Account.id == acc_id).get().proxies.replace('`', '"').replace('https://', '')
            prntb(proxy_str)
            cur_val = json.loads(proxy_str).get(proxy, 'Proxy not found').get('https', 'HTTPS Proxy not found')
        elif account:
            account_srt = Account.select().where(Account.id == acc_id).get().accounts.replace('`', '"').replace('https://', '')
            prntb(account_srt)
            account_json = json.loads(account_srt)
            cur_val = account_json.get(account, 'BK not found').get('login', 'login not found') + '/' + account_json.get(account, 'BK not found').get('password', 'password not found')
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        err_str = str(e) + ' ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        prntb(str(err_str))
    update.message.reply_text(
        text='*' + text + '*: ' + cur_val +
             '\n\n''*Ограничения по настройке*:\n' + dop_indo + '\n\n' + bot_prop.MSG_PUT_VAL,
        reply_markup=markup,
        parse_mode=telegram.ParseMode.MARKDOWN
    )
    context.user_data['choice'] = text


def start(update, context):
    try:
        msg = get_user_str(update.message.chat.id)
    except:
        msg = 'Ваш ID в тегерамм: ' + str(update.message.chat.id)
    update.message.reply_text(msg, parse_mode=telegram.ParseMode.MARKDOWN)


def add_day(update, context):
    user_sender = update.message.chat.id
    if User.select().where(User.id == user_sender).get().role == 'admin':
        try:
            comm = update.message.text

            c, acc_id, days = comm.split(' ')

            acc_info = Account.select().where(Account.id == acc_id).get()
            date_end = acc_info.date_end
            owner_user_id = acc_info.user_id

            if date_end:
                date_end_str = datetime.datetime.fromtimestamp(date_end).strftime('%d.%m.%Y')

                date_plus = 60 * 60 * 24 * int(days)
                date_end_new = date_end + date_plus

                Account.update(date_end=date_end_new).where((Account.id == acc_id)).execute()
                date_end_new_db = Account.select().where(Account.id == acc_id).get().date_end
                date_end_new_db_str = datetime.datetime.fromtimestamp(date_end_new_db).strftime('%d.%m.%Y')

                admin_list = User.select().where(User.role == 'admin')
                for admin in admin_list:
                    context.bot.send_message(admin.id, '{}: Аккаунт с датой окончания {}, изменен на {} дней, текущая дата окончания: {}'.format(acc_id, date_end_str, days, date_end_new_db_str))
                context.bot.send_message(owner_user_id, '{}: Аккаунт с датой окончания {}, изменен на {} дней, текущая дата окончания: {}'.format(acc_id, date_end_str, days, date_end_new_db_str))
            else:
                update.message.reply_text('Дата окончания у аккаунта №' + str(acc_id) + ' не обнаружена')
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            err_str = str(e) + ' ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
            prntb(str(err_str))
            context.bot.send_message(
                user_sender,
                'Для изменения дней аккаунта, нужно отправить команду в формате:\n*add_day acc_id days*,\nнапример *add_day 4 30*',
                parse_mode=telegram.ParseMode.MARKDOWN
            )


def add(update, context):
    global type_user
    user_sender = update.message.chat.id
    types = ('user', 'acc')

    if User.select().where(User.id == user_sender).get().role == 'admin':
        try:
            comm = update.message.text
            c, type_, id_, new_val = comm.split(' ')
            admin_list = User.select().where(User.role == 'admin')
            if type_ == 'user':
                email, phone, role = new_val.split(';')
                email = email.strip().lower()
                phone = phone.strip().lower()
                role = role.strip().lower()
                if role not in type_user:
                    raise ValueError('Role not found!')
                try:
                    user_info = User.select().where(User.id == id_).get()
                    if user_info:
                        for admin in admin_list:
                            context.bot.send_message(admin.id, '[{}](tg://user?id={}): Пользователь уже в базе!'.format(id_, id_), parse_mode=telegram.ParseMode.MARKDOWN)
                except Exception as e:
                    if 'instance matching query does not exist' in str(e):
                        User.create(id=id_, role=role, email=email, phone=phone)
                        for admin in admin_list:
                            context.bot.send_message(admin.id, '[{}](tg://user?id={}): Пользователь успешно добавлен!'.format(id_, id_), parse_mode=telegram.ParseMode.MARKDOWN)
                    else:
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        err_str = str(e) + ' ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                        prntb(str(err_str))
            elif type_ == 'acc':
                acc_copy, fbu, fbp, olu, olp, proxy = new_val.split(';')

                if not re.match(r'^\d+$', fbu):
                    raise ValueError('Логин фонбет, пока только цифры')
                if proxy.count(':') == 1 or (proxy.count(':') == 2 and proxy.count('@') == 1):
                    pass
                else:
                    raise ValueError('Неверный формат прокси')

                proxies = '{`fonbet`:{`http`:`http://' + proxy + '`,`https`:`https://' + proxy + '`},`olimp`:{`http`:`http://' + proxy + '`,`https`:`https://' + proxy + '`}}'
                accounts = '{`olimp`:{`login`:`' + olu + '`,`password`:`' + olp + '`,`mirror`:`olimp.com`},`fonbet`:{`login`:' + fbu + ',`password`:`' + fbp + '`,`mirror`:``}}'
                try:
                    user_info = User.select().where(User.id == id_).get()
                    prop_new = Account.select().where(Account.id == acc_copy).get()
                    if user_info:
                        acc = Account.create(
                            user=id_,
                            key=uuid1(),
                            date_end=get_trunc_sysdate(30),
                            status='active',
                            proxies=proxies,
                            accounts=accounts
                        )

                        prop = (
                            Properties.insert_from(
                                Properties.select(acc.id, Properties.val, Properties.key).where(Properties.acc_id == acc_copy),
                                fields=[Properties.acc_id, Properties.val, Properties.key]
                            ).execute()
                        )
                        for admin in admin_list:
                            context.bot.send_message(admin.id, '{}: Аккаунт успешно добавлен!'.format(acc))
                except Exception as e:
                    if 'instance matching query does not exist' in str(e):
                        context.bot.send_message(user_sender, '{}: Пользователь не найден!'.format(id_))
                    else:
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        err_str = str(e) + ' ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                        prntb(str(err_str))
            else:
                raise ValueError('Type not found!')
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            err_str = str(e) + ' ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
            prntb(str(err_str))
            context.bot.send_message(
                user_sender,
                'Для добавления пользователя,\n' + \
                'нужно прислать команду:\n' + \
                '*add user telegtam_id email;phone;role*:\n' + \
                '\n' + \
                'Для добавления аккаунта пользователю,\n' + \
                'нужно прислать команду:\n' + \
                '*add acc user_id copy_acc;fbu;fbp;olu;olp;proxy*:\n' + \
                'proxy - указывать в формате login:pass@ip:port или ip:port\n'
                '\n' + \
                'Доступные значенения типов:\n' + ', '.join(map(str, types)),
                parse_mode=telegram.ParseMode.MARKDOWN
            )


def change(update, context):
    global type_user
    user_sender = update.message.chat.id
    types = ('user', 'acc', 'prop')
    type_acc = ('active', 'inactive', 'pause', 'deleted')

    if User.select().where(User.id == user_sender).get().role == 'admin':
        try:
            comm = update.message.text
            c, type_, id_, new_val = comm.split(' ')

            admin_list = User.select().where(User.role == 'admin')
            if type_ == 'user':
                try:
                    user_info = User.select().where(User.id == id_).get()
                    if user_info:
                        old_val = user_info.role
                        if new_val in type_user:
                            User.update(role=new_val).where((User.id == id_)).execute()

                            msg = '{}: Тип юзера сменен с {} на {}'.format(id_, old_val, new_val)
                            for admin in admin_list:
                                context.bot.send_message(admin.id, msg, parse_mode=telegram.ParseMode.MARKDOWN)
                        else:
                            context.bot.send_message(user_sender,
                                                     '{}: Вы пытаетесь сменить тип аккаунта, но значение {} - запрещено, доступно только: {}'.format(id_, type_, ', '.join(map(str, type_user))))
                except Exception as e:
                    if 'instance matching query does not exist' in str(e):
                        context.bot.send_message(user_sender, '{}: Пользователь не найден!'.format(id_))
                    else:
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        err_str = str(e) + ' ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                        prntb(str(err_str))
            elif type_ == 'acc':
                try:
                    acc_info = Account.select().where(Account.id == id_).get()
                    if acc_info:
                        old_val = acc_info.status
                        if new_val in type_acc:
                            Account.update(status=new_val).where((Account.id == id_)).execute()

                            msg = '{}: Тип аккаунта сменен с {} на {}'.format(id_, old_val, new_val)
                            for admin in admin_list:
                                context.bot.send_message(admin.id, msg, parse_mode=telegram.ParseMode.MARKDOWN)
                        else:
                            context.bot.send_message(user_sender,
                                                     '{}: Вы пытаетесь сменить тип аккаунта, но значение {} - запрещено, доступно только: {}'.format(id_, type_, ', '.join(map(str, type_acc))))
                except Exception as e:
                    if 'instance matching query does not exist' in str(e):
                        context.bot.send_message(user_sender, '{}: Аккаунт не найден!'.format(id_))
                    else:
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        err_str = str(e) + ' ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                        prntb(str(err_str))
            elif type_ == 'prop':
                try:
                    prop_new = Account.select().where(Account.id == new_val).get()
                    prop_old = Account.select().where(Account.id == id_).get()
                    if prop_new and prop_old:
                        Properties.delete().where((Properties.acc_id == id_)).execute()
                        source = (Properties.select(id_, Properties.key, Properties.val).where(Properties.acc_id == new_val))
                        Properties.insert_from(source, [Properties.acc_id, Properties.key, Properties.val]).execute()

                        msg = '{}: Настройки аккаунта скопированы с {}'.format(id_, new_val)
                        for admin in admin_list:
                            context.bot.send_message(admin.id, msg, parse_mode=telegram.ParseMode.MARKDOWN)
                except Exception as e:
                    if 'instance matching query does not exist' in str(e):
                        context.bot.send_message(user_sender, '{}: Аккаунт не найден!'.format(id_))
                    else:
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        err_str = str(e) + ' ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                        prntb(str(err_str))
            else:
                raise ValueError('Type not found!')
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            err_str = str(e) + ' ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
            prntb(str(err_str))
            context.bot.send_message(
                user_sender,
                'Для изменения дней аккаунта, нужно отправить команду в формате:\n' + \
                '*change type id new_val*, например:\n' + \
                'change user 5465456 junior или\n' + \
                'change acc 1 inactive или\n' + \
                'change prop 29 5 (копия с 5го на 29)\n' + \
                '\n' + \
                'Доступные значенения типов:\n' + ', '.join(map(str, types)) + '\n' + \
                'Доступные значенения для *user*:\n' + ', '.join(map(str, type_user)) + '\n' + \
                'Доступные значенения для *acc*:\n' + ', '.join(map(str, type_acc)) + '\n',
                parse_mode=telegram.ParseMode.MARKDOWN
            )


def help(update, context):
    user_sender = update.message.chat.id
    if User.select().where(User.id == user_sender).get().role == 'admin':
        context.bot.send_message(
            user_sender,
            'Справка по команадам админа:\n\n' + \
            '/add_day номер_аккаунта колво_дней\n\n' + \
            '/change тип:аккаунт/юзер/настройки ИД новое_значение\n\n'
            '/add acc ид_юзера копия_настроек;FB логин;FB пароль;O логин;O пароль;прокси\n\n'
        )


def get_time(update, context):
    update.message.reply_text('Time: ' + str(int(datetime.datetime.timestamp(datetime.datetime.now()))))


def get_acc_list(update, p_stat=''):
    acc_list = None
    user_id = update.message.chat.id

    if p_stat != '':
        list_visibly = ((Account.status == 'active') | (Account.status == 'inactive') | (Account.status == 'pause')) & (Account.work_stat == p_stat)
    else:
        list_visibly = (Account.status == 'active') | (Account.status == 'inactive') | (Account.status == 'pause')

    if user_id in bot_prop.ADMINS:
        acc_list = Account.select().where(list_visibly).order_by(Account.id)
    else:
        acc_list = Account.select().where((Account.user_id == user_id) & (list_visibly)).order_by(Account.id)
    return acc_list


def botlist(update, context, edit=False):
    keyboard = []
    work_stat = None
    date_end = None

    if edit:
        update = update.callback_query
    user = update.message.chat

    acc_list = get_acc_list(update)

    for acc in acc_list:
        work_stat_inactive = None
        date_end_str = ''
        if acc.date_end:
            date_end = datetime.datetime.fromtimestamp(acc.date_end)
            date_end_str = '[до ' + date_end.strftime('%d.%m.%Y') + ']'
            # check for date
            if date_end < datetime.datetime.now():
                work_stat_inactive = emojize(':x:', use_aliases=True) + ' Не активен' + ' ' + date_end_str
            elif acc.status == 'pause':
                work_stat_inactive = emojize(':double_vertical_bar:', use_aliases=True) + ' На паузе'
            elif acc.status == 'inactive':
                work_stat_inactive = emojize(':x:', use_aliases=True) + ' Не активен' + ' ' + date_end_str
        else:
            date_end_str = '[бессрочно]'

        if not work_stat_inactive:
            if acc.work_stat == 'start':
                work_stat = emojize(':arrow_forward:', use_aliases=True) + ' Работает ' + ' ' + date_end_str
            elif acc.work_stat == 'stop':
                work_stat = emojize(':stop_button:', use_aliases=True) + ' Остановлен ' + ' ' + date_end_str
        else:
            work_stat = work_stat_inactive

        ivest_list = User.select().where(User.role == 'investor')
        for invest in ivest_list:
            if str(acc.user_id) == str(invest.id):
                work_stat = work_stat + emojize(':dollar:', use_aliases=True)

        keyboard.append([InlineKeyboardButton(text=str(acc.id) + ': ' + work_stat, callback_data=acc.key)])

    keyboard.append([InlineKeyboardButton(text=emojize(':ambulance:', use_aliases=True) + ' Написать в тех. поддержку', url="t.me/autobro_sup")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    if not edit:
        update.message.reply_text(text=bot_prop.MSG_CHANGE_ACC, reply_markup=reply_markup)
    else:
        update.message.edit_text(text=bot_prop.MSG_CHANGE_ACC, reply_markup=reply_markup)


def list_split(ls: list, col=2):
    main = []
    cur_col = 1
    buff = []
    last_el = 0
    if len(ls) > col:
        for n, val in enumerate(ls):
            buff.append(val)
            cur_col += 1
            if cur_col == (col + 1):
                main.append(buff)
                cur_col = 1
                buff = []
                last_el = n
    else:
        main.append(ls)
    if last_el + 1 != len(ls) and len(ls) > col:
        main.append(ls[last_el + 1:len(ls)])
    return main


def botstat(update, context):
    keyboard = []
    acc_list = get_acc_list(update, 'start')
    if acc_list:
        for acc in acc_list:
            keyboard.append(InlineKeyboardButton(text=str(acc.id), callback_data='get_stat_short:' + str((acc.id))))
        keyboard = list_split(keyboard, 7)
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(text=bot_prop.MSG_CHANGE_ACC, reply_markup=reply_markup)
    else:
        update.message.reply_text(text=bot_prop.MSG_CHANGE_ACC_NONE)


def button(update, context):
    def prnt_acc_stat(user_role='junior'):
        keyboard = []
        if acc_info.get().work_stat == 'stop':
            start_stop = emojize(":arrow_forward:", use_aliases=True) + ' Запустить'
        else:
            start_stop = emojize(":stop_button:", use_aliases=True) + 'Остановить'

        keyboard.append([InlineKeyboardButton(text=start_stop, callback_data=query.data)])
        keyboard.append([InlineKeyboardButton(text=bot_prop.BTN_SETTINGS, callback_data='pror_edit')])
        if user_role in ('admin', 'investor'):
            keyboard.append([InlineKeyboardButton(text=bot_prop.BTN_GET_LOG, callback_data='get_log')])
        keyboard.append([InlineKeyboardButton(text=bot_prop.BTN_GET_STAT, callback_data='get_stat')])
        keyboard.append([InlineKeyboardButton(text=bot_prop.BTN_BACK, callback_data='botlist')])

        reply_markup = InlineKeyboardMarkup(keyboard)

        query.message.edit_text(
            text=bot_prop.MSG_START_STOP + ' [ID: ' + str(acc_info.get().id) + '@' + str(acc_info.get().user_id) + '](tg://user?id=' + str(acc_info.get().user_id) + ')\n' + get_prop_str(
                acc_info.get().id),
            reply_markup=reply_markup,
            parse_mode=telegram.ParseMode.MARKDOWN
        )

    query = update.callback_query

    is_admin = False
    user_id = update.callback_query.message.chat.id
    if user_id in bot_prop.ADMINS:
        is_admin = True
    user_role = User.select().where(User.id == user_id).get().role

    if query:
        if query.data == 'botlist':
            botlist(update, context, 'Edit')
        if query.data == 'pror_edit':
            acc_into = Account.select().where(Account.id == context.user_data.get('acc_id'))
            if acc_into.get().work_stat != 'stop' and acc_into.get().pid != 0:
                update.callback_query.answer(show_alert=True, text="Для настройки остановите аккаунт!")
            else:
                prop_btn = []

                for key, val in prop_abr.items():

                    abr = None
                    if user_role in ('admin', 'investor'):
                        abr = val.get('abr')
                    elif key not in ('TEST_OTH_SPORT', 'MAXBET_FACT'):
                        if user_role == 'junior':
                            if key in ('SUMM', 'WORK_HOUR_END', 'FONBET_MIRROR', 'FONBET_S', 'WORK_HOUR_END', 'SUMM', 'MAX_FORK'):
                                abr = val.get('abr')
                        else:
                            # if key not in ('FONBET_U', 'FONBET_P', 'OLIMP_U', 'OLIMP_P'):
                            abr = val.get('abr')

                    if abr:
                        prop_btn.append(abr)

                reply_keyboard = build_menu(prop_btn, n_cols=2, header_buttons=[bot_prop.BTN_CLOSE])
                markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
                query.message.reply_text(bot_prop.MSG_PROP_LIST, reply_markup=markup, )
        if query.data == 'get_stat':
            markup = ReplyKeyboardRemove()
            acc_id_str = str(context.user_data.get('acc_id'))
            query.message.reply_text(acc_id_str + ': ' + print_stat(acc_id_str), reply_markup=markup, parse_mode=telegram.ParseMode.MARKDOWN)
        elif 'get_log' in query.data:
            acc_id_str = str(context.user_data.get('acc_id'))
            file_stat_name = acc_id_str + '_to_cl.log'
            if os.path.isfile(file_stat_name):
                # send to tg
                with open(file_stat_name, 'r', encoding='utf-8') as f:
                    Message.insert({
                        Message.to_user: user_id,
                        Message.blob: f.read(),
                        Message.file_name: file_stat_name,
                        Message.file_type: 'document'
                    }).execute()
            else:
                query.message.reply_text(acc_id_str + ': Файл логов не найден', parse_mode=telegram.ParseMode.MARKDOWN)
        elif 'get_stat_short' in query.data:
            markup = ReplyKeyboardRemove()
            acc_id_str = query.data.split(':')[1]
            query.message.reply_text(acc_id_str + ': ' + print_stat(acc_id_str, 'short'), reply_markup=markup, parse_mode=telegram.ParseMode.MARKDOWN)

        acc_info = Account.select().where(Account.key == query.data)
        if acc_info:
            context.user_data['acc_id'] = acc_info.get().id
            context.user_data['key'] = acc_info.get().key
            # print(query.message.text)
            if bot_prop.MSG_START_STOP in query.message.text:
                if acc_info.get().work_stat == 'start':
                    send_message_bot(acc_info.get().user_id, str(acc_info.get().id) + ': ' + bot_prop.MSG_ACC_STOP_WAIT_EXT)
                    time.sleep(1)
                    Account.update(work_stat='stop').where(Account.key == query.data).execute()
                    update.callback_query.answer(text=bot_prop.MSG_ACC_STOP_WAIT)
                else:
                    if acc_info.get().date_end:
                        if datetime.datetime.fromtimestamp(acc_info.get().date_end) < datetime.datetime.now():
                            update.callback_query.answer(show_alert=True, text="Аккаунт не активен")
                        else:
                            Account.update(work_stat='start').where(Account.key == query.data).execute()
                            update.callback_query.answer(text=bot_prop.MSG_ACC_START_WAIT)
                    else:
                        Account.update(work_stat='start').where(Account.key == query.data).execute()
                        update.callback_query.answer(text=bot_prop.MSG_ACC_START_WAIT)
                prnt_acc_stat(user_role)
            elif query.message.text == bot_prop.MSG_CHANGE_ACC:
                if acc_info.get().date_end:
                    if datetime.datetime.fromtimestamp(acc_info.get().date_end) < datetime.datetime.now():
                        update.callback_query.answer(show_alert=True, text="Аккаунт не активен")
                    elif acc_info.get().status == 'active':
                        prnt_acc_stat(user_role)
                    else:
                        update.callback_query.answer(show_alert=True, text="Аккаунт не активен")
                elif acc_info.get().status == 'active':
                    prnt_acc_stat(user_role)
                else:
                    update.callback_query.answer(show_alert=True, text="Аккаунт не активен")
            else:
                prnt_acc_stat(user_role)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


#
#
# def error_callback(bot, update, error):
#     try:
#         raise error
#     # except Unauthorized:
#     #     # remove update.message.chat_id from conversation list
#     except BadRequest as e:
#         prntb('BadRequest: ' + str(e))
#         # handle malformed requests - read more below!
#     # except TimedOut:
#     #     # handle slow connection problems
#     # except NetworkError:
#     #     # handle other connection problems
#     # except ChatMigrated as e:
#     #     # the chat_id of a group has changed, use e.new_chat_id instead
#     # except TelegramError:
#     #     # handle all other telegram related errors


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
                        context.bot.send_message(msg.to_user, msg.text[0:4000].strip(), parse_mode=telegram.ParseMode.MARKDOWN)
                        Message.update(date_send=round(time.time())).where(Message.id == msg.id).execute()
                    except Exception as e:

                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        err_str = str(e) + ' ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                        prntb(str(err_str))

                        Message.update(date_send=-1).where(Message.id == msg.id).execute()
                        for admin in bot_prop.ADMINS:
                            try:
                                context.bot.send_message(admin, 'Возникла ошибка:{}, msg:{} - сообщение исключено'.format(str(e), 'msg_id: ' + str(msg.id) + ', user_id:' + str(msg.to_user)))
                            except Exception as e:
                                exc_type, exc_value, exc_traceback = sys.exc_info()
                                err_str = str(e) + ' ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                                prntb(str(err_str))
            except Exception as e:

                exc_type, exc_value, exc_traceback = sys.exc_info()
                err_str = str(e) + ' ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                prntb(str(err_str))

                Message.update(date_send=-1).where(Message.id == msg.id).execute()
                for admin in bot_prop.ADMINS:
                    try:
                        context.bot.send_message(admin, 'Возникла ошибка:{}, msg:{} - сообщение исключено'.format(str(e), 'msg_id: ' + str(msg.id) + ', user_id:' + str(msg.to_user)))
                    except Exception as e:
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        err_str = str(e) + ' ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                        prntb(str(err_str))
        time.sleep(1)


def close_prop(update, context):
    markup = ReplyKeyboardRemove()

    update.message.reply_text(text='Настройка завершена.', reply_markup=markup)


def matches(update, context):
    msg = ''
    cnt = []
    try:
        resp = requests.get('http://' + bot_prop.IP_SERVER + '/get_cnt_matches', timeout=5)
        cnt = ast.literal_eval(resp.text)
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        err_str = str(e) + ' ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        prntb(str(err_str))
        update.message.reply_text(text='Ошибка при запросе кол-ва матчей: ' + str(e))

    top = []
    try:
        resp_t = requests.get('http://' + bot_prop.IP_SERVER + '/get_cnt_top_matches', timeout=5)
        top = ast.literal_eval(resp_t.text)
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        err_str = str(e) + ' ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        prntb(str(err_str))
        update.message.reply_text(text='Ошибка при запросе кол-ва TOP матчей: ' + str(e))

    msg = 'Кол-во матчей: ' + str(len(cnt)) + ' \n'
    matches_dict = {}
    for match in cnt:
        match_type = match[2][0:1].upper() + match[2][1:]
        is_top = 1 if int(match[0]) in top or int(match[1]) in top else 0
        matches_dict[match_type] = {
            'cnt': matches_dict.get(match_type, {}).get('cnt', 0) + 1,
            'top': matches_dict.get(match_type, {}).get('top', 0) + is_top
        }

    for match_type, match_cnt in matches_dict.items():
        msg = msg + match_type + ': ' + str(match_cnt.get('cnt')) + ', top: ' + str(match_cnt.get('top')) + '\n'
    msg = msg.strip()

    update.message.reply_text(text=msg)


if __name__ == '__main__':
    updater = Updater(bot_prop.TOKEN, use_context=True, request_kwargs=bot_prop.REQUEST_KWARGS)
    dispatcher = updater.dispatcher
    context = CallbackContext(dispatcher)

    prc_sender = Thread(target=sender, args=(context,))
    prc_sender.start()

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('botlist', botlist))
    updater.dispatcher.add_handler(CommandHandler('matches', matches))
    updater.dispatcher.add_handler(CommandHandler('time', get_time))
    updater.dispatcher.add_handler(CommandHandler('botstat', botstat))
    updater.dispatcher.add_handler(CommandHandler('add_day', add_day))
    updater.dispatcher.add_handler(CommandHandler('change', change))
    updater.dispatcher.add_handler(CommandHandler('add', add))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    updater.dispatcher.add_handler(RegexHandler(patterns, choose_prop))
    updater.dispatcher.add_handler(RegexHandler('^(' + bot_prop.BTN_CLOSE + ')$', close_prop))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, set_prop))
    updater.dispatcher.add_handler(CommandHandler('help', help))
    # updater.dispatcher.add_error_handler(error_callback)

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()
