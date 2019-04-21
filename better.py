# coding:utf-8
from bet_fonbet import *
from bet_olimp import *
import datetime
from fork_recheck import get_kof_olimp, get_kof_fonbet
from utils import prnt, get_account_info, get_prop, prop_abr
import threading
from multiprocessing import Manager, Process
import time
from random import randint
import platform
from exceptions import FonbetBetError, OlimpBetError, Shutdown, MaxFail, MaxFork
import http.client
import json
import re
import sys
import traceback
import os
from db_model import send_message_bot
from bot_prop import ADMINS

if __name__ == '__main__':
    from history import export_hist

global KEY, ACC_ID

shutdown = False
if get_prop('debug'):
    DEBUG = True
else:
    DEBUG = False


def get_sum_bets(k1, k2, total_bet, hide=False):
    round_fork = int(get_prop('round_fork'))

    k1 = float(k1)
    k2 = float(k2)
    prnt('k1:{}, k2:{}'.format(k1, k2), hide)
    l = (1 / k1) + (1 / k2)

    # Округление проставления в БК1 происходит по правилам математики
    bet_1 = round(total_bet / (k1 * l) / round_fork) * round_fork
    bet_2 = total_bet - bet_1

    prnt('L: ' + str(round((1 - l) * 100, 2)) + '% (' + str(l) + ') ', hide)
    prnt('bet1: ' + str(bet_1) + ', bet2: ' + str(bet_2) + '|' + ' bet_sum: ' + str(bet_1 + bet_2), hide)

    return bet_1, bet_2


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
    global MIN_L

    l_exclude_text = ''

    if L <= 0.90:
        l_exclude_text = l_exclude_text + 'Вилка ' + str(L) + ' (' + str(round((1 - L) * 100, 2)) + \
                         '%), вилка исключена т.к. доходноть высокая >= 10%\n'
    if L > MIN_L:
        l_exclude_text = l_exclude_text + 'Вилка ' + \
                         str(L) + ' (' + str(round((1 - L) * 100, 3)) + '%), беру вилки только >= ' + str(round((1 - MIN_L) * 100, 3)) + '%\n'

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


def check_fork(key, L, k1, k2, live_fork, bk1_score, bk2_score, minute, time_break_fonbet, period, name, name_rus, deff_max, info=''):
    global bal1, bal2, balance_line, cnt_fork_success, black_list_matches

    fork_exclude_text = ''
    v = True

    if get_prop('junior_team_exclude'):
        if re.search('(u\d{2}|\(жен\)|\(ж\)|\(р\)|\(рез\)|\(.*\d{2}\)|-студ.)', name_rus.lower()):
            fork_exclude_text = fork_exclude_text + 'Вилка исключена по названию команд: ' + name_rus + '\n'

        if re.search('(u\d{2}|\(w\)|\(r\)|\(res\)|\(Reserves\)|-stud\.)', name.lower()):
            fork_exclude_text = fork_exclude_text + 'Вилка исключена по названию команд: ' + name + '\n'

    if not bet_type_is_work(key):
        fork_exclude_text = fork_exclude_text + 'Вилка исключена, т.к. я еще не умею работать с этой ставкой: ' + str(key) + ')\n'

    deff_limit = 3
    if deff_max > deff_limit:
        fork_exclude_text = fork_exclude_text + 'Вилка исключена, т.к. deff_max (' + str(deff_max) + ' > ' + str(deff_limit) + ')\n'

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

    # Если баланс меньше 30% то берем плече только с коэф-м меньше 1,5
    if bal1 <= balance_line and k1 >= 1.3:
        fork_exclude_text = fork_exclude_text + 'Вилка ' + str(round((1 - L) * 100, 2)) \
                            + '% исключена: баланс БК Олимп меньше 30%, а коэф-т >= 1.3 (' + str(k1) + ')\n'
    elif bal2 <= balance_line and k2 >= 1.3:
        fork_exclude_text = fork_exclude_text + 'Вилка ' + str(round((1 - L) * 100, 2)) \
                            + '% исключена: баланс БК фонбет меньше 30%, а коэф-т >= 1.3 (' + str(k2) + ')\n'

    if bk1_score != bk2_score:
        fork_exclude_text = fork_exclude_text + 'Вилка ' \
                            + str(round((1 - L) * 100, 2)) \
                            + '% исключена т.к. счет не совпадает: olimp(' + bk1_score + ') fonbet(' + bk2_score + ')\n'

    # Больше 43 минуты и не идет перерыв и это 1 период
    if 43.0 < float(minute) and not time_break_fonbet and period == 1:
        fork_exclude_text = \
            fork_exclude_text + 'Вилка ' + str(round((1 - L) * 100, 2)) + '% исключена т.к. идет ' + str(minute) + \
            ' минута матча и это не перерыв и это не 2-й период \n'

    if float(minute) > 88.0:
        fork_exclude_text = \
            fork_exclude_text + 'Вилка ' + str(round((1 - L) * 100, 2)) + '% исключена т.к. идет ' + str(minute) + ' минута матча \n'

    # Вилка живет достаточно
    long_livers = int(get_prop('fork_life_time'))
    if live_fork < long_livers:
        fork_exclude_text = fork_exclude_text + 'Вилка ' + str(round((1 - L) * 100, 2)) + \
                            '% исключена т.к. живет меньше ' + str(long_livers) + ' сек. \n'

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


def set_statistics(key, err_bk1, err_bk2, fork_info=None, init=False):
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
        msg_str = 'Кол-во ошибок больше допустимого (' + str(max_fail) + '), работа завершена.'
        raise MaxFail(msg_str)

    max_fork = int(get_prop('max_fork'))
    if len(cnt_fork_success) >= max_fork:
        msg_str = 'Кол-во успешно просталвенных вилок достигнуто (' + str(max_fork) + '), работа завершена.'
        raise MaxFork(msg_str)


def go_bets(wag_ol, wag_fb, total_bet, key, deff_max, vect1, vect2, sc1, sc2):
    global bal1, bal2, cnt_fail, cnt_fork_success

    olimp_bet_type = str(key.split('@')[-2])
    fonbet_bet_type = str(key.split('@')[-1])
    # Проверяем ставили ли мы на этот матч, пока в ручную

    L = ((1 / float(wag_ol['factor'])) + (1 / float(wag_fb['value'])))
    cur_proc = round((1 - L) * 100, 2)

    amount_olimp, amount_fonbet = get_sum_bets(wag_ol['factor'], wag_fb['value'], total_bet)

    if __name__ == '__main__':
        wait_sec = 0
        prnt('Wait sec: ' + str(wait_sec))

        real_wait = wait_sec + deff_max
        prnt('Real wait sec: ' + str(real_wait))
        if real_wait > 9:
            prnt('Fork is lost: real wait > 9')
            return False

        time.sleep(wait_sec)
        with Manager() as manager:
            obj = manager.dict()

            recheck_o = Process(target=get_kof_olimp, args=(obj, wag_ol['event'], olimp_bet_type))
            recheck_fb = Process(target=get_kof_fonbet, args=(obj, wag_fb['event'], int(wag_fb['factor']), wag_fb['param']))

            recheck_fb.start()
            recheck_o.start()

            recheck_fb.join()
            recheck_o.join()

            deff_max = max(obj['olimp_time_req'], obj['fonbet_time_req'])

            prnt('deff_max: ' + str(deff_max) + ', O ' +
                 olimp_bet_type + ': ' + str(wag_ol['factor']) + ' -> ' + str(obj['olimp']) + '| F ' +
                 fonbet_bet_type + ': ' + str(wag_fb['value']) + ' -> ' + str(obj['fonbet']))

            wag_fb['value'] = obj['fonbet']
            wag_ol['value'] = obj['olimp']
            wag_ol['factor'] = obj['olimp']

            # Проверяем что полученный коэфициент больше 1
            if float(obj['olimp']) > 1 < float(obj['fonbet']):

                # пересчетаем суммы ставок
                amount_olimp, amount_fonbet = get_sum_bets(float(obj['olimp']), float(obj['fonbet']), total_bet)

                # Выведем текую доходность вилки
                prnt('cur proc: ' + str(cur_proc) + '%')
                L = (1 / float(obj['olimp'])) + (1 / float(obj['fonbet']))
                new_proc = round((1 - L) * 100, 2)
                change_proc = round(new_proc - cur_proc, 2)
                prnt('new proc: ' + str(new_proc) + '%, change: ' + str(change_proc))

                if check_l(L) == '' or (DEBUG and bet_type_is_work(key)):

                    is_recheck = True
                    fork_id = int(time.time())
                    fork_info = {
                        fork_id: {
                            'olimp': {
                                'id': wag_ol['event'],
                                'kof': wag_ol['factor'],
                                'amount': amount_olimp,
                                'reg_id': 0,
                                'bet_type': olimp_bet_type,
                                'balance': bal1,
                                'time_bet': 0,
                                'vector': vect1,
                                'new_bet_sum': 0,
                                'err': 'ok'
                            },
                            'fonbet': {
                                'id': wag_fb['event'],
                                'kof': wag_fb['value'],
                                'amount': amount_fonbet,
                                'reg_id': 0,
                                'bet_type': fonbet_bet_type,
                                'balance': bal2,
                                'time_bet': 0,
                                'bet_delay': 0,
                                'vector': vect2,
                                'new_bet_sum': 0,
                                'err': 'ok'
                            },
                        }
                    }
                else:
                    is_recheck = False

                prnt('Recheck fork result: ' + str(is_recheck))
                if is_recheck is False:
                    prnt('Fork is lost =(')
                    return False
            else:
                prnt('One of the coefficients is not available')
                return False

        if DEBUG:
            amount_olimp = 30
            amount_fonbet = 30
            # return False

        shared = dict()

        shared['olimp'] = {
            'opposite': 'fonbet',
            'amount': amount_olimp,
            'wager': wag_ol,
            'bet_type': olimp_bet_type,
            'vect': vect1,
            'sc1': sc1,
            'sc2': sc2,
            'cur_total': sc1 + sc2,
            'side_team': '1'
        }
        shared['fonbet'] = {
            'opposite': 'olimp',
            'amount': amount_fonbet,
            'wager': wag_fb,
            'bet_type': fonbet_bet_type,
            'vect': vect2,
            'sc1': sc1,
            'sc2': sc2,
            'cur_total': sc1 + sc2,
            'side_team': '2',
            'max_bet': 0
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

        fork_info[fork_id]['olimp']['new_bet_sum'] = shared['olimp'].get('new_bet_sum')
        fork_info[fork_id]['fonbet']['new_bet_sum'] = shared['fonbet'].get('new_bet_sum')

        fork_info[fork_id]['olimp']['reg_id'] = shared['olimp'].get('reg_id')
        fork_info[fork_id]['fonbet']['reg_id'] = shared['fonbet'].get('reg_id')

        fork_info[fork_id]['olimp']['err'] = str(shared.get('olimp_err', 'ok'))
        fork_info[fork_id]['fonbet']['err'] = str(shared.get('fonbet_err', 'ok'))

        fork_info[fork_id]['fonbet']['max_bet'] = shared['fonbet'].get('max_bet')
        # CHECK FATAL ERROR
        if shared.get('fonbet_err_fatal') or shared.get('olimp_err_fatal'):
            msg_str = 'Обнаружена фатальная ошибка:' + \
                      str(shared.get('fonbet_err_fatal')) + \
                      str(shared.get('olimp_err_fatal')) + '), работа завершена.'
            raise MaxFail(msg_str)

        # CALC/SET STATISTICS
        set_statistics(key, shared.get('olimp_err'), shared.get('fonbet_err'), fork_info=fork_info[fork_id])
        get_statistics()
        msg_errs = ' ' + shared.get('olimp_err') + shared.get('fonbet_err')
        if not 'BkOppBetError'.lower() in msg_errs.lower():
            # SAVE INFO
            save_fork(fork_info)
        # CHECK FAILS
        check_statistics()
        # WAITING AFTER BET
        sleep_post_work = 30
        prnt('Ожидание ' + str(sleep_post_work) + ' сек.')
        time.sleep(sleep_post_work)

        return True


def run_client():
    global server_forks
    global shutdown
    global server_ip

    try:
        if 'Windows' == platform.system() or DEBUG:
            conn = http.client.HTTPConnection(server_ip, 80, timeout=3.51)
        else:
            conn = http.client.HTTPConnection(server_ip, 80, timeout=6)

        while True:
            if shutdown:
                err_str = 'Основной поток завершен и run_client тоже.'
                conn.close()
                raise Shutdown(err_str)
            conn.request('GET', '')
            rs = conn.getresponse()
            data = rs.read().decode('utf-8')
            data_json = json.loads(data)
            server_forks = data_json
            time.sleep(0.5)
    except Shutdown as e:
        prnt(str(e.__class__.__name__) + ' - ' + str(e))
        raise Shutdown(e)
    except Exception as e:
        prnt('better: ' + str(e.__class__.__name__) + ' - ' + str(e))
        server_forks = {}
        conn.close()
        time.sleep(10)
        return run_client()


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
balance_line = 0  # (bal1 + bal2) / 2 / 100 * 60
time_get_balance = datetime.datetime.now()
time_live = datetime.datetime.now()

cnt_fail = 0
black_list_matches = []
cnt_fork_success = []
printed = False
last_fork_time = 0
wait_before_start = 15

# wag_fb:{'event': '12797479', 'factor': '921', 'param': '', 'score': '0:0', 'value': '2.35'}
# wag_fb:{'apid': '1144260386:45874030:1:3:-9999:3:NULL:NULL:1', 'factor': '1.66', 'sport_id': 1, 'event': '45874030'}

if __name__ == '__main__':
    try:
        Account.update(pid=os.getpid(), time_start=round(time.time())).where(Account.key == KEY).execute()
        prnt('DEBUG: ' + str(DEBUG))

        time_get_balance = datetime.datetime.now()
        time_live = datetime.datetime.now()

        if DEBUG:
            bal1 = 20000
            bal2 = 20000
            # Общая масксимальная сумма ставки
            total_bet = round(0.10 * (bal1 + bal2))
        else:
            bal1 = OlimpBot(OLIMP_USER).get_balance()  # Баланс в БК1
            bal2 = FonbetBot(FONBET_USER).get_balance()  # Баланс в БК2
            total_bet = int(get_prop('summ'))

        balance_line = (bal1 + bal2) / 2 / 100 * 30
        if not DEBUG:
            server_ip = get_prop('server_ip')
        else:
            server_ip = get_prop('server_ip_test')

        MIN_L = float(get_prop('min_l'))
        prnt(' ')
        prnt('ID аккаунта: ' + str(ACC_ID))
        prnt('IP-адрес сервера: ' + server_ip + ':80')
        prnt('Баланс в БК Олимп: ' + str(bal1))
        prnt('Баланс в БК Фонбет: ' + str(bal2))

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
            if total_bet < 400:
                err_msg = 'Обшая сумма ставки, должна превышать 400 руб.'
                raise ValueError(err_msg)
            else:
                prnt('Общая сумма ставки: ' + str(total_bet))
                prnt('Отклонение от общей суммы ставки (в %): ' + str(random_summ_proc))
                total_bet_min = int(total_bet - (total_bet * int(random_summ_proc) / 100))
                total_bet_max = int(total_bet + (total_bet * int(random_summ_proc) / 100))
                prnt('Полученный диапазон общей суммы ставки (в валюте): ' + str(total_bet_min) + '-' + str(total_bet_max))

        prnt('Пропускаем ставки > 1.2, если баланс БК меньше: ' + str(balance_line))
        prnt('Время жизни вилки от (сек.): ' + str(int(get_prop('fork_life_time'))))
        prnt('Исключаем низшие команды: ' + str(get_prop('junior_team_exclude')))
        prnt('Работаю максимум (ч.): ' + str(int(get_prop('work_hour'))))
        prnt('Работаю до (ч.): ' + str(int(get_prop('work_hour_end'))))
        prnt('Максимальное кол-во успешных вилок: ' + str(int(get_prop('max_fork'))))
        prnt('Максимально допустимое количество ошибок/выкупов: ' + str(int(get_prop('max_fail'))))
        prnt('Минимальный профит вилки от (%): ' + str(round((1 - MIN_L) * 100, 3)))
        prnt('Жесткая ставка второго плеча: ' + str(get_prop('hard_bet_right')))
        prnt(' ')
        try:
            with open(str(ACC_ID) + '_id_forks.txt') as f:
                for line in f:
                    js = json.loads(line)
                    last_time_temp = 0
                    for key, val in js.items():
                        bet_key = str(val.get('olimp', {}).get('id')) + '@' + str(val.get('fonbet', {}).get('id')) + '@' + \
                                  val.get('olimp', {}).get('bet_type') + '@' + val.get('fonbet', {}).get('bet_type')
                        set_statistics(bet_key, val.get('olimp').get('err'), val.get('fonbet').get('err'))

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

        time.sleep(wait_before_start)

        if Account.select().where(Account.key == KEY).get().work_stat == 'start':
            send_message_bot(USER_ID, str(ACC_ID) + ': Начал работу', ADMINS)

        while Account.select().where(Account.key == KEY).get().work_stat == 'start':
            # print(str(Account.select().where(Account.key == KEY).get().id) + ': ' + Account.select().where(Account.key == KEY).get().work_stat)
            balance_line = (bal1 + bal2) / 2 / 100 * 30

            shutdown_minutes = 60 * (60 * int(get_prop('work_hour')))  # секунды * на кол-во (60*1) - это час
            if (datetime.datetime.now() - time_live).total_seconds() > shutdown_minutes:
                msg_str = 'Прошло ' + str(round(shutdown_minutes / 60 / 60, 2)) + ' ч., я завершил работу'
                raise Shutdown(msg_str)

            cur_hour = int(datetime.datetime.now().strftime('%H'))
            if cur_hour < 12:
                shutdown_hour = int(get_prop('work_hour_end'))
                if cur_hour >= shutdown_hour:
                    msg_str = 'Роботаю до:{} ч., сейчас:{} ч., я завершил работу'.format(shutdown_hour, cur_hour)
                    raise Shutdown(msg_str)

            # Обновление баланса каждые 30 минут
            ref_balace = 30
            if (datetime.datetime.now() - time_get_balance).total_seconds() > (60 * ref_balace):
                prnt(' ')
                prnt('Прошло больше ' + str(ref_balace) + ' минут, пора обновить балансы:')
                time_get_balance = datetime.datetime.now()
                bal1 = OlimpBot(OLIMP_USER).get_balance()  # Баланс в БК1
                bal2 = FonbetBot(FONBET_USER).get_balance()  # Баланс в БК2

            # Показываем каждые 30 минут
            cur_min = int(datetime.datetime.now().strftime('%M'))
            ref_min = 30
            if cur_min % ref_min == 0 and not printed:
                prnt(' ')
                msg_str = str(ACC_ID) + ': ' + \
                          'Кол-во успешно проставленных вилок: ' + str(len(cnt_fork_success)) + '\n' + \
                          'Кол-во вилок с выкупами: ' + str(cnt_fail) + '\n' + \
                          'Работаю еще: ' + str(
                    round((shutdown_minutes - (datetime.datetime.now() - time_live).total_seconds()) / 60 / 60, 2)) + ' ч.'
                prnt(msg_str)
                printed = True

                send_message_bot(USER_ID, msg_str)
            elif cur_min % ref_min != 0 and printed:
                printed = False

            if server_forks:
                go_bet_key = {}
                l = 0.0
                go_bet_json = {}
                for key, val_json in server_forks.items():
                    # print(json.dumps(val_json, ensure_ascii=False))
                    l_temp = val_json.get('l', 0.0)

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
                    period = val_json.get('period')
                    time_last_upd = val_json.get('time_last_upd', 1)
                    live_fork_total = val_json.get('live_fork_total', 0)
                    live_fork = val_json.get('live_fork', 0)

                    deff_olimp = round(float(time.time() - float(val_json.get('time_req_olimp', 0))))
                    deff_fonbet = round(float(time.time() - float(val_json.get('time_req_fonbet', 0))))
                    deff_max = max(0, deff_olimp, deff_fonbet)

                    bk1_bet_json = val_json.get('kof_olimp')
                    bk2_bet_json = val_json.get('kof_fonbet')

                    bk1_hist = bk1_bet_json.get('hist', {})
                    bk2_hist = bk2_bet_json.get('hist', {})

                    k1 = bk1_bet_json.get('factor', 0)
                    k2 = bk2_bet_json.get('value', 0)

                    vect1 = bk1_bet_json.get('vector')
                    vect2 = bk2_bet_json.get('vector')

                    try:
                        info = key + ': ' + name + ' ' + \
                               k1_type + '=' + str(k1) + '/' + \
                               k2_type + '=' + str(k2) + ', ' + \
                               v_time + ' (' + str(minute) + ') ' + \
                               score + ' ' + str(pair_math) + \
                               ', live_fork: ' + str(live_fork) + \
                               ', live_fork_total: ' + str(live_fork_total) + \
                               ', max deff: ' + str(deff_max)
                    except Exception as e:
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        err_str = str(e) + ' ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                        prnt('better: ' + err_str)

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

                    if vect1 and vect2:
                        if (0.0 <= l < l_temp or DEBUG) and deff_max < 10 and k1 > 0 < k2:
                            round_bet = int(get_prop('round_fork'))
                            total_bet = round(randint(total_bet_min, total_bet_max) / round_bet) * round_bet

                            bet1, bet2 = get_sum_bets(k1, k2, total_bet, 'hide')
                            # Проверим вилку на исключения
                            if check_fork(key, l_temp, k1, k2, live_fork, bk1_score, bk2_score,
                                          minute, time_break_fonbet, period, name, name_rus, deff_max, info) or DEBUG:
                                go_bet_key.clear()
                                l = l_temp
                                go_bet_json = val_json
                                go_bet_key[key] = {
                                    'go_bet_json': go_bet_json,
                                    'total_bet': total_bet,
                                    'go_bet_key': go_bet_key,
                                    'deff_max': deff_max,
                                    'vect1': vect1,
                                    'vect2': vect2,
                                    'sc1': sc1,
                                    'sc2': sc2,
                                    'info': info
                                }
                        elif deff_max >= 10:
                            pass
                    else:
                        prnt('Вектор направления коф-та не определен: VECT1=' + str(vect1) + ', VECT2=' + str(vect2))
                if go_bet_key:
                    for key, val in go_bet_key.items():
                        prnt(' ')
                        prnt('Go bets: ' + key + ' ' + val.get('info'))
                        fork_success = go_bets(val.get('go_bet_json').get('kof_olimp'), val.get('go_bet_json').get('kof_fonbet'),
                                               val.get('total_bet'), key, val.get('deff_max'), val.get('vect1'),
                                               val.get('vect2'), val.get('sc1'), val.get('sc2'))
                        break
                    total_bet = int(get_prop('summ'))
                    go_bet_key.clear()
                    server_forks.clear()
                else:
                    pass
            else:
                pass
            time.sleep(0.5)
        Account.update(pid=0).where(Account.key == KEY).execute()
        shutdown = True

    except (Shutdown, MaxFail, MaxFork) as e:
        shutdown = True
        prnt(' ')
        prnt(str(e))
        send_message_bot(USER_ID, str(ACC_ID) + ': ' + str(e))

        last_fork_time_diff = int(time.time()) - last_fork_time
        wait_before_exp = max(60 * 60 * 2 - last_fork_time_diff, 0)
        msg_str = str(ACC_ID) + ': ' + \
                  str(last_fork_time_diff) + ' секунд прошло с момента последней ставки\nОжидание ' + \
                  str(wait_before_exp / 60) + ' минут, до выгрузки'

        prnt(msg_str)
        send_message_bot(USER_ID, msg_str)

        time.sleep(wait_before_exp)
        export_hist(OLIMP_USER, FONBET_USER)

    except Exception as e:
        shutdown = True
        exc_type, exc_value, exc_traceback = sys.exc_info()
        err_str = str(e) + ' ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        err_str = str(ACC_ID) + ': Возникла ошибка! ' + str(e.__class__.__name__) + ' - ' + str(err_str)
        prnt(err_str)
        send_message_bot(USER_ID, str(e), ADMINS)

    finally:
        msg_str = str(ACC_ID) + ': Завершил работу'
        send_message_bot(USER_ID, msg_str, ADMINS)
        Account.update(pid=0, work_stat='stop', time_stop=round(time.time())).where(Account.key == KEY).execute()
