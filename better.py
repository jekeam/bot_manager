# coding:utf-8
from bet_fonbet import *
from bet_olimp import *
import datetime
import time
from utils import prnt, get_account_info, get_prop, get_sum_bets, get_new_sum_bets, get_proxies, normalized_vector
import threading
from multiprocessing import Manager, Process
import time
from random import randint, uniform
import platform
from exceptions import FonbetBetError, OlimpBetError, Shutdown, MaxFail, MaxFork
import http.client
import json
import re
import sys
import traceback
import os
from db_model import db, send_message_bot, prop_abr
from bot_prop import ADMINS
import ml
import random
import subprocess
import pandas as pd

if __name__ == '__main__':
    from history import export_hist

global KEY, ACC_ID, START_SLEEP

shutdown = False
if get_prop('debug'):
    DEBUG = True
else:
    DEBUG = False


def bet_fonbet_cl(obj):
    global FONBET_USER
    try:
        fonbet = FonbetBot(FONBET_USER)
        fonbet.sign_in()
        fonbet.place_bet(obj)
        obj['fonbet_err'] = 'ok'
    except OlimpBetError:
        obj['fonbet_err'] = 'ok'
        obj['olimp_err'] = 'ok'
    except Exception as e:
        obj['fonbet_err'] = str(e)
    finally:
        obj['fonbet'] = fonbet


def bet_olimp_cl(obj):
    global OLIMP_USER
    try:
        olimp = OlimpBot(OLIMP_USER)
        olimp.sign_in()
        olimp.place_bet(obj)
        obj['olimp_err'] = 'ok'
    except FonbetBetError:
        obj['olimp_err'] = 'ok'
        obj['fonbet_err'] = 'ok'
    except Exception as e:
        obj['olimp_err'] = str(e)
    finally:
        obj['olimp'] = olimp


def check_l(L):
    global MIN_PROC, MAX_PROC, ACC_ID
    MIN_L = 1 - (MIN_PROC / 100)
    MAX_L = 1 - (MAX_PROC / 100)

    l_exclude_text = ''

    if L > MIN_L:
        l_exclude_text = l_exclude_text + 'Вилка ' + str(L) + ' (' + str(round((1 - L) * 100, 3)) + '%), беру вилки только >= ' + str(round((1 - MIN_L) * 100, 3)) + '%\n'
    if L < MAX_L:
        l_exclude_text = l_exclude_text + 'Вилка ' + str(L) + ' (' + str(round((1 - L) * 100, 3)) + '%), беру вилки только <= ' + str(round((1 - MAX_L) * 100, 3)) + '%\n'

    if l_exclude_text != '':
        return l_exclude_text
    else:
        return ''


def bet_type_is_work(key, event_type, group_limit_id=None):
    key = key.upper()
    olimp_bet_type = str(key.split('@')[-2])
    fonbet_bet_type = str(key.split('@')[-1])

    if event_type == 'tennis':
        # Чтобы брать другие исходы, например П1
        if 'ТБ' in key:
            if 'ТМ' in olimp_bet_type and 'ТБ' in fonbet_bet_type:
                return True
            else:
                return False
    # elif event_type == 'esports':
    #     return False

    if ('Ф1(' in key or 'Ф2(' in key) and get_prop('fora') == 'выкл':
        return False

    return True


def get_team_type(name_rus: str, name: str):
    if re.search('(u\d{2}|\(.*\d{2}\))', name_rus.lower()) or re.search('u\d{2}', name.lower()):
        return 'team_junior', 'rus: ' + str(name_rus) + ', en: ' + str(name)
    elif re.search('(\(жен\)|\(ж\))', name_rus.lower()) or re.search('\(w\)', name.lower()):
        return 'team_female', 'rus: ' + str(name_rus) + ', en: ' + str(name)
    elif re.search('(\s|-|\(\.)студ', name_rus.lower()) or re.search('(\s|-|\(\.)stud', name.lower()):
        return 'team_stud', 'rus: ' + str(name_rus) + ', en: ' + str(name)
    elif re.search('(\(р\)|\(рез\))', name_rus.lower()) or re.search('(\(r\)|\(res\)|\(reserves\))', name.lower()):
        return 'team_res', 'rus: ' + str(name_rus) + ', en: ' + str(name)
    else:
        return '', 'rus: ' + str(name_rus) + ', en: ' + str(name)


fork_exclude_list = []


def check_fork(key, L, k1, k2, live_fork, live_fork_total, bk1_score, bk2_score, event_type, minute, time_break_fonbet, period, team_type, team_names, curr_deff, level_liga, is_hot, info=''):
    global bal1, bal2, bet1, bet2, cnt_fork_success, black_list_matches, matchs_success, summ_min, fonbet_maxbet_fact, vect1, vect2, group_limit_id, place, max_deff, start_after_min
    global fork_exclude_list, vect_check_ok
    global USER_ID, ACC_ID, ADMINS, msg_by_fork

    fork_exclude_text = ''
    v = True

    place_prop = str(get_prop('place'))
    if place_prop != 'any':
        if place_prop != place:
            fork_exclude_text = fork_exclude_text + 'Вилка исключена т.к. тип матча (лайф/прематч) не определен, place_prop:{}, place_current:{}\n'.format(place_prop, place)
    if place == 'pre':
        if start_after_min / 60 > float(get_prop('place_time')):
            fork_exclude_text = fork_exclude_text + 'Вилка исключена т.к. матч будет через:{} ч, а в настройках не больше:{} ч.\n'.format(start_after_min / 60, get_prop('place_time'))

    if vect1 == vect2 or not vect1 or not vect2 or not vect_check_ok:
        fork_exclude_text = fork_exclude_text + 'Вилка исключена т.к. вектор движения не определен или сонаправлен, vect1:{}, vect2:{}, vect_check_ok:{}\n'.format(vect1, vect2, vect_check_ok)

    if get_prop('maxbet_fact', 'выкл') == 'вкл' and fonbet_maxbet_fact == 0:
        fork_exclude_text = fork_exclude_text + 'Вилка исключена т.к. нет значения fonbet_maxbet_fact\n'

    if get_prop('team_junior', 'выкл') == 'выкл':
        if team_type == 'team_junior':
            fork_exclude_text = fork_exclude_text + 'Вилка исключена по названию команд: ' + team_names + '\n'

    if get_prop('team_female', 'выкл') == 'выкл':
        if team_type == 'team_female':
            fork_exclude_text = fork_exclude_text + 'Вилка исключена по названию команд: ' + team_names + '\n'

    if get_prop('team_stud', 'выкл') == 'выкл':
        if team_type == 'team_stud':
            fork_exclude_text = fork_exclude_text + 'Вилка исключена по названию команд: ' + team_names + '\n'

    if get_prop('team_res', 'выкл') == 'выкл':
        if team_type == 'team_res':
            fork_exclude_text = fork_exclude_text + 'Вилка исключена по названию команд: ' + team_names + '\n'

    if not bet_type_is_work(key, event_type, group_limit_id):
        fork_exclude_text = fork_exclude_text + 'Вилка исключена, т.к. я еще не умею работать с этой ставкой: ' + str(key) + ', event_type: ' + str(event_type) + ', group_limit_id: ' + str(group_limit_id) + '\n'

    if curr_deff > max_deff:
        fork_exclude_text = fork_exclude_text + 'Вилка исключена, т.к. deff_max (' + str(curr_deff) + ' > ' + str(max_deff) + ')\n'

    if get_prop('double_bet', 'выкл') == 'выкл':
        if cnt_fork_success.count(key) > 0:
            fork_exclude_text = fork_exclude_text + 'Вилка не проставлена, т.к. уже проставляли на эту вилку: ' + key + '\n'

    if get_prop('one_bet', 'выкл') == 'вкл':
        if matchs_success.count(str(key.split('@')[0])) > 0 or matchs_success.count(str(key.split('@')[1])) > 0:
            fork_exclude_text = fork_exclude_text + 'Вилка не проставлена, т.к. уже ставили 1 вилку на данный матч: ' + str(matchs_success) + '\n'

    if black_list_matches.count(key) > 0:
        fork_exclude_text = fork_exclude_text + 'Вилка исключена, т.к. событие анесено в blacklist: ' + key + ', ' + str(black_list_matches) + '\n'

    # Проверяем корректная ли сумма
    if bet1 < 30 or bet2 < 30:
        msg_temp = 'Вилка ' + key + '  исключена, т.к сумма одной из ставок меньше 30р\n'
        if key not in msg_by_fork and fork_exclude_text == '':
            msg_by_fork.append(key)
            # send_message_bot(USER_ID, str(ACC_ID) + ': ' + msg_temp, ADMINS)
        fork_exclude_text = fork_exclude_text + msg_temp

    if (bet1 + bet2) < summ_min:
        msg_temp = 'Общая сумма ставки: {}, меньше нижнего предела: {}.\n'.format((bet1 + bet2), summ_min)
        if key not in msg_by_fork and fork_exclude_text == '':
            msg_by_fork.append(key)
            # send_message_bot(USER_ID, str(ACC_ID) + ': ' + msg_temp, ADMINS)
        fork_exclude_text = fork_exclude_text + msg_temp

    # Проверяем хватить денег для ставки
    if (bal1 < bet1) or (bal2 < bet2):
        msg_temp = 'Для проставления вилки ' + key + ' недостаточно средств, bal1=' + str(bal1) + ', bet1=' + str(bet1) + ', bal2=' + str(bal2) + ', bet2=' + str(bet2) + '\n'
        if key not in msg_by_fork and fork_exclude_text == '':
            msg_by_fork.append(key)
            # send_message_bot(USER_ID, str(ACC_ID) + ': ' + msg_temp, ADMINS)
        fork_exclude_text = fork_exclude_text + msg_temp

    if get_prop('max_kof'):
        max_kof = float(get_prop('max_kof'))
        if k1 > max_kof or k2 > max_kof:
            fork_exclude_text = fork_exclude_text + 'Вилка ' + key + ' исключена т.к. коэф-большой: ({}/{}) > {})\n'.format(k1, k2, max_kof)

    if get_prop('min_kof'):
        min_kof = float(get_prop('min_kof'))
        if k1 < min_kof or k2 < min_kof:
            fork_exclude_text = fork_exclude_text + 'Вилка ' + key + ' исключена т.к. коэф-маленький: ({}/{}) > {})\n'.format(k1, k2, min_kof)

    if bk1_score != bk2_score and place != 'pre':
        fork_exclude_text = fork_exclude_text + 'Вилка ' + key + ' исключена т.к. счет не совпадает: olimp(' + bk1_score + ') fonbet(' + bk2_score + ')\n'

    if event_type == 'football':
        # Больше 43 минуты и не идет перерыв и это 1 период
        if 43.0 < float(minute) and not time_break_fonbet and period == 1:
            fork_exclude_text = fork_exclude_text + 'Вилка ' + key + ' исключена т.к. идет ' + str(minute) + ' минута матча и это не перерыв / не 2-й период \n'

        if float(minute) > 88.0:
            fork_exclude_text = fork_exclude_text + 'Вилка ' + key + ' исключена т.к. идет ' + str(minute) + ' минута матча \n'

    # Вилка живет достаточно
    long_livers = int(get_prop('fork_life_time'))
    long_livers_max = int(get_prop('fork_life_time_max', 9999))
    if get_prop('fork_time_type', 'auto') in ('auto', 'текущее'):
        # if live_fork - deff_max < long_livers:
        if live_fork < long_livers:
            fork_exclude_text = fork_exclude_text + 'Вилка ' + key + ' исключена т.к. живет меньше ' + str(long_livers) + ' сек. \n'
        if live_fork > long_livers_max:
            fork_exclude_text = fork_exclude_text + 'Вилка ' + key + ' исключена т.к. живет больше ' + str(long_livers) + ' сек. \n'
    else:
        # if live_fork_total - deff_max < long_livers:
        if live_fork_total < long_livers:
            fork_exclude_text = fork_exclude_text + 'Вилка ' + key + ' исключена т.к. живет в общем меньше ' + str(long_livers) + ' сек. \n'
        if live_fork_total > long_livers_max:
            fork_exclude_text = fork_exclude_text + 'Вилка ' + key + ' исключена т.к. живет в общем больше ' + str(long_livers) + ' сек. \n'

    if get_prop('top') == 'top' and level_liga != 'top':
        fork_exclude_text = fork_exclude_text + 'Вилка исключена т.к. это не топ лига: ' + name_rus + '\n'
    elif get_prop('top') == 'middle' and level_liga not in ('top', 'middle'):
        fork_exclude_text = fork_exclude_text + 'Вилка исключена т.к. это шлак лига: ' + name_rus + '\n'

    if get_prop('hot', 'выкл') == 'вкл' and not is_hot:
        fork_exclude_text = fork_exclude_text + 'Вилка исключена т.к. это не популярная катировка: ' + key + '\n'

    pour_into = get_prop('pour_into', 'auto')
    if pour_into != 'auto':
        if pour_into == 'olimp' and k1 > k2:
            fork_exclude_text = fork_exclude_text + 'Вилка исключена т.к. задан перелив в {}, а коф-т менее вероятен: k_ol:{} > k_fb:{}\n'.format(pour_into, k1, k2)
        elif pour_into == 'fonbet' and k2 > k1:
            fork_exclude_text = fork_exclude_text + 'Вилка исключена т.к. задан перелив в {}, а коф-т менее вероятен: k_ol:{} < k_fb:{}\n'.format(pour_into, k1, k2)

    fork_exclude_text = fork_exclude_text + check_l(L)

    if fork_exclude_text != '':
        v = False
        if key not in fork_exclude_list:
            fork_exclude_list.append(key)
            prnt(vstr=info + '\n' + fork_exclude_text, hide='hide', to_cl=True, type_='fork')
    return v


def upd_last_fork_time(v_time: int = None):
    global last_fork_time
    if v_time:
        last_fork_time = v_time
    else:
        last_fork_time = int(time.time())


def set_statistics(key, err_bk1, err_bk2, fork_info=None, bk1_sale_profit=0, bk2_sale_profit=0):
    global cnt_fail, black_list_matches, cnt_fork_success, matchs_success
    bet_skip = False
    if err_bk1 and err_bk2:
        if 'BkOppBetError'.lower() in str(err_bk1).lower() + str(err_bk2).lower() and 'ttempt limit exceeded'.lower() not in str(err_bk1).lower() + str(err_bk2).lower():
            bet_skip = True
            if fork_info:
                fork_info['olimp']['err'] = 'Вилка была пропущена: ' + err_bk1
                fork_info['fonbet']['err'] = 'Вилка была пропущена: ' + err_bk2

    if err_bk1 != 'ok' or err_bk2 != 'ok':
        if not bet_skip:
            if bk1_sale_profit < 0 or bk2_sale_profit < 0:
                cnt_fail = cnt_fail + 1
            black_list_matches.append(key)
            # Добавим доп инфу о проставлении
            upd_last_fork_time()
    elif not bet_skip:
        cnt_fork_success.append(key)
        matchs_success.append(str(key.split('@')[0]))
        matchs_success.append(str(key.split('@')[1]))
        upd_last_fork_time()


def get_statistics():
    global cnt_fail, black_list_matches, cnt_fork_success

    prnt('Успешных ставок: ' + str(len(cnt_fork_success)))
    prnt('Кол-во ставок с ошибками/выкупом: ' + str(cnt_fail))
    prnt('Черный список матчей: ' + str(black_list_matches))


def check_statistics():
    global cnt_fail, cnt_fork_success

    max_fail = int(get_prop('max_fail'))
    if cnt_fail >= max_fail:
        msg_str = 'Кол-во выкупов больше допустимого (' + str(max_fail) + '), работа завершена.'
        raise MaxFail(msg_str)

    max_fork = int(get_prop('max_fork'))
    if len(cnt_fork_success) >= max_fork:
        msg_str = 'Кол-во успешно просталвенных вилок достигнуто (' + str(max_fork) + '), работа завершена.'
        raise MaxFork(msg_str)


def save_plt(folder, filename, plt):
    if not os.path.exists(folder):
        os.makedirs(folder)
    plt.savefig(os.path.join(folder, filename))


def go_bets(wag_ol, wag_fb, key, deff_max, vect1, vect2, sc1, sc2, created, event_type, l, l_fisrt, level_liga, fork_slice, cnt_act_acc, info_csv):
    global bal1, bal2, cnt_fail, cnt_fork_success, k1, k2, total_bet, bet1, bet2, OLIMP_USER, FONBET_USER, ACC_ID, summ_min
    global USER_ID, ACC_ID, ADMINS, msg_by_fork

    olimp_bet_type = str(key.split('@')[-2])
    fonbet_bet_type = str(key.split('@')[-1])
    # Проверяем ставили ли мы на этот матч, пока в ручную

    L = (1 / float(wag_ol['factor'])) + (1 / float(wag_fb['value']))
    cur_proc = round((1 - L) * 100, 2)

    if __name__ == '__main__':
        wait_sec = 0
        prnt('Wait sec: ' + str(wait_sec))
        real_wait = wait_sec + deff_max
        prnt('Real wait sec: ' + str(real_wait))

        time.sleep(wait_sec)

        fork_id = int(time.time())
        fork_info = {
            fork_id: {
                'olimp': {
                    'id': wag_ol['event'],
                    'kof': wag_ol['factor'],
                    'amount': bet1,
                    'reg_id': 0,
                    'bet_type': olimp_bet_type,
                    'balance': bal1,
                    'time_bet': 0,
                    'vector': vect1,
                    'new_bet_sum': 0,
                    'new_bet_kof': 0,
                    'sale_profit': 0,
                    'event_type': event_type,
                    'err': 'ok'
                },
                'fonbet': {
                    'id': wag_fb['event'],
                    'kof': wag_fb['value'],
                    'amount': bet2,
                    'reg_id': 0,
                    'bet_type': fonbet_bet_type,
                    'balance': bal2,
                    'time_bet': 0,
                    'bet_delay': 0,
                    'vector': vect2,
                    'new_bet_sum': 0,
                    'new_bet_kof': 0,
                    'sale_profit': 0,
                    'event_type': event_type,
                    'err': 'ok'
                },
            }
        }

        if DEBUG:
            pass
            # bet1 = 30
            # bet2 = 30
        # return False

        x = wag_fb.get('hist', {}).get('avg_change')
        y = wag_fb.get('hist', {}).get('order')
        x2 = wag_ol.get('hist', {}).get('avg_change')
        y2 = wag_ol.get('hist', {}).get('order')

        if get_prop('ml_noise') == 'вкл':
            if vect1 == 'UP':
                x_ml = x2
                y_ml = y2
            elif vect2 == 'UP':
                x_ml = x
                y_ml = y
            vect = ''
            try:
                if sum(x_ml) > 2:
                    prnt('x_ml({}): {}'.format(type(x_ml), x_ml))
                    prnt('y_ml({}): {}'.format(type(y_ml), y_ml))
                    data = pd.DataFrame.from_dict({'sec': [x_ml], 'val': [y_ml], })
                    data = data[(data.val != '') & (data.val != '[]') & (data.sec != '') & (data.sec != '[]')]
                    # отсеиваю ряды у которых длина значений не равна кол-ву временных интервалов
                    data = data[data.val.apply(len) == data.sec.apply(len)]
                    # отсеиваю ряды у которых длина значений и временных интервалов 1, т.к. они статичные
                    data = data[data.val.apply(len) > 1]
                    data = data.reset_index(drop=True)
                    parts_gradient, plt = ml.preprocessing(
                        data.sec[0],
                        data.val[0],
                        True
                    )
                    # parts_gradient ['UP', 18, 0.0675, 22.22] / (vect, sec, speed(if > 0.02 - fast), quality (if > 80 - ok))
                    prnt('get parts_gradient: ' + str(parts_gradient))
                    if type(parts_gradient[0]) is str:
                        vect = str(parts_gradient[0])
                        sec = str(parts_gradient[1])
                        speed = str(parts_gradient[2])
                        quality = str(parts_gradient[3])
                    else:
                        vect = str(parts_gradient[-1][0])
                        sec = str(parts_gradient[-1][1])
                        speed = str(parts_gradient[-1][2])
                        quality = str(parts_gradient[-1][3])
                    prnt('ml get data: vect:{}, sec:{}, speed:{}, quality:{}'.format(vect, sec, speed, quality))
                    err_msg = ''
                    if vect:
                        if vect.lower() != 'up'.lower():
                            err_msg = err_msg + 'вектор не UP\n'
                    if sec:
                        if int(sec) < 300:
                            err_msg = err_msg + 'Данных меньше 300 сек.\n'
                    if speed:
                        if float(speed) < 0.02:
                            err_msg = err_msg + 'Скорость меньше 0.02\n'
                    if quality:
                        if float(quality) < 0.80:
                            err_msg = err_msg + 'Качество меньше 80%\n'
                    if err_msg:
                        prnt('Проверка на ML не пройдена т.к:\n' + err_msg)
                        # buf = ml.save_to_mem(plt)
                        return False
                    # else:
                    # str(ACC_ID) + '/' + datetime.datetime.now().strftime('%d.%m.%Y'),
                    # str(fork_id)
                    # peremennie errors
                    # if type(parts_gradient) is str:
                    #    ml.save_plt(acc_id + '/' + parts_gradient.lower(), fork_id, plt)
                    # else:
                    # ml.save_plt(acc_id + '/' + 'slices', fork_id, plt)
                    # переопределение векторов. тут внимательно они перепутаны местами фб и олимп
                else:
                    prnt('Проверка на ML не пройдена т.к. кол-ва сек. недостаточно: ' + str(x_ml))
                    return False
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                err_str = str(e) + ' ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                prnt('Проверка на ML не пройдена т.к. возникла ошибка: ' + str(err_str))
                return False

        shared = dict()

        shared['olimp'] = {
            'acc_id': ACC_ID,
            'opposite': 'fonbet',
            'created': created,
            'amount': bet1,
            'wager': wag_ol,
            'bet_type': olimp_bet_type,
            'vect': vect1,
            'sc1': sc1,
            'sc2': sc2,
            'cur_total': sc1 + sc2,
            'side_team': '1',
            'event_type': event_type,
            'summ_min': summ_min,
            'round': int(get_prop('round_fork')),
            'place': info_csv['place'],
        }
        shared['fonbet'] = {
            'acc_id': ACC_ID,
            'opposite': 'olimp',
            'created': created,
            'amount': bet2,
            'wager': wag_fb,
            'bet_type': fonbet_bet_type,
            'vect': vect2,
            'sc1': sc1,
            'sc2': sc2,
            'cur_total': sc1 + sc2,
            'side_team': '2',
            'max_bet': 0,
            'event_type': event_type,
            'key': key,
            'summ_min': summ_min,
            'round': int(get_prop('round_fork')),
            'place': info_csv['place'],
        }
        if '(' in fonbet_bet_type:
            shared['olimp']['bet_total'] = float(re.findall(r'\((.*)\)', fonbet_bet_type)[0])
            shared['fonbet']['bet_total'] = float(re.findall(r'\((.*)\)', fonbet_bet_type)[0])

        for bk_name, val in shared.items():
            prnt('BK ' + str(bk_name) +
                 ': bet_total:{}, cur_total:{}, sc1:{}, sc2:{}, vect:{} ({})'.format(
                     val.get('bet_total', ''), val.get('cur_total', ''),
                     val.get('sc1', ''), val.get('sc2', ''),
                     val.get('vect', ''), val.get('wager', '')))

        from bet_manager import run_bets
        run_bets(shared)

        prnt('shared: ' + str(shared), 'hide')

        bal1_new = shared['olimp'].get('balance', bal1)
        bal2_new = shared['fonbet'].get('balance', bal2)
        if bal1_new:
            bal1 = round(bal1_new)
        if bal2_new:
            bal2 = round(bal2_new)

        fork_info[fork_id]['olimp']['balance'] = bal1_new
        fork_info[fork_id]['fonbet']['balance'] = bal2_new

        fork_info[fork_id]['olimp']['time_bet'] = shared['olimp'].get('time_bet')
        fork_info[fork_id]['fonbet']['time_bet'] = shared['fonbet'].get('time_bet')
        fork_info[fork_id]['fonbet']['bet_delay'] = shared['fonbet'].get('bet_delay')
        fork_info[fork_id]['fonbet']['l'] = l
        fork_info[fork_id]['fonbet']['l_fisrt'] = l_fisrt

        fork_info[fork_id]['olimp']['new_bet_sum'] = shared['olimp'].get('new_bet_sum')
        fork_info[fork_id]['fonbet']['new_bet_sum'] = shared['fonbet'].get('new_bet_sum')

        fork_info[fork_id]['olimp']['new_bet_kof'] = shared['olimp'].get('new_bet_kof')
        fork_info[fork_id]['fonbet']['new_bet_kof'] = shared['fonbet'].get('new_bet_kof')

        fork_info[fork_id]['olimp']['sale_profit'] = shared['olimp'].get('sale_profit')
        fork_info[fork_id]['fonbet']['sale_profit'] = shared['fonbet'].get('sale_profit')

        fork_info[fork_id]['olimp']['reg_id'] = shared['olimp'].get('reg_id')
        fork_info[fork_id]['fonbet']['reg_id'] = shared['fonbet'].get('reg_id')

        fork_info[fork_id]['olimp']['err'] = str(shared.get('olimp_err', 'ok'))
        fork_info[fork_id]['fonbet']['err'] = str(shared.get('fonbet_err', 'ok'))

        fork_info[fork_id]['fonbet']['order_bet'] = str(shared.get('order_bet', ''))
        fork_info[fork_id]['fonbet']['max_bet'] = shared['fonbet'].get('max_bet')
        fork_info[fork_id]['fonbet']['maxbet_fact'] = info_csv.get('maxbet_fact')
        fork_info[fork_id]['fonbet']['fonbet_maxbet_fact'] = info_csv.get('fonbet_maxbet_fact', '')
        fork_info[fork_id]['fonbet']['first_bet_in'] = info_csv.get('first_bet_in', '')
        fork_info[fork_id]['fonbet']['total_first'] = info_csv.get('total_first', '')

        fork_info[fork_id]['fonbet']['is_top'] = level_liga
        fork_info[fork_id]['fonbet']['is_hot'] = wag_fb.get('is_hot')
        fork_info[fork_id]['fonbet']['fork_slice'] = fork_slice
        fork_info[fork_id]['fonbet']['cnt_act_acc'] = cnt_act_acc

        fork_info[fork_id]['fonbet']['fork_time_type'] = get_prop('fork_time_type', 'auto')
        fork_info[fork_id]['fonbet']['fork_life_time'] = get_prop('fork_life_time', 0)
        fork_info[fork_id]['fonbet']['fork_life_time_max'] = get_prop('fork_life_time_max', 9999)
        fork_info[fork_id]['fonbet']['min_proc'] = get_prop('min_proc', 0)
        fork_info[fork_id]['fonbet']['max_proc'] = get_prop('max_proc', 20)

        fork_info[fork_id]['fonbet']['user_id'] = info_csv.get('user_id', '')
        fork_info[fork_id]['fonbet']['fb_bk_type'] = info_csv.get('fb_bk_type', 'com')
        fork_info[fork_id]['fonbet']['group_limit_id'] = info_csv.get('group_limit_id', '')
        fork_info[fork_id]['fonbet']['live_fork'] = info_csv.get('live_fork', '')
        fork_info[fork_id]['fonbet']['team_type'] = info_csv.get('team_type', '')
        fork_info[fork_id]['fonbet']['summ_min'] = info_csv.get('summ_min', '')
        fork_info[fork_id]['fonbet']['place'] = info_csv.get('place', '')

        fork_info[fork_id]['fonbet']['avg_change'] = str(x)
        fork_info[fork_id]['fonbet']['order_kof'] = str(y)

        fork_info[fork_id]['olimp']['avg_change'] = str(x2)
        fork_info[fork_id]['olimp']['order_kof'] = str(y2)

        # CHECK FATAL ERROR
        if shared.get('fonbet_err_fatal') or shared.get('olimp_err_fatal'):
            msg_str = 'Обнаружена фатальная ошибка: ' + str(shared.get('fonbet_err_fatal')) + str(shared.get('olimp_err_fatal')) + ', проверьте счет на порезку, блокировку ставки и вывода средств!'
            raise MaxFail(msg_str)

        # CALC/SET STATISTICS
        set_statistics(
            key,
            shared.get('olimp_err'),
            shared.get('fonbet_err'),
            fork_info[fork_id],
            shared['olimp'].get('sale_profit', 0),
            shared['fonbet'].get('sale_profit', 0)
        )
        get_statistics()
        msg_errs = ' ' + shared.get('olimp_err') + shared.get('fonbet_err')
        # if 'шибка баланса' in msg_errs:
        #     if key not in msg_by_fork:
        #         msg_by_fork.append(key)
        #         try:
        #             re.findall(r'(^\d+:  BkOppBetError: Ошибка: BetIsLost - Ошибка баланса:\s)(.*)(Traceback .*)', msg_errs)[0][1]
        #             send_message_bot(USER_ID, str(ACC_ID) + ': ' + msg_errs + ' - вилка ' + key + ' исключена', ADMINS)
        #         except Exception as e:
        #             prnt('Error 582: ' + str(e))
        if not 'BkOppBetError'.lower() in msg_errs.lower():
            if get_prop('ml_noise') == 'вкл' and vect and plt:
                ml.save_plt(
                    str(ACC_ID) + '/' + datetime.datetime.now().strftime('%d.%m.%Y') + '/' + str(vect).lower(),
                    str(fork_id),
                    plt
                )
            # SAVE INFO
            save_fork(fork_info)
            # WAITING AFTER BET
            sleep_post_work = int(get_prop('timeout_fork', 30))
            prnt(vstr='Ожидание ' + str(sleep_post_work) + ' сек.', hide=None, to_cl=True)
            time.sleep(sleep_post_work)
            # GET NEW BALANCE
            bal1 = OlimpBot(OLIMP_USER).get_balance()  # Баланс в БК1
            bal2 = FonbetBot(FONBET_USER).get_balance()  # Баланс в БК2
        # CHECK FAILS
        check_statistics()
        return True


time_out_cnt = 0
connection_error_cnt = 0
send_msg = False


def run_client():
    global server_forks
    global shutdown
    global server_ip

    global ADMINS
    global ACC_ID

    global time_out_cnt
    global send_msg
    global connection_error_cnt

    long_pool_wait = randint(5, 60)
    prnt('Long pool sec: ' + str(long_pool_wait))

    try:
        conn = http.client.HTTPConnection(server_ip, 8888, timeout=long_pool_wait)

        while True:
            if shutdown:
                err_str = 'Основной поток завершен и run_client тоже.'
                conn.close()
                raise Shutdown(err_str)

            # prnt('Get /get_forks', hide=True)
            # prnt('Get /get_forks')

            conn.request('GET', '/get_forks')
            rs = conn.getresponse()
            data = rs.read().decode('utf-8')
            data_json = json.loads(data)
            server_forks = data_json

            # prnt('End /get_forks', hide=True)
            # prnt('End /get_forks, len: ' + str(len(data_json)) + '\n' + str(data_json))

            # if str(ACC_ID) == '72':
            #     raise ValueError('ConnectionRefusedError')

            time.sleep(1)
            if time_out_cnt > 0 or connection_error_cnt > 0:
                prnt('run_client: ok ')
                time_out_cnt = 0
                connection_error_cnt = 0
    except Shutdown as e:
        prnt(str(e.__class__.__name__) + ' - ' + str(e))
        raise Shutdown(e)
    except Exception as e:
        msg_err = 'run_client: ' + str(e.__class__.__name__) + ' - ' + str(e)
        prnt(str(e.__class__.__name__) + ' - ' + msg_err)
        server_forks = {}
        conn.close()

        if ('timeout'.lower() in msg_err.lower() or 'timed out'.lower() in msg_err.lower()) and not send_msg:
            time_out_cnt = time_out_cnt + 1
            if time_out_cnt > randint(10, 20):
                subprocess.call('systemctl restart scan.service', shell=True)
                for admin in ADMINS:
                    msg_err = str(ACC_ID) + ': Возникла ошибка при запросе катировок со сканнера, сканнер перезапущен автоматически, без обновления прокси ' + str(msg_err)
                    # msg_err = str(ACC_ID) + ': Возникла ошибка таймаута, при запросе катировок со сканнера, просьба проверить ' + str(msg_err)
                    send_message_bot(admin, msg_err.replace('_', '\\_'))
                send_msg = True
        elif 'ConnectionRefusedError'.lower() in msg_err.lower() and not send_msg:
            connection_error_cnt = connection_error_cnt + 1
            if connection_error_cnt > randint(10, 20):
                subprocess.call('systemctl stop scan.service', shell=True)
                time.sleep(60)
                subprocess.call('python3.6 proxy_push.py', shell=True, cwd='/home/scan/')
                subprocess.call('systemctl restart scan.service', shell=True)
                for admin in ADMINS:
                    msg_err = str(ACC_ID) + ': Возникла ошибка при запросе катировок со сканнера, прокси запушены и сканнер перезапущен автоматически, ' + str(msg_err)
                    # msg_err = str(ACC_ID) + ': Возникла ошибка соединения, при запросе катировок со сканнера, просьба проверить, ' + str(msg_err)
                    send_message_bot(admin, msg_err.replace('_', '\\_'))
                send_msg = True
        prnt('connection_error_cnt: {}, time_out_cnt: {}, send_msg: {}'.format(connection_error_cnt, time_out_cnt, send_msg))
        time.sleep(long_pool_wait)
        return run_client()


def recalc_bets(hide=True):
    global k1, k2, total_bet, bal1, bet1, bet2, round_bet, fonbet_maxbet_fact
    # prnt('Get sum bets', hide, True, 'calc')
    # prnt('total_bet: {}, round_bet: {}, bal1:{}, bal2:{}, bet1:{},  bet2:{}'.format(total_bet, round_bet, bal1, bal2, bet1, bet2), hide, True, 'calc')
    bet1, bet2 = get_sum_bets(k1, k2, total_bet, round_bet, hide)
    if bet1 > bal1 or bet2 > bal2:
        if bal1 < bal2:
            # prnt('recalc bet (bal1 < bal2)', hide, True, 'calc')
            bet1, bet2 = get_new_sum_bets(k1, k2, bal1, bal2, hide, round_bet)
            total_bet = bet1 + bet2
        else:
            # prnt('recalc bet (bal1 > bal2)', hide, True, 'calc')
            bet2, bet1 = get_new_sum_bets(k2, k1, bal2, bal1, hide, round_bet)
            total_bet = bet1 + bet2

    max_bet_fonbet = int(get_prop('max_bet_fonbet', '0'))
    if get_prop('maxbet_fact', 'выкл') == 'вкл':
        if fonbet_maxbet_fact > 0:
            if bet2 > fonbet_maxbet_fact:
                # prnt('recalc bet (fonbet_maxbet_fact)', hide, True, 'calc')
                bet2, bet1 = get_new_sum_bets(k2, k1, max_bet_fonbet, bal1, hide, round_bet)
                total_bet = bet1 + bet2

    if bet2 > max_bet_fonbet > 0:
        # prnt('recalc bet (max_bet_fonbet)', hide, True, 'calc')
        bet2, bet1 = get_new_sum_bets(k2, k1, max_bet_fonbet, bal1, hide, round_bet)
        total_bet = bet1 + bet2


FONBET_USER = {'login': get_account_info('fonbet', 'login'), 'password': get_account_info('fonbet', 'password')}
OLIMP_USER = {'login': get_account_info('olimp', 'login'), 'password': get_account_info('olimp', 'password')}

bet1 = 0.  # Сумма ставки в БК1
bet2 = 0.  # Сумма ставки в БК2
total_bet = 0.  # Величина общей ставки;
betMax1 = 3000.  # Максимальная ставка в БК1 на данную позицию
betMax2 = 3000.  # Максимальная ставка в БК2 на данную позицию
betMin1 = 30.  # Минимальная ставка в БК1 на данную позицию
betMin2 = 30.  # Минимальная ставка в БК2 на данную позицию
pf1 = 0.  # Прибыль в БК1
pf2 = 0.  # Прибыль в БК2
pf = 0.  # минимальная прибыль;
bal1 = 0
bal2 = 0
N = 0  # счетчик (количество, проставленных вилок)
F = 0  # счетчик (количество, найденых вилок)
time_get_balance = datetime.datetime.now()
time_live = datetime.datetime.now()

cnt_fail = 0
black_list_matches = []
cnt_fork_success = []
matchs_success = []
msg_excule_pushed = []
printed = False
last_fork_time = 0
last_refresh_time = 0

cnt_fork_success_old = 0
cnt_fork_fail_old = 0
start_message_send = False

temp_lock_fork = {}

export_block = False

msg_str_old = ''
msg_str = ''
info_csv = {}
msg_by_fork = []

# sleeping_forks = []

cnt_acc_sql = "select count(*)\n" + \
              "from(\n" + \
              "  select\n" + \
              "    id,\n" + \
              "    sum(case when prop = 'MIN_PROC' and val <= :cur_proc then 1 else 0 end) as min_proc,\n" + \
              "    coalesce(sum(case when prop = 'MAX_PROC' and val >= :cur_proc then 1 else null end), 1) as max_proc,\n" + \
              "    sum(case when prop = 'FORK_LIFE_TIME' and val <= :live_fork then 1 else 0 end) as live_fork,\n" + \
              "    coalesce(sum(case when prop = 'FORK_LIFE_TIME_MAX' and val >= :live_fork then 1 else null end), 1) as live_fork_max,\n" + \
              "    sum(case when (prop = upper(':team_type') and val = 'ВКЛ') or ':team_type' = '' then 1 else 0 end) as team,\n" + \
              "    coalesce(sum(case when prop = 'TOP' and val = 'ВКЛ' and :is_top != 'True' then 0 else null end), 1) as top\n" + \
              "  from (\n" + \
              "    select a.id, upper(p.`key`) as prop, upper(p.val) as val\n" + \
              "    from properties p\n" + \
              "    join account a\n" + \
              "    on a.id = p.acc_id and\n" + \
              "	   a.work_stat = 'start' and\n" + \
              "	   status = 'active'\n" + \
              "  ) x\n" + \
              "where id != :acc_id\n" + \
              "  group by id\n" + \
              ") y\n" + \
              "where min_proc = 1\n" + \
              "  and max_proc = 1\n" + \
              "  and live_fork = 1\n" + \
              "  and live_fork_max = 1\n" + \
              "  and team >= 1\n" + \
              "  and top = 1;"


# wag_fb:{'event': '12797479', 'factor': '921', 'param': '', 'score': '0:0', 'value': '2.35'}
# wag_fb:{'apid': '1144260386:45874030:1:3:-9999:3:NULL:NULL:1', 'factor': '1.66', 'sport_id': 1, 'event': '45874030'}

def ref_bal_small(bal1, bal2):
    return (bal1 <= 400 or bal2 <= 400)


if __name__ == '__main__':
    try:

        random_time = uniform(0, 1)
        prnt('random_time: ' + str(random_time))
        time.sleep(random_time)
        prnt('current pid: ' + str(os.getpid()))

        wait_before_start_sec = 0
        if START_SLEEP != '':
            wait_before_start_sec = float(randint(1, 1200))
            Account.update(work_stat='start').where(Account.key == KEY).execute()
        send_message_bot(USER_ID, str(ACC_ID) + ': ' + 'Аккаунт запущен', ADMINS)
        prnt('начну работу через ' + str(round(wait_before_start_sec)) + ' сек...')

        while Account.select().where(Account.key == KEY).get().work_stat in ('start', 'start_sleep'):
            if wait_before_start_sec > 0:
                wait_before_start_sec = wait_before_start_sec - 0.5
                time.sleep(0.5)
            else:

                Account.update(pid=os.getpid(), time_start=round(time.time())).where(Account.key == KEY).execute()
                prnt('DEBUG: ' + str(DEBUG))

                time_get_balance = datetime.datetime.now()
                time_live = datetime.datetime.now()

                bk1 = OlimpBot(OLIMP_USER)
                bk2 = FonbetBot(FONBET_USER)

                bk1_name = bk1.get_bk_name()
                bk2_name = bk2.get_bk_name()

                bal1 = bk1.get_balance()  # Баланс в БК1
                bal2 = bk2.get_balance()  # Баланс в БК2
                total_bet = int(get_prop('summ'))
                summ_min = int(get_prop('summ_min', '0'))
                summ_min_stat = int(get_prop('summ_min', '0'))
                if summ_min >= total_bet:
                    err_msg = 'Минимальная общая ставка не должена быть больше или равена максимальному'
                    raise ValueError(err_msg)

                sport_list = get_prop('sport_list').replace(';;', ';').split(';')

                if not DEBUG:
                    server_ip = get_prop('server_ip')
                else:
                    server_ip = get_prop('server_ip_test')

                MIN_PROC = float(get_prop('min_proc', '0.0').replace(',', '.'))
                MAX_PROC = float(get_prop('max_proc', '20.0').replace(',', '.'))
                if MIN_PROC >= MAX_PROC:
                    err_msg = 'Минимальный процент вилки не должен быть больше или равен максимальному'
                    raise ValueError(err_msg)

                FORK_LIFE_TIME = float(get_prop('fork_life_time', '0.0').replace(',', '.'))
                FORK_LIFE_TIME_MAX = float(get_prop('fork_life_time_max', '9999.0').replace(',', '.'))
                if FORK_LIFE_TIME >= FORK_LIFE_TIME_MAX:
                    err_msg = 'Минимальный период времени жизни вилки не должен быть больше или равен максимальному'
                    raise ValueError(err_msg)

                prnt(' ')
                prnt('START_SLEEP: ' + str(START_SLEEP))
                prnt('Current Time: ' + str(datetime.datetime.now()))
                prnt('ID аккаунта: ' + str(ACC_ID))
                prnt('IP-адрес сервера: ' + server_ip + ':8888')
                prnt('Баланс в БК Олимп: ' + str(bal1))
                prnt('Баланс в БК Фонбет: ' + str(bal2))
                prnt('Блокировка вывода: ' + str(bk2.get_acc_info('pay')))
                prnt('Блокировка ставки: ' + str(bk2.get_acc_info('bet')))
                prnt('Блокировка продажи: ' + str(bk2.get_acc_info('sale')))
                group_limit_id = str(bk2.get_acc_info('group'))
                prnt('Группа лимита: ' + group_limit_id)
                prnt('Тип БК: ' + get_prop('fonbet_s', 'com'))

                prnt('Жесткость ставки 1 плеча: ' + get_prop('flex_bet1'))
                prnt('Жесткость ставки 2 плеча: ' + get_prop('flex_bet2'))

                prnt('Жесткость катировки 1 плеча: ' + get_prop('flex_kof2'))
                prnt('Жесткость катировки 2 плеча: ' + get_prop('flex_kof2'))

                prnt('Ставить на форы: ' + get_prop('fora'))
                prnt('Первая ставка в БК: ' + str(get_prop('first_bet_in')))
                prnt('Первая ставка на ТМ/ТБ: ' + str(get_prop('total_first')))

                get_round_fork = int(get_prop('round_fork'))
                if get_round_fork not in (1, 5, 10, 50, 100, 1000):
                    err_msg = 'Недопустимое округление ставки={}'.format(get_round_fork)
                    raise ValueError(err_msg)
                else:
                    prnt('Округление вилки и суммы ставки до: ' + str(get_round_fork))

                random_summ_proc = int(get_prop('random_summ_proc', '0'))
                if random_summ_proc:
                    if random_summ_proc > 30:
                        err_msg = 'Отклонение от общей суммы ставки не должно привышать 30%'
                        raise ValueError(err_msg)
                    else:
                        total_bet_min = int(total_bet - (total_bet * int(random_summ_proc) / 100))
                        total_bet_max = int(total_bet + (total_bet * int(random_summ_proc) / 100))
                        prnt('total_bet:{}, total_bet_min: {}, total_bet_max: {}'.format(total_bet, total_bet_min, total_bet_max))
                        if summ_min > total_bet_min:
                            total_bet_min = summ_min
                            prnt('recalc total_bet:{}, total_bet_min: {}, total_bet_max: {}'.format(total_bet, total_bet_min, total_bet_max))
                else:
                    total_bet_min = total_bet
                    total_bet_max = total_bet

                if not DEBUG and total_bet < summ_min_stat:
                    err_msg = 'Обшая сумма ставки должна превышать ' + str(summ_min_stat) + ' руб.'
                    raise ValueError(err_msg)

                acc_info = Account.select().where(Account.key == KEY)
                for prop in acc_info.get().properties:
                    k = prop_abr.get(prop.key)
                    if k:
                        prnt(k.get('abr', '') + ': ' + prop.val)
                prnt(' ')
                try:
                    with open(str(ACC_ID) + '_id_forks.txt') as f:
                        for line in f:
                            js = json.loads(line)
                            last_time_temp = 0
                            for key, val in js.items():
                                bet_key = str(val.get('olimp', {}).get('id')) + '@' + str(val.get('fonbet', {}).get('id')) + '@' + \
                                          val.get('olimp', {}).get('bet_type') + '@' + val.get('fonbet', {}).get('bet_type')
                                set_statistics(
                                    bet_key,
                                    val.get('olimp').get('err'),
                                    val.get('fonbet').get('err'),
                                    val.get('olimp').get('sale_profit', 0),
                                    val.get('fonbet').get('sale_profit', 0)
                                )

                                if int(key) > last_time_temp:
                                    last_time_temp = int(key)
                        get_statistics()
                        if last_time_temp:
                            upd_last_fork_time(last_time_temp)
                except Exception as e:
                    prnt(e)
                check_statistics()

                last_fork_time_min = (int(time.time()) - last_fork_time) / 60
                prnt('С момента поледней ставки прошло: ' + str(last_fork_time_min) + ' мин.')

                server_forks = dict()
                start_see_fork = threading.Thread(target=run_client)  # , args=(server_forks,))
                start_see_fork.start()

                while Account.select().where(Account.key == KEY).get().work_stat == 'start':

                    time_export = False
                    if get_prop('work_hour_end'):
                        if int(get_prop('work_hour_end')) == int(datetime.datetime.now().strftime('%H')):
                            time_export = True

                    if os.path.exists('./' + str(ACC_ID) + '_id_forks.txt'):
                        if export_block:
                            if not time_export:
                                prnt('Час выгрузки прошел, снимаю блокировку')
                                export_block = False
                        else:
                            if time_export:
                                msg_str = 'Время выгрузки: {} ч., начинаю выгрузку...'.format(get_prop('work_hour_end'))
                                raise Shutdown(msg_str)
                    else:
                        if not export_block:
                            prnt('Файл не найден, выставлена блокировка выгрузки на тек. час')
                            export_block = True

                    one_proc = (bal1 + bal2) / 100
                    bal_small = ref_bal_small(bal1, bal2)

                    msg_str = ''

                    if group_limit_id == '4' and not start_message_send:
                        msg_str = msg_str + 'Обнаружена порезка до 4й группы\n'
                        summ_min_stat = 60
                        summ_min = 60
                    elif bk2.get_acc_info('sale').lower() == 'да' and not start_message_send:
                        msg_str = msg_str + 'Обнаружена неявная порезка до 4й группы, т.к. есть блокировка выкупа ставки\n'

                    if not start_message_send:
                        cnt_fork_success_old = len(cnt_fork_success)
                        cnt_fork_fail_old = cnt_fail
                        msg_str_t = ''
                        if one_proc:
                            msg_str_t = str(ACC_ID) + ': Распределение балансов:\n' + bk1_name + ': ' + str(round(bal1 / one_proc)) + '%\n' + bk2_name + ': ' + str(round(bal2 / one_proc)) + '%\n'
                        if cnt_fork_success_old != 0:
                            msg_str_t = msg_str_t + 'Проставлено вилок: {}\n'.format(len(cnt_fork_success))
                        if cnt_fork_fail_old != 0:
                            msg_str_t = msg_str_t + 'Сделано минусовы выкупов: {}\n'.format(cnt_fail)
                        if msg_str_t:
                            send_message_bot(USER_ID, msg_str_t, ADMINS)
                            start_message_send = True

                    elif len(cnt_fork_success) != cnt_fork_success_old:
                        msg_str = msg_str + 'Проставлено вилок: {}->{}'.format(cnt_fork_success_old, len(cnt_fork_success)) + '\n'
                        msg_str = msg_str + 'Сделано минусовы выкупов: {}'.format(cnt_fail) + '\n'
                        cnt_fork_success_old = len(cnt_fork_success)
                    elif cnt_fork_fail_old != cnt_fail:
                        msg_str = msg_str + 'Проставлено вилок: {}'.format(len(cnt_fork_success)) + '\n'
                        msg_str = msg_str + 'Сделано минусовы выкупов: {}->{}'.format(cnt_fork_fail_old, cnt_fail) + '\n'
                        cnt_fork_fail_old = cnt_fail

                    msg_err = ''

                    if bal_small and not DEBUG:
                        last_fork_time_min = (int(time.time()) - last_fork_time) / 60
                        if last_fork_time_min >= 120:
                            bal1 = bk1.get_balance()
                            bal2 = bk2.get_balance()
                            bal_small = ref_bal_small(bal1, bal2)
                            if bal_small:
                                msg_err = msg_err + '\nаккаунт остановлен: денег в одной из БК не достаточно для работы, просьба выровнять балансы.\n' + bk1_name + ': ' + str(bal1) + '\n' + bk2_name + ': ' + str(bal2)
                        else:
                            if last_fork_time_min % 30 == 0:
                                time.sleep(61)
                                msg_bal = 'C момента последней ставки прошло {} мин. обновляю балансы ' + str(bal1) + '->{}, ' + str(bal2) + '->{}, дисбаланс:{}'
                                bal1 = bk1.get_balance()
                                bal2 = bk2.get_balance()
                                bal_small = ref_bal_small(bal1, bal2)
                                msg_bal = msg_bal.format(last_fork_time_min, bal1, bal2, bal_small)
                                prnt(msg_bal)
                                # send_message_bot(USER_ID, str(ACC_ID) + ': ' + msg_bal, ADMINS)

                    if bk2.get_acc_info('bet').lower() != 'Нет'.lower():
                        msg_err = msg_err + '\n' + 'обнаружена блокировка ставки в Фонбет, аккаунт остановлен!'

                    if bk2.get_acc_info('pay').lower() != 'Нет'.lower():
                        msg_err = msg_err + '\n' + 'обнаружена блокировка вывода, нужно пройти верификацию в Фонбет, аккаунт остановлен!'

                    if msg_str != msg_str_old:
                        msg_str_old = msg_str
                        if msg_str:
                            send_message_bot(USER_ID, str(ACC_ID) + ': ' + msg_str, ADMINS)

                    if msg_err != '':
                        prnt(msg_err.strip())
                        raise Shutdown(msg_err.strip())

                    if server_forks:
                        for key, val_json in sorted(server_forks.items(), key=lambda x: random.random()):
                            l = val_json.get('l', 0.0)
                            l_fisrt = val_json.get('l_fisrt', 0.0)
                            k1_type = key.split('@')[-2]
                            k2_type = key.split('@')[-1]

                            name = val_json.get('name', 'name')
                            name_rus = val_json.get('name_rus', 'name_rus')
                            pair_math = val_json.get('pair_math', 'pair_math')

                            bk1_score = str(val_json.get('bk1_score', 'bk1_score'))
                            bk2_score = str(val_json.get('bk2_score', 'bk2_score'))
                            score = '[' + bk1_score + '|' + bk2_score + ']'

                            sc1 = 0
                            sc2 = 0
                            try:
                                sc1 = int(bk2_score.split(':')[0])
                            except BaseException:
                                pass

                            try:
                                sc2 = int(bk2_score.split(':')[1])
                            except BaseException:
                                pass

                            v_time = val_json.get('time', 'v_time')
                            minute = val_json.get('minute', 0)
                            time_break_fonbet = val_json.get('time_break_fonbet')
                            level_liga = val_json.get('is_top')
                            period = val_json.get('period')
                            time_last_upd = val_json.get('time_last_upd', 1)
                            live_fork_total = val_json.get('live_fork_total', 0)
                            live_fork = val_json.get('live_fork', 0)
                            created_fork = val_json.get('created_fork', '')
                            event_type = val_json.get('event_type')
                            place = val_json.get('place')

                            prnt(' ', 'hide')
                            prnt('GET ' + place.upper() + ' FORK: ' + name + ', ' + key, 'end')

                            fonbet_maxbet_fact = val_json.get('fonbet_maxbet_fact', {}).get(str(group_limit_id), 0)

                            deff_olimp = round(float(time.time() - float(val_json.get('time_req_olimp', 0.0))))
                            deff_fonbet = round(float(time.time() - float(val_json.get('time_req_fonbet', 0.0))))
                            curr_deff = max(0, deff_olimp, deff_fonbet)

                            bk1_bet_json = val_json.get('kof_olimp', {})
                            bk2_bet_json = val_json.get('kof_fonbet', {})
                            start_after_min = val_json.get('start_after_min', 0)

                            bk1_hist = bk1_bet_json.get('hist', {})
                            bk2_hist = bk2_bet_json.get('hist', {})

                            base_line = bk2_bet_json.get('base_line', False)
                            is_hot = bk2_bet_json.get('is_hot', False)

                            bk1_avg_change = bk1_hist.get('avg_change')
                            bk2_avg_change = bk2_hist.get('avg_change')

                            bk1_kof_order = bk1_hist.get('order')
                            bk2_kof_order = bk2_hist.get('order')

                            k1 = bk1_bet_json.get('factor', 0)
                            k2 = bk2_bet_json.get('value', 0)

                            vect1 = bk1_bet_json.get('vector')
                            vect2 = bk2_bet_json.get('vector')
                            try:
                                info = key + ': ' + name + ', ' + \
                                       'place: ' + str(place) + ', ' + \
                                       'created: ' + created_fork + ', ' + \
                                       k1_type + '=' + str(k1) + '/' + \
                                       k2_type + '=' + str(k2) + ', ' + \
                                       v_time + ' (' + str(minute) + ') ' + \
                                       score + ' ' + str(pair_math) + \
                                       ', live_fork: ' + str(live_fork) + \
                                       ', live_fork_total: ' + str(live_fork_total) + \
                                       ', max deff: ' + str(curr_deff) + \
                                       ', event_type: ' + event_type + \
                                       ', fonbet_maxbet_fact: ' + str(fonbet_maxbet_fact)
                            except Exception as e:
                                exc_type, exc_value, exc_traceback = sys.exc_info()
                                err_str = str(e) + ' ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                                prnt('better: ' + err_str)
                                prnt('event_type: ' + event_type)
                                prnt('deff max: ' + str(curr_deff))
                                prnt('live fork total: ' + str(live_fork_total))
                                prnt('live fork: ' + str(live_fork))
                                prnt('pair_math: ' + str(pair_math))
                                prnt('score: ' + str(score))
                                prnt('minute: ' + str(minute))
                                prnt('time: ' + str(v_time))
                                prnt('k1: ' + str(k1))
                                prnt('k1_type: ' + str(k1_type))
                                prnt('k2: ' + str(k2))
                                prnt('k2_type: ' + str(k2_type))
                                prnt('name: ' + str(name))
                                prnt('key: ' + str(key))
                                prnt('val_json: ' + str(val_json))
                                prnt('vect1: ' + str(vect1))
                                prnt('vect2: ' + str(vect2))
                                info = ''
                            if event_type in sport_list:
                                if vect1 and vect2:
                                    max_deff = 3
                                    if place == 'pre':
                                        max_deff = 33
                                    if curr_deff <= curr_deff and k1 > 0 < k2:
                                        vect1_old = vect1
                                        vect2_old = vect2
                                        if vect1 == vect2:
                                            vect1, vect2 = normalized_vector(vect1, k1, vect2, k2)
                                            prnt('{} - Нормализация векторов: vect1: {}->{}, vect2: {}->{}'.format(key, vect1_old, vect1, vect2_old, vect2), 'hide')
                                        # TODO: binding for BK_NAME from kofs an not left/rigth side
                                        v_first_bet_in = get_prop('first_bet_in', 'auto')
                                        vect_check_ok = True
                                        if v_first_bet_in != 'auto':
                                            if v_first_bet_in == 'fonbet':
                                                vect1 = 'UP'
                                                vect2 = 'DOWN'
                                                if 'ТМ' in k2_type.upper() or 'ТБ' in k2_type.upper():
                                                    if get_prop('total_first') not in k2_type:
                                                        vect_check_ok = False
                                            elif v_first_bet_in == 'olimp':
                                                vect1 = 'DOWN'
                                                vect2 = 'UP'
                                                if 'ТМ' in k1_type.upper() or 'ТБ' in k1_type.upper():
                                                    if get_prop('total_first') not in k1_type:
                                                        vect_check_ok = False
                                            if not vect_check_ok and get_prop('total_first') == 'any':
                                                vect_check_ok = True
                                        elif get_prop('total_first') in key:
                                            # FB
                                            if get_prop('total_first') in k2_type:
                                                vect1 = 'UP'
                                                vect2 = 'DOWN'
                                            # OL
                                            elif get_prop('total_first') in k1_type:
                                                vect1 = 'DOWN'
                                                vect2 = 'UP'
                                            elif get_prop('total_first') == 'any':
                                                pass
                                            else:
                                                vect_check_ok = False
                                        prnt('{} - Первая ставка в {}: vect1: {}->{}, vect2: {}->{}'.format(key, v_first_bet_in, vect1_old, vect1, vect2_old, vect2), 'hide')

                                        round_bet = int(get_prop('round_fork'))
                                        total_bet = round(randint(total_bet_min, total_bet_max) / round_bet) * round_bet
                                        # prnt('total_bet random: ' + str(total_bet), 'hide')
                                        # prnt('start recalc_bets: ' + key, 'end')
                                        recalc_bets()
                                        # prnt('end recalc_bets: ' + key, 'end')
                                        team_type, team_names = get_team_type(name_rus, name)
                                        # team_junior - юнош.команды
                                        # team_female - жен.команды
                                        # team_stud - студ.команды
                                        # team_res - рез - екоманды
                                        # Проверим вилку на исключения
                                        if check_fork(
                                                key, l, k1, k2, live_fork, live_fork_total, bk1_score, bk2_score, event_type, minute, time_break_fonbet, period, team_type, team_names, curr_deff,
                                                level_liga, is_hot, info
                                        ) or DEBUG:
                                            prnt('OK - check_fork', 'hide')
                                            now_timestamp = int(time.time())
                                            last_timestamp = temp_lock_fork.get(key, now_timestamp)
                                            if 0 < (now_timestamp - last_timestamp) < 60 and len(server_forks) > 1:
                                                if key not in msg_excule_pushed:
                                                    msg_excule_pushed.append(key)
                                                    prnt(
                                                        vstr='Вилка ' + str(key) + ' исключена, т.к. мы ее пытались проставить не успешно, но прошло менее 60 секунд и есть еще вилки,'
                                                                                   'now:{}, last:{}, diff:{}'.format(now_timestamp, last_timestamp, now_timestamp - last_timestamp),
                                                        hide=None,
                                                        to_cl=True,
                                                        type_='fork'
                                                    )
                                            else:
                                                if key in msg_excule_pushed:
                                                    msg_excule_pushed.remove(key)
                                                temp_lock_fork.update({key: now_timestamp})
                                                cnt_act_acc = 0
                                                is_bet = 0
                                                cur_proc = round((1 - l) * 100, 2)
                                                fork_slice = int(get_prop('FORK_SLICE', 50))

                                                prnt('% уникальности: ' + str(fork_slice))

                                                if fork_slice:
                                                    sql = cnt_acc_sql \
                                                        .replace(':cur_proc', str(cur_proc)) \
                                                        .replace(':live_fork', str(live_fork)) \
                                                        .replace(':team_type', str(team_type)) \
                                                        .replace(':is_top', str(level_liga)) \
                                                        .replace(':acc_id', str(ACC_ID))

                                                    prnt('SQL:\n', 'hide')
                                                    prnt(sql, 'hide')

                                                    cursor = db.execute_sql(sql)
                                                    cnt_act_acc = cursor.fetchone()[0]

                                                    prnt('cnt_act_acc: ' + str(cnt_act_acc))

                                                    is_bet = randint(1, 100)

                                                    prnt('Активных акаунтов на вилку: ' + str(cnt_act_acc))
                                                    prnt('Случайное число: ' + str(is_bet) + ', => ' + str(fork_slice))

                                                if fork_slice <= is_bet or cnt_act_acc <= 5 or fork_slice == 0:
                                                    prnt(vstr=' ' + key + ' ' + info, hide=None, to_cl=True)
                                                    prnt(vstr='Делаю ставку: ' + key + ' ' + info, hide=None, to_cl=True)

                                                    info_csv.update({
                                                        'user_id': str(USER_ID),
                                                        'group_limit_id': group_limit_id,
                                                        'live_fork': live_fork,
                                                        'team_type': team_type,
                                                        'summ_min': summ_min_stat,
                                                        'maxbet_fact': get_prop('maxbet_fact', 'выкл'),
                                                        'fonbet_maxbet_fact': fonbet_maxbet_fact,
                                                        'fb_bk_type': get_prop('fonbet_s', 'com'),
                                                        'first_bet_in': get_prop('first_bet_in', 'auto'),
                                                        'total_first': get_prop('total_first', 'auto'),
                                                        'place': place
                                                    })
                                                    prnt('info_csv: ' + str(info_csv))
                                                    prnt('{} - Первая ставка в {}: vect1-olimp: {}->{}, vect2-fonbet: {}->{}'.format(
                                                        key, v_first_bet_in, vect1_old, vect1, vect2_old, vect2)
                                                    )
                                                    fork_success = go_bets(
                                                        val_json.get('kof_olimp'), val_json.get('kof_fonbet'),
                                                        key, curr_deff, vect1, vect2, sc1, sc2, created_fork, event_type,
                                                        l, l_fisrt, level_liga, str(fork_slice), str(cnt_act_acc), info_csv
                                                    )
                                        else:
                                            prnt('ERR - check_fork', 'hide')
                                    elif curr_deff > max_deff:
                                        pass
                                        prnt('ERR T - check_fork', 'hide')
                                        # if key not in sleeping_forks:
                                        #     sleeping_forks.append(key)
                                        #     prnt('Sleeping forks: ' + str(deff_max) + ' sec (' + str(time.time()) + '), ' + str(key) + ': ' + str(val_json))
                                else:
                                    # prnt('Вектор направления коф-та не определен: VECT1=' + str(vect1) + ', VECT2=' + str(vect2))
                                    pass
                            else:
                                # prnt('Вилка исключена, т.к. вид спорта: ' + event_type + ', base_line: ' + str(base_line))
                                pass
                    else:
                        pass
                    # ts = round(uniform(1, 3), 2)
                    # prnt('ts:' + str(ts), 'hide')
                    time.sleep(0.5)


    except (Shutdown, MaxFail, MaxFork) as e:
        try:
            shutdown = True
            prnt(' ')
            prnt(str(e))

            send_message_bot(USER_ID, str(ACC_ID) + ': ' + str(e), ADMINS)

            last_fork_time_diff = int(time.time()) - last_fork_time
            if get_prop('place') == 'pre':
                wait_before_exp = 0
            else:
                wait_before_exp = max(60 * 60 * 2 - last_fork_time_diff, 0)
            prnt(str(last_fork_time_diff) + ' секунд прошло с момента последней ставки')
            if DEBUG:
                wait_before_exp = 0
            if wait_before_exp:
                msg_str = str(ACC_ID) + ': Ожидание ' + str(round(wait_before_exp / 60)) + ' минут, до выгрузки'
                prnt(msg_str)
                send_message_bot(USER_ID, msg_str, ADMINS)
            while Account.select().where(Account.key == KEY).get().pid > 0 and Account.select().where(Account.key == KEY).get().work_stat == 'start' and wait_before_exp > 0:
                wait_before_exp = wait_before_exp - 10
                time.sleep(10)

            if wait_before_exp <= 0:
                send_message_bot(USER_ID, str(ACC_ID) + ': Делаю выгрузку, пожалуйста подождите...')
                export_hist(OLIMP_USER, FONBET_USER)
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            err_str = str(e) + ' ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
            prnt(err_str)

    except Exception as e:
        shutdown = True

        exc_type, exc_value, exc_traceback = sys.exc_info()
        err_str = str(e) + ' ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        err_str = str(ACC_ID) + ': Возникла ошибка! ' + str(e.__class__.__name__) + ' - ' + str(err_str)
        prnt(err_str)

        send_message_bot(USER_ID, str(ACC_ID) + ': Возникла ошибка, ' + str(e), ADMINS)

    finally:
        shutdown = True

        msg_str = str(ACC_ID) + ': Завершил работу'
        prnt(msg_str)
        Account.update(pid=0, work_stat='stop', time_stop=round(time.time())).where(Account.key == KEY).execute()
        send_message_bot(USER_ID, msg_str, ADMINS)
