# coding:utf-8
from bet_fonbet import *
from bet_olimp import *
import datetime
import time
from fork_recheck import get_kof_olimp, get_kof_fonbet
from utils import prnt, get_account_info, get_prop, get_sum_bets, get_new_sum_bets, get_proxies
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
from db_model import send_message_bot, prop_abr
from bot_prop import ADMINS
from ml import get_vect, check_vect, check_noise, get_creater
import random

if __name__ == '__main__':
    from history import export_hist

global KEY, ACC_ID

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
    global MIN_PROC, ACC_ID
    MIN_L = 1 - (MIN_PROC / 100)

    l_exclude_text = ''

    # if L <= 0.90 and str(ACC_ID) != '3':
    #         l_exclude_text = l_exclude_text + 'Вилка ' + str(L) + ' (' + str(round((1 - L) * 100, 2)) + '%), вилка исключена т.к. доходноть высокая >= 10%\n'
    if L > MIN_L:
        l_exclude_text = l_exclude_text + 'Вилка ' + str(L) + ' (' + str(round((1 - L) * 100, 3)) + '%), беру вилки только >= ' + str(round((1 - MIN_L) * 100, 3)) + '%\n'

    if l_exclude_text != '':
        return l_exclude_text
    else:
        return ''


def bet_type_is_work(key):
    # if 'ТМ' in key or \
    #   'ТБ' in key or \
    #   \
    #   'П1' in key or \
    #   'П2' in key or \
    #   \
    #   'КЗ' in key or \
    #   'КНЗ' in key or \
    #   \
    #   'ОЗД' == key or \
    #   'ОЗН' == key:
    return True


def check_fork(key, L, k1, k2, live_fork, live_fork_total, bk1_score, bk2_score, event_type, minute, time_break_fonbet, period, name, name_rus, deff_max, is_top, info=''):
    global bal1, bal2, bet1, bet2, cnt_fork_success, black_list_matches

    fork_exclude_text = ''
    v = True

    if L < 0.70:
        fork_exclude_text = fork_exclude_text + 'Вилка ' + str(L) + ' (' + str(round((1 - L) * 100, 2)) + '%), вилка исключена т.к. доходноть высокая > 30%\n'

    if get_prop('team_junior', 'выкл') == 'выкл':
        if re.search('(u\d{2}|\(.*\d{2}\))', name_rus.lower()):
            fork_exclude_text = fork_exclude_text + 'Вилка исключена по названию команд: ' + name_rus + '\n'

        if re.search('u\d{2}', name.lower()):
            fork_exclude_text = fork_exclude_text + 'Вилка исключена по названию команд: ' + name + '\n'

    if get_prop('team_female', 'выкл') == 'выкл':
        if re.search('(\(жен\)|\(ж\))', name_rus.lower()):
            fork_exclude_text = fork_exclude_text + 'Вилка исключена по названию команд: ' + name_rus + '\n'

        if re.search('\(w\)', name.lower()):
            fork_exclude_text = fork_exclude_text + 'Вилка исключена по названию команд: ' + name + '\n'

    if get_prop('team_stud', 'выкл') == 'выкл':
        if re.search('(\s|-|\(\.)студ', name_rus.lower()):
            fork_exclude_text = fork_exclude_text + 'Вилка исключена по названию команд: ' + name_rus + '\n'

        if re.search('(\s|-|\(\.)stud', name.lower()):
            fork_exclude_text = fork_exclude_text + 'Вилка исключена по названию команд: ' + name + '\n'

    if get_prop('team_res', 'выкл') == 'выкл':
        if re.search('(\(р\)|\(рез\))', name_rus.lower()):
            fork_exclude_text = fork_exclude_text + 'Вилка исключена по названию команд: ' + name_rus + '\n'

        if re.search('(\(r\)|\(res\)|\(reserves\))', name.lower()):
            fork_exclude_text = fork_exclude_text + 'Вилка исключена по названию команд: ' + name + '\n'

    if not bet_type_is_work(key):
        fork_exclude_text = fork_exclude_text + 'Вилка исключена, т.к. я еще не умею работать с этой ставкой: ' + str(key) + ')\n'

    deff_limit = 3
    if deff_max > deff_limit:
        fork_exclude_text = fork_exclude_text + 'Вилка исключена, т.к. deff_max (' + str(deff_max) + ' > ' + str(deff_limit) + ')\n'

    if get_prop('double_bet', 'выкл') == 'выкл':
        if cnt_fork_success.count(key) > 0:
            fork_exclude_text = fork_exclude_text + 'Вилка не проставлена, т.к. уже проставляли на эту вилку: ' + key + '\n'

    if black_list_matches.count(key.split('@')[0]) > 0 or black_list_matches.count(key.split('@')[1]) > 0:
        fork_exclude_text = fork_exclude_text + 'Вилка исключена, т.к. матч занесен в blacklist: ' + key + ', ' + str(black_list_matches) + '\n'

    # Проверяем корректная ли сумма
    if bet1 < 30 or bet2 < 30:
        fork_exclude_text = fork_exclude_text + 'Сумма одной из ставок меньше 30р.\n'

    # Проверяем хватить денег для ставки
    if (bal1 < bet1) or (bal2 < bet2):
        fork_exclude_text = fork_exclude_text + 'Для проставления вилки ' + str(round((1 - L) * 100, 2)) \
                            + '% недостаточно средств, bal1=' \
                            + str(bal1) + ', bet1=' + str(bet1) \
                            + ', bal2=' + str(bal2) + ', bet2=' + str(bet2) + '\n'

    if get_prop('max_kof'):
        max_kof = float(get_prop('max_kof'))
        if k1 > max_kof or k2 > max_kof:
            fork_exclude_text = fork_exclude_text + 'Вилка ' + str(round((1 - L) * 100, 2)) + '% исключена т.к. коэф-большой: ({}/{}) > {})\n'.format(k1, k2, max_kof)

    if bk1_score != bk2_score:
        fork_exclude_text = fork_exclude_text + 'Вилка ' + str(round((1 - L) * 100, 2)) + '% исключена т.к. счет не совпадает: olimp(' + bk1_score + ') fonbet(' + bk2_score + ')\n'

    if event_type == 'football':
        # Больше 43 минуты и не идет перерыв и это 1 период
        if 43.0 < float(minute) and not time_break_fonbet and period == 1:
            fork_exclude_text = fork_exclude_text + 'Вилка ' + str(round((1 - L) * 100, 2)) + '% исключена т.к. идет ' + \
                                str(minute) + ' минута матча и это не перерыв / не 2-й период \n'

        if float(minute) > 88.0:
            fork_exclude_text = fork_exclude_text + 'Вилка ' + str(round((1 - L) * 100, 2)) + '% исключена т.к. идет ' + str(minute) + ' минута матча \n'

    # Вилка живет достаточно
    long_livers = int(get_prop('fork_life_time'))
    if get_prop('fork_time_type', 'auto') in ('auto', 'текущее'):
        if live_fork - deff_max < long_livers:
            fork_exclude_text = fork_exclude_text + 'Вилка ' + str(round((1 - L) * 100, 2)) + '% исключена т.к. живет меньше ' + str(long_livers) + ' сек. \n'
    else:
        if live_fork_total - deff_max < long_livers:
            fork_exclude_text = fork_exclude_text + 'Вилка ' + str(round((1 - L) * 100, 2)) + '% исключена т.к. живет в общем меньше ' + str(long_livers) + ' сек. \n'

    if get_prop('top', 'выкл') == 'вкл' and not is_top:
        fork_exclude_text = fork_exclude_text + 'Вилка исключена т.к. это не топовый матч: ' + name_rus + '\n'

    pour_into = get_prop('pour_into', 'auto')
    if pour_into != 'auto':
        if pour_into == 'olimp' and k1 > k2:
            fork_exclude_text = fork_exclude_text + 'Вилка исключена т.к. задан перелив в {}, а коф-т менее вероятен: k_ol:{} > k_fb:{}\n'.format(pour_into, k1, k2)
        elif pour_into == 'fonbet' and k2 > k1:
            fork_exclude_text = fork_exclude_text + 'Вилка исключена т.к. задан перелив в {}, а коф-т менее вероятен: k_ol:{} < k_fb:{}\n'.format(pour_into, k1, k2)

    fork_exclude_text = fork_exclude_text + check_l(L)

    if fork_exclude_text != '':
        prnt(info + '\n' + fork_exclude_text + '\n', 'hide')
        v = False
    return v


def upd_last_fork_time(v_time: int = None):
    global last_fork_time
    if v_time:
        last_fork_time = v_time
    else:
        last_fork_time = int(time.time())


def set_statistics(key, err_bk1, err_bk2, fork_info=None, bk1_sale_profit=0, bk2_sale_profit=0):
    global cnt_fail, black_list_matches, cnt_fork_success
    bet_skip = False
    if err_bk1 and err_bk2:
        if 'BkOppBetError' in err_bk1 and 'BkOppBetError' in err_bk2:
            bet_skip = True
            if fork_info:
                fork_info['olimp']['err'] = 'Вилка была пропущена: ' + err_bk1
                fork_info['fonbet']['err'] = 'Вилка была пропущена: ' + err_bk2

    if err_bk1 != 'ok' or err_bk2 != 'ok':
        if not bet_skip:
            if bk1_sale_profit < 0 or bk2_sale_profit < 0:
                cnt_fail = cnt_fail + 1
            black_list_matches.append(key.split('@')[0])
            black_list_matches.append(key.split('@')[1])
            # Добавим доп инфу о проставлении
            upd_last_fork_time()
    elif not bet_skip:
        cnt_fork_success.append(key)
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


def go_bets(wag_ol, wag_fb, key, deff_max, vect1, vect2, sc1, sc2, created, event_type, l, l_fisrt, is_top):
    global bal1, bal2, cnt_fail, cnt_fork_success, k1, k2, total_bet, bet1, bet2, OLIMP_USER, FONBET_USER

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

        shared = dict()

        shared['olimp'] = {
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
        }
        shared['fonbet'] = {
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
        }
        if '(' in fonbet_bet_type:
            shared['olimp']['bet_total'] = float(re.findall(r'\((.*)\)', fonbet_bet_type)[0])
            shared['fonbet']['bet_total'] = float(re.findall(r'\((.*)\)', fonbet_bet_type)[0])

        for bk_name, val in shared.items():
            prnt('BK ' + str(bk_name) +
                 ': bet_total:{}, cur_total:{}, sc1:{}, sc2:{}, v:{} ({})'.format(
                     val.get('bet_total', ''), val.get('cur_total', ''),
                     val.get('sc1', ''), val.get('sc2', ''),
                     val.get('vect', ''), val.get('wager', '')))

        x = wag_fb.get('hist', {}).get('avg_change')
        y = wag_fb.get('hist', {}).get('order')

        x2 = wag_ol.get('hist', {}).get('avg_change')
        y2 = wag_ol.get('hist', {}).get('order')

        if get_prop('ml_noise', 'выкл') == 'вкл':
            if sum(x) >= 2 <= sum(x2):
                ml_ok = False
                real_vect2, real_vect1, noise2, noise1, k2_is_noise, k1_is_noise, plt = get_vect(x, y, x2, y2)

                filename = key.replace('.', '')
                # ML #1 - CHECK VECTS
                # if not ACC_ID in (1, 3):
                if check_vect(real_vect1, real_vect2) and check_noise(noise1, noise2):
                    ml_ok = True
                    prnt('Fork key: ' + str(filename) + ', успешно прошел проверку 1 (векторы строго сонаправлены и нет шума)')
                    if vect1 != real_vect1:
                        prnt('Вектор в Олимп измнен: {}->{}'.format(vect1, real_vect1))
                        shared['olimp']['vect'] = real_vect1
                    if vect2 != real_vect2:
                        prnt('Вектор в Фонбет измнен: {}->{}'.format(vect2, real_vect2))
                        shared['fonbet']['vect'] = real_vect2
                    save_plt(str(ACC_ID) + '_I_ok', filename, plt)
                else:
                    prnt('Fork key: ' + str(filename) + ', не прошел проверку 1 (векторы строго сонаправлены и нет шума)')
                    save_plt(str(ACC_ID) + '_I_err', filename, plt)

                # ML #2 CHECK CREATER-NOISE
                if not ml_ok:
                    side_created = get_creater(k1_is_noise, k2_is_noise)
                    if side_created == 1:
                        fake_vect1 = 'DOWN'
                        fake_vect2 = 'UP'
                    elif side_created == 2:
                        fake_vect2 = 'DOWN'
                        fake_vect1 = 'UP'
                    else:
                        prnt('Fork key: ' + str(filename) + ', не прошел проверку 2 (Шумный создатель вилки)')
                        save_plt(str(ACC_ID) + '_II_err', filename, plt)

                    if side_created:
                        ml_ok = True
                        prnt('Fork key: ' + str(filename) + ', успешно прошел проверку 2 (Шумный создатель вилки)')
                        if vect1 != fake_vect1:
                            prnt('Вектор в Олимп измнен: {}->{}'.format(vect1, fake_vect1))
                            shared['olimp']['vect'] = fake_vect1
                        if vect2 != fake_vect2:
                            prnt('Вектор в Фонбет измнен: {}->{}'.format(vect2, fake_vect2))
                            shared['fonbet']['vect'] = fake_vect2
                        save_plt(str(ACC_ID) + '_II_ok', filename, plt)

                plt.close()
                if not ml_ok:
                    return False
            else:
                prnt('Проверка на ML не пройдена т.к. один их Х < 2')
                return False

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

        fork_info[fork_id]['fonbet']['max_bet'] = shared['fonbet'].get('max_bet')

        fork_info[fork_id]['fonbet']['is_top'] = is_top
        fork_info[fork_id]['fonbet']['is_hot'] = wag_fb.get('is_hot')

        fork_info[fork_id]['fonbet']['avg_change'] = str(x)
        fork_info[fork_id]['fonbet']['order_kof'] = str(y)

        fork_info[fork_id]['olimp']['avg_change'] = str(x2)
        fork_info[fork_id]['olimp']['order_kof'] = str(y2)

        # CHECK FATAL ERROR
        if shared.get('fonbet_err_fatal') or shared.get('olimp_err_fatal'):
            msg_str = 'Обнаружена фатальная ошибка: ' + \
                      str(shared.get('fonbet_err_fatal')) + \
                      str(shared.get('olimp_err_fatal')) + ', проверьте счет на порезку, блокировку ставки и вывода средств!'
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
        if not 'BkOppBetError'.lower() in msg_errs.lower():
            # SAVE INFO
            save_fork(fork_info)
            # WAITING AFTER BET
            sleep_post_work = int(get_prop('timeout_fork', 30))
            prnt('Ожидание ' + str(sleep_post_work) + ' сек.')
            time.sleep(sleep_post_work)
            # GET NEW BALANCE
            bal1 = OlimpBot(OLIMP_USER).get_balance()  # Баланс в БК1
            bal2 = FonbetBot(FONBET_USER).get_balance()  # Баланс в БК2
        # CHECK FAILS
        check_statistics()
        return True


def run_client():
    global server_forks
    global shutdown
    global server_ip

    try:
        if 'Windows' == platform.system() or DEBUG:
            conn = http.client.HTTPConnection(server_ip, 8888, timeout=3.51)
        else:
            conn = http.client.HTTPConnection(server_ip, 8888, timeout=6)

        while True:
            if shutdown:
                err_str = 'Основной поток завершен и run_client тоже.'
                conn.close()
                raise Shutdown(err_str)
            conn.request('GET', '/get_forks')
            rs = conn.getresponse()
            data = rs.read().decode('utf-8')
            data_json = json.loads(data)
            server_forks = data_json
            time.sleep(1)
    except Shutdown as e:
        prnt(str(e.__class__.__name__) + ' - ' + str(e))
        raise Shutdown(e)
    except Exception as e:
        prnt('better: ' + str(e.__class__.__name__) + ' - ' + str(e))
        server_forks = {}
        conn.close()
        time.sleep(10)
        return run_client()


def recalc_bets(hide=True):
    global k1, k2, total_bet, bal1, bal1, bet1, bet2, total_bet_min, total_bet_max, round_bet
    prnt('Get sum bets', hide)
    prnt('total_bet: {}, total_bet_min: {}, total_bet_max: {}, round_bet: {}, bal1:{}, bal2:{}, bet1:{},  bet2:{}'.format(
        total_bet, total_bet_min, total_bet_max, round_bet, bal1, bal2, bet1, bet2), hide
    )
    bet1, bet2 = get_sum_bets(k1, k2, total_bet, 5, hide)
    if bet1 > bal1 or bet2 > bal2:
        if bal1 < bal2:
            prnt('recalc bet (bal1 < bal2)', hide)
            bet1, bet2 = get_new_sum_bets(k1, k2, bal1, hide)
            total_bet = bet1 + bet2
        else:
            prnt('recalc bet (bal1 > bal2)', hide)
            bet2, bet1 = get_new_sum_bets(k2, k1, bal2, hide)
            total_bet = bet1 + bet2

    max_bet_fonbet = int(get_prop('max_bet_fonbet', '0'))
    if bet2 > max_bet_fonbet > 0:
        prnt('recalc bet (max_bet_fonbet)', hide)
        bet2, bet1 = get_new_sum_bets(k2, k1, max_bet_fonbet, hide)
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
printed = False
last_fork_time = 0
long_pool_wait = randint(30, 60)

cnt_fork_success_old = 0
cnt_fork_fail_old = 0
start_message_send = False

temp_lock_fork = {}

export_block = False

# wag_fb:{'event': '12797479', 'factor': '921', 'param': '', 'score': '0:0', 'value': '2.35'}
# wag_fb:{'apid': '1144260386:45874030:1:3:-9999:3:NULL:NULL:1', 'factor': '1.66', 'sport_id': 1, 'event': '45874030'}

if __name__ == '__main__':
    try:
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

        if not DEBUG:
            server_ip = get_prop('server_ip')
        else:
            server_ip = get_prop('server_ip_test')

        MIN_PROC = float(get_prop('min_proc').replace(',', '.'))
        prnt(' ')
        prnt('Current Time: ' + str(datetime.datetime.now()))
        prnt('Long pool sec: ' + str(long_pool_wait))
        prnt('ID аккаунта: ' + str(ACC_ID))
        prnt('IP-адрес сервера: ' + server_ip + ':8888')
        prnt('Баланс в БК Олимп: ' + str(bal1))
        prnt('Баланс в БК Фонбет: ' + str(bal2))

        prnt('Блокировка вывода: ' + str(bk2.get_acc_info('pay')))
        prnt('Блокировка ставки: ' + str(bk2.get_acc_info('bet')))
        prnt('Группа лимита: ' + str(bk2.get_acc_info('group')))

        get_round_fork = int(get_prop('round_fork'))
        if get_round_fork not in (5, 10, 50, 100, 1000):
            err_msg = 'Недопустимое округление ставки={}'.format(get_round_fork)
            raise ValueError(err_msg)
        else:
            prnt('Округление вилки и суммы ставки до: ' + str(get_round_fork))

        random_summ_proc = int(get_prop('random_summ_proc'))
        if random_summ_proc > 30:
            err_msg = 'Отклонение от общей суммы ставки не должно привышать 30%'
            raise ValueError(err_msg)
        else:
            if not DEBUG and total_bet < 400:
                err_msg = 'Обшая сумма ставки, должна превышать 400 руб.'
                raise ValueError(err_msg)
            else:
                total_bet_min = int(total_bet - (total_bet * int(random_summ_proc) / 100))
                total_bet_max = int(total_bet + (total_bet * int(random_summ_proc) / 100))
                prnt('total_bet:{}, total_bet_min: {}, total_bet_max: {}'.format(total_bet, total_bet_min, total_bet_max))

        acc_info = Account.select().where(Account.key == KEY)
        print(acc_info)
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

        server_forks = dict()
        start_see_fork = threading.Thread(target=run_client)  # , args=(server_forks,))
        start_see_fork.start()

        wait_before_start_sec = float(randint(1, 300))
        send_message_bot(USER_ID, str(ACC_ID) + ': ' + 'Аккаунт запущен', ADMINS)
        prnt('начну работу через ' + str(round(wait_before_start_sec)) + ' сек...')
        
        if str(ACC_ID) == '3':
            #select count(*) from account a where a.work_stat = 'start' and exists(select 1 from properties p where p. `key` = 'MIN_PROC' and round(cast(p.val as decimal(3, 1))) = round(3) and p.acc_id = a.id); 
            
            cnt = Account.select().join(Properties).where( 
                (Account.work_stat == 'start') & 
                (Properties.key == 'MIN_PROC') & 
                (Properties.val >= round(MIN_PROC)) 
            )#.count()
            x = ''
            for c in cnt:
                x = x + str(c.id) + ','
            print(x)
                
        
        while Account.select().where(Account.key == KEY).get().work_stat == 'start':

            if wait_before_start_sec > 0:
                wait_before_start_sec = wait_before_start_sec - 0.5
                time.sleep(0.5)
            else:
                
                time_export = False
                if get_prop('work_hour_end'):
                    if int(get_prop('work_hour_end')) == int(datetime.datetime.now().strftime('%H')):
                        time_export = True
                
                if os.path.exists('./' + str(ACC_ID) + '_id_forks.txt'):
                    if export_block:
                        if not time_export:
                            export_block = False
                    else: 
                        if time_export:
                            msg_str = 'Время выгрузки: {} ч., начинаю выгрузку...'.format(get_prop('work_hour_end'))
                            raise Shutdown(msg_str)
                else:
                    export_block = True

                # Обновление баланса каждые 120 минут
                ref_balace = 120
                if (datetime.datetime.now() - time_get_balance).total_seconds() > (60 * ref_balace):
                    prnt(' ')
                    prnt('Прошло больше ' + str(ref_balace) + ' минут, пора обновить балансы:')
                    time_get_balance = datetime.datetime.now()
                    bal1 = bk1.get_balance()  # Баланс в БК1
                    bal2 = bk2.get_balance()  # Баланс в БК2
                one_proc = (bal1 + bal2) / 100

                msg_str = str(ACC_ID) + ': '
                msg_push = False

                msg_err = ''

                if bk2.get_acc_info('bet').lower() != 'Нет'.lower():
                    msg_err = msg_err + '\n' + 'обнаружена блокировка ставки в Фонбет, аккаунт остановлен!'

                if bk2.get_acc_info('pay').lower() != 'Нет'.lower():
                    msg_err = msg_err + '\n' + 'обнаружена блокировка вывода, нужно пройти верификацию в Фонбет, аккаунт остановлен!'

                if str(bk2.get_acc_info('group')).lower() == '4'.lower():
                    msg_err = msg_err + '\n' + 'обнаружена порезка до 4й группы, аккаунт остановлен!'

                if bal1 == 0 or bal2 == 0:
                    if (len(cnt_fork_success) == 0 and cnt_fail == 0) or ((int(time.time()) - last_fork_time) > 7200):
                        msg_err = msg_err + '\n' + 'баланс в одной из БК равен 0, аккаунт остановлен!\n' + bk1_name + ': ' + str(bal1) + '\n' + bk2_name + ': ' + str(bal2)

                if (bal1 / one_proc) < 10 or (bal2 / one_proc) < 10:
                    if (len(cnt_fork_success) == 0 and cnt_fail == 0) or ((int(time.time()) - last_fork_time) > 7200):
                        msg_err = msg_err + '\n' + 'аккаунт остановлен: денег в одной из БК не достаточно для работы, просьба выровнять балансы.\n' + bk1_name + ': ' + str(bal1) + '\n' + bk2_name + ': ' + str(bal2)

                if msg_err != '':
                    prnt(msg_err.strip())
                    raise Shutdown(msg_err.strip())

                if not start_message_send:
                    cnt_fork_success_old = len(cnt_fork_success)
                    cnt_fork_fail_old = cnt_fail
                    msg_str = str(ACC_ID) + ': Распределение балансов:\n' + bk1_name + ': ' + str(round(bal1 / one_proc)) + '%\n' + bk2_name + ': ' + str(round(bal2 / one_proc)) + '%'
                    if cnt_fork_success_old != 0:
                        msg_str = msg_str + '\nПроставлено вилок: {}'.format(len(cnt_fork_success))
                    if cnt_fork_fail_old != 0:
                        msg_str = msg_str + '\nСделано минусовы выкупов: {}'.format(cnt_fail)
                    msg_push = True
                    start_message_send = True
                elif len(cnt_fork_success) != cnt_fork_success_old:
                    msg_str = msg_str + 'Проставлено вилок: {}->{}'.format(cnt_fork_success_old, len(cnt_fork_success)) + '\n'
                    msg_str = msg_str + 'Сделано минусовы выкупов: {}'.format(cnt_fail) + '\n'
                    cnt_fork_success_old = len(cnt_fork_success)
                    msg_push = True
                elif cnt_fork_fail_old != cnt_fail:
                    msg_str = msg_str + 'Проставлено вилок: {}'.format(len(cnt_fork_success)) + '\n'
                    msg_str = msg_str + 'Сделано минусовы выкупов: {}->{}'.format(cnt_fork_fail_old, cnt_fail) + '\n'
                    cnt_fork_fail_old = cnt_fail
                    msg_push = True

                if msg_push:
                    msg_push = False
                    send_message_bot(USER_ID, msg_str.strip(), ADMINS)

                if server_forks:
                    for key, val_json in sorted(server_forks.items(), key=lambda x: random.random()):
                        l = val_json.get('l', 0.0)
                        l_fisrt = val_json.get('l_fisrt', 0.0)
                        k1_type = key.split('@')[-1]
                        k2_type = key.split('@')[-2]

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
                        is_top = val_json.get('is_top')
                        period = val_json.get('period')
                        time_last_upd = val_json.get('time_last_upd', 1)
                        live_fork_total = val_json.get('live_fork_total', 0)
                        live_fork = val_json.get('live_fork', 0)
                        created_fork = val_json.get('created_fork', '')
                        event_type = val_json.get('event_type')

                        deff_olimp = round(float(time.time() - float(val_json.get('time_req_olimp', 0))))
                        deff_fonbet = round(float(time.time() - float(val_json.get('time_req_fonbet', 0))))
                        deff_max = max(0, deff_olimp, deff_fonbet)

                        bk1_bet_json = val_json.get('kof_olimp')
                        bk2_bet_json = val_json.get('kof_fonbet')

                        bk1_hist = bk1_bet_json.get('hist', {})
                        bk2_hist = bk2_bet_json.get('hist', {})

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
                                   'created: ' + created_fork + ', ' + \
                                   k1_type + '=' + str(k1) + '/' + \
                                   k2_type + '=' + str(k2) + ', ' + \
                                   v_time + ' (' + str(minute) + ') ' + \
                                   score + ' ' + str(pair_math) + \
                                   ', live_fork: ' + str(live_fork) + \
                                   ', live_fork_total: ' + str(live_fork_total) + \
                                   ', max deff: ' + str(deff_max) + \
                                   ', event_type: ' + event_type
                        except Exception as e:
                            exc_type, exc_value, exc_traceback = sys.exc_info()
                            err_str = str(e) + ' ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                            prnt('better: ' + err_str)

                            prnt('event_type: ' + event_type)

                            prnt('deff max: ' + str(deff_max))
                            prnt('live fork total: ' + str(live_fork_total))
                            prnt('live fork: ' + str(live_fork))
                            prnt('pair_math: ' + str(pair_math))
                            prnt('score: ' + str(score))
                            prnt('minute: ' + str(minute))
                            prnt('time: ' + str(v_time))
                            prnt('k2_type: ' + str(k2_type))
                            prnt('k1_type: ' + str(k1_type))
                            prnt('k1: ' + str(k1))
                            prnt('k2: ' + str(k2))
                            prnt('name: ' + str(name))
                            prnt('key: ' + str(key))
                            prnt('val_json: ' + str(val_json))

                            info = ''
                        if (event_type == 'football' and get_prop('test_oth_sport', 'выкл') == 'выкл') or (event_type in ('hockey', 'football') and get_prop('test_oth_sport', 'выкл') == 'вкл'):
                            if vect1 and vect2:
                                if deff_max < 3 and k1 > 0 < k2:
                                    round_bet = int(get_prop('round_fork'))
                                    total_bet = round(randint(total_bet_min, total_bet_max) / round_bet) * round_bet
                                    prnt('total_bet random: ' + str(total_bet), 'hide')

                                    recalc_bets()
                                    # Проверим вилку на исключения
                                    if check_fork(key, l, k1, k2, live_fork, live_fork_total, bk1_score, bk2_score, event_type, minute, time_break_fonbet, period, name, name_rus, deff_max, is_top, info) or DEBUG:
                                        prnt(' ')

                                        now_timestamp = int(time.time())
                                        last_timestamp = temp_lock_fork.get(key, now_timestamp)
                                        prnt('now_timestamp: ' + str(now_timestamp) + ', last_timestamp:' + str(last_timestamp) + ', server_forks:' + str(len(server_forks)) + '\n' + str(server_forks))

                                        if 0 < (now_timestamp - last_timestamp) < 60 and len(server_forks) > 1:
                                            prnt('Вилка исключена, т.к. мы ее пытались проставить успешно/не успешно, но прошло менее 60 секунд и есть еще вилки, будем ставить другие, новые')
                                        else:
                                            temp_lock_fork.update({key: now_timestamp})
                                            prnt('Go bets: ' + key + ' ' + info)
                                            fork_success = go_bets(val_json.get('kof_olimp'), val_json.get('kof_fonbet'), key, deff_max, vect1, vect2, sc1, sc2, created_fork, event_type, l, l_fisrt, is_top)
                                elif deff_max >= 3:
                                    pass
                            else:
                                prnt('Вектор направления коф-та не определен: VECT1=' + str(vect1) + ', VECT2=' + str(vect2))
                        else:
                            prnt('Вилка исключена, т.к. вид спорта: ' + event_type)
                else:
                    pass
                ts = round(uniform(1, 3), 2)
                prnt('ts:' + str(ts), 'hide')
                time.sleep(ts)

    except (Shutdown, MaxFail, MaxFork) as e:
        try:
            shutdown = True
            prnt(' ')
            prnt(str(e))

            send_message_bot(USER_ID, str(ACC_ID) + ': ' + str(e), ADMINS)

            last_fork_time_diff = int(time.time()) - last_fork_time
            wait_before_exp = max(60 * 60 * 2 - last_fork_time_diff, 0)
            prnt(str(last_fork_time_diff) + ' секунд прошло с момента последней ставки')
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
        Account.update(pid=0, work_stat='stop', time_stop=round(time.time())).where(Account.key == KEY).execute()
        send_message_bot(USER_ID, msg_str, ADMINS)
