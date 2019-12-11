# coding:utf-8
from requests import Session
from json import loads, dumps
import os
import cfscrape
import requests
import datetime
import statistics
import copy
from math import floor

from db_model import Account, Properties
import sys

DEBUG = False
MINUTE_COMPLITE = 88
VSTR_OLD = ''
VSTR_OLD_CL = ''

package_dir = os.path.dirname(__file__)
dtOld = datetime.datetime.now()

csv_head = [
    'ID', 'time', 'event_type', 'pre_fb_kof', 'pre_o_kof', 'pre_fb_sum', 'pre_o_sum',
    'fb_id', 'o_id', 'fb_time', 'o_time', 'fb_kof', 'o_kof', 'fb_sum_bet', 'o_sum_bet',
    'fb_profit', 'o_profit', 'fb_result', 'o_result', 'fb_name', 'o_name', 'fb_status',
    'o_sum_sale', 'f_kof_type', 'o_kof_type', 'order_bet', 'fb_vector', 'ol_vector', 'first_bet_in', 'total_first', 'fb_time_bet', 'ol_time_bet',
    'fb_new_bet_sum', 'ol_new_bet_sum', 'fb_bal', 'ol_bal', 'fb_max_bet', 'maxbet_fact', 'fb_max_bet_fact', 'fb_bet_delay', 'fb_is_top', 'fb_is_hot', 'fork_slice', 'cnt_act_acc', 'time_type', 'fork_time',
    'fork_time_max', 'min_proc', 'max_proc',
    'user_id', 'fb_bk_type', 'group_limit_id', 'live_fork', 'team_type', 'summ_min',
    'cur_proc', 'fisrt_proc', 'fb_err', 'ol_err'
]

opposition = {
    '1ТБ': '1ТМ',
    '1ТМ': '1ТБ',
    '2ТБ': '2ТМ',
    '2ТМ': '2ТБ',
    'ТБ': 'ТМ',
    'ТМ': 'ТБ',
    '1ТБ1': '1ТМ1',
    '1ТМ1': '1ТБ1',
    '1ТБ2': '1ТМ2',
    '1ТМ2': '1ТБ2',
    '2ТБ1': '2ТМ1',
    '2ТМ1': '2ТБ1',
    '2ТБ2': '2ТМ2',
    '2ТМ2': '2ТБ2',
    'ТБ1': 'ТМ1',
    'ТМ1': 'ТБ1',
    'ТБ2': 'ТМ2',
    'ТМ2': 'ТБ2',
    # '1УГЛТБ': '1УГЛТМ',
    # '1УГЛТМ': '1УГЛТБ',
    # '2УГЛТБ': '2УГЛТМ',
    # '2УГЛТМ': '2УГЛТБ',
    # 'УГЛТБ': 'УГЛТМ',
    # 'УГЛТМ': 'УГЛТБ',
    'П1': 'П2Н',
    'П2': 'П1Н',
    'П1Н': 'П2',
    'П2Н': 'П1',
    'Н': '12',
    '12': 'Н',
    '1КЗ1': '1КНЗ1',
    '1КНЗ1': '1КЗ1',
    '1КЗ2': '1КНЗ2',
    '1КНЗ2': '1КЗ2',
    '2КЗ1': '2КНЗ1',
    '2КНЗ1': '2КЗ1',
    '2КЗ2': '2КНЗ2',
    '2КНЗ2': '2КЗ2',
    'КЗ1': 'КНЗ1',
    'КНЗ1': 'КЗ1',
    'КЗ2': 'КНЗ2',
    'КНЗ2': 'КЗ2',
    'ОЗД': 'ОЗН',
    'ОЗН': 'ОЗД',
    'ННД': 'ННН',
    'ННН': 'ННД'
}

KEY = ''
ACC_ID = 0
START_SLEEP = ''
USER_ID = 0
PROPERTIES = {}
ACCOUNTS = {}
try:
    ACC_ID = sys.argv[2]
except:
    pass

try:
    START_SLEEP = sys.argv[3]
except:
    pass

if ACC_ID:
    acc_info = Account.select().where(Account.id == ACC_ID)
    KEY = acc_info.get().key
    if acc_info:
        print('___________________INIT____________________')
        ACCOUNTS = loads(acc_info.get().accounts.replace('`', '"'))
        pror_dict = {}
        for prop in acc_info.get().properties:
            pror_dict.update({prop.key: prop.val})
        PROPERTIES = copy.deepcopy(pror_dict)

        PROXIES = loads(acc_info.get().proxies.replace('`', '"'))
        ACC_ID = acc_info.get().id
        USER_ID = acc_info.get().user_id


def prnt(vstr=None, hide=None, to_cl=False, type_='bet'):
    global VSTR_OLD

    if type_ in ('bet', 'fork'):
        if vstr != VSTR_OLD:
            VSTR_OLD = vstr
            if vstr:
                global dtOld
                global ACC_ID

                if not hide:
                    dtDeff = round((datetime.datetime.now() - dtOld).total_seconds())
                    strLog = datetime.datetime.now().strftime('%d %H:%M:%S.%f ') + '[' + str(dtDeff).rjust(2,
                                                                                                           '0') + ']    ' + str(
                        ACC_ID) + ': ' + str(vstr)
                    print(strLog)
                    dtOld = datetime.datetime.now()
                    Outfile = open(str(ACC_ID) + '_client.log', "a+", encoding='utf-8')
                    Outfile.write(strLog + '\n')
                    Outfile.close()
                else:
                    strLog = datetime.datetime.now().strftime('%d %H:%M:%S.%f ') + '    ' + str(vstr)
                    Outfile = open(str(ACC_ID) + '_client_hide.log', "a+", encoding='utf-8')
                    Outfile.write(strLog + '\n')
                    Outfile.close()

                if to_cl:
                    strLog = datetime.datetime.now().strftime('%d %H:%M:%S.%f ') + '    ' + str(vstr)
                    Outfile = open(str(ACC_ID) + '_to_cl_' + type_ + '.log', "a+", encoding='utf-8')
                    Outfile.write(strLog + '\n')
                    Outfile.close()


prnt('KEY: ' + str(KEY))


def int_to_str(n: int) -> str:
    return '{:,}'.format(round(n)).replace(',', ' ')


def build_menu(buttons,
               n_cols,
               header_buttons=None,
               footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


def get_kof_from_serv(bk_name, match_id, kof, server_ip=''):
    if server_ip == '':
        server_ip = get_prop('server_ip', '')
        if server_ip == '':
            server_ip = '80.87.193.55'
    url_get_kof = 'http://' + server_ip + ':8888/' + bk_name + '/' + str(match_id) + '/' + kof
    answer = ''
    try:
        res = requests.get(url=url_get_kof, verify=False, timeout=1)
        answer = res.text
    except Exception as e:
        answer = str(e)
    prnt('url_get_kof: ' + str(url_get_kof) + ', answer: ' + str(answer))
    return answer


def get_sum_bets(k1, k2, total_bet, round_fork=5, hide=False):
    if get_prop('round_fork'):
        round_fork = int(get_prop('round_fork'))

    k1 = float(k1)
    k2 = float(k2)
    prnt('k1:{}, k2:{}'.format(k1, k2), hide)
    l = (1 / k1) + (1 / k2)

    # Округление проставления в БК1 происходит по правилам математики
    bet_1 = floor(total_bet / (k1 * l) / round_fork) * round_fork
    bet_2 = total_bet - bet_1

    prnt('L: ' + str(round((1 - l) * 100, 2)) + '% (' + str(l) + ') ', hide)
    prnt('bet1: ' + str(bet_1) + ', bet2: ' + str(bet_2) + '|' + ' bet_sum: ' + str(bet_1 + bet_2), hide)

    return bet_1, bet_2


def floor_to_2(num: float):
    return floor(num / 100) * 100.


def get_new_sum_bets(bk1, bk2, max_bet, bal2, hide=False, round_fork=5):
    if get_prop('round_fork'):
        round_fork = int(get_prop('round_fork'))
    l = 1 / bk1 + 1 / bk2
    total_bet = round((max_bet * bk1 * l) / round_fork) * round_fork
    total_bet_max = (max_bet + bal2)
    if total_bet > total_bet_max:
        total_bet = total_bet_max
        prnt('Error, total_bet > total_bet_max, {}>{}'.format(total_bet, total_bet_max), hide)
    sum_bk1, sum_bk2 = get_sum_bets(bk1, bk2, total_bet, round_fork, hide)
    if sum_bk2 > bal2:
        prnt('Error, sum_bk2 > bal2, {}>{}, sum_bk1: {}, max_bet: {}'.format(sum_bk2, bal2, sum_bk1, max_bet), hide)
        sum_bk2, sum_bk1 = get_new_sum_bets(bk2, bk1, bal2, max_bet, hide, round_fork)
    return sum_bk1, sum_bk2


def get_vector(bet_type, sc1=None, sc2=None):
    def raise_err(VECT, sc1, sc2):
        if sc1 is None or sc2 is None and VECT != '':
            raise ValueError('ERROR: sc1 or sc2 not defined!')

    D = 'DOWN'
    U = 'UP'
    VECT = ''

    if sc1:
        sc1 = int(sc1)
    if sc2:
        sc2 = int(sc2)

    if [t for t in ['ТБ', 'КЗ', 'ОЗД', 'ННД'] if t in bet_type]:
        return U
    if [t for t in ['ТМ', 'КНЗ', 'ОЗН', 'ННН'] if t in bet_type]:
        return D

    # Или добавлять ретурн в каждую из веток,
    # но те типы что по длинне написания больше,  должны быть выше

    if 'П1Н' in bet_type:
        raise_err(VECT, sc1, sc2)
        if sc1 >= sc2:
            return D
        else:
            return U

    if 'П2Н' in bet_type:
        raise_err(VECT, sc1, sc2)
        if sc1 <= sc2:
            return D
        else:
            return U

    if '12' in bet_type:
        raise_err(VECT, sc1, sc2)
        if sc1 != sc2:
            return D
        else:
            return U

    if 'П1' in bet_type:
        raise_err(VECT, sc1, sc2)
        if sc1 > sc2:
            return D
        else:
            return U

    if 'П2' in bet_type:
        raise_err(VECT, sc1, sc2)
        if sc1 < sc2:
            return D
        else:
            return U

    if 'Н' in bet_type:
        raise_err(VECT, sc1, sc2)
        if sc1 == sc2:
            return D
        else:
            return U

    raise ValueError('Error: vector not defined!')


def invetsion_vect(vect: str):
    vect = vect.upper()
    if vect == 'UP':
        return 'DOWN'
    elif vect == 'DOWN':
        return 'UP'


def normalized_vector(vect1: str, k1: float, vect2: str, k2: float):
    vect1 = vect1.upper()
    vect2 = vect2.upper()
    if (vect1 == vect2) or (vect1 == '' and vect2 == ''):
        if k1 > k2:
            return 'DOWN', 'UP'
        elif k2 > k1:
            return 'UP', 'DOWN'
        else:
            return vect1, vect2
    else:
        return vect1, vect2


def find_max_mode(list1):
    list_table = statistics._counts(list1)
    len_table = len(list_table)

    if len_table == 1:
        max_mode = statistics.mode(list1)
    else:
        new_list = []
        for i in range(len_table):
            new_list.append(list_table[i][0])
        max_mode = max(new_list)
    return max_mode


def write_file(filename, s):
    with open(os.path.join(os.path.dirname(__file__), filename), 'w') as file:
        file.write(s)


def read_file(filename):
    try:
        with open(os.path.join(os.path.dirname(__file__), filename), 'r') as file:
            return file.read()
    except:
        pass


def get_account_info(bk=None, param=None):
    global ACCOUNTS
    if bk and param:
        return ACCOUNTS.get(bk, {}).get(param, None)
    if bk and not param:
        return ACCOUNTS.get(bk)
    else:
        return ACCOUNTS


def get_prop(param, set_default=None):
    global PROPERTIES
    return PROPERTIES.get(param.upper(), set_default)


def serv_log(filename: str, vstr: str, hide=False):
    prnts(vstr, hide)
    Outfile = open(filename + '.log', "a+", encoding='utf-8')
    Outfile.write(vstr + '\n')
    Outfile.close()


def client_log(filename: str, vstr: str):
    prnt(vstr)
    Outfile = open(filename + '.log', "a+", encoding='utf-8')
    Outfile.write(vstr + '\n')
    Outfile.close()


def prnts(vstr=None, hide=None):
    if vstr:
        global dtOld
        dtDeff = round((datetime.datetime.now() - dtOld).total_seconds())
        strLog = datetime.datetime.now().strftime('%d %H:%M:%S.%f ') + '[' + str(dtDeff).rjust(2, '0') + ']    ' + \
                 str(vstr)
        if not hide:
            dtOld = datetime.datetime.now()
            print(strLog)

        Outfile = open('server.log', "a+", encoding='utf-8')
        Outfile.write(strLog + '\n')
        Outfile.close()


def save_fork(fork_info):
    prnt('SAVE FORK:' + str(fork_info))
    f = open(str(ACC_ID) + '_id_forks.txt', 'a+', encoding='utf-8')
    f.write(dumps(fork_info) + '\n')


class LoadException(Exception):
    pass


def check_status(status_code):
    if status_code != 200:
        raise LoadException("Site is not responding, status code: {}".format(status_code))


def check_status_with_resp(resp, olimp=None):
    if (resp.status_code != 200 and olimp is None) \
            or (olimp is not None and resp.status_code not in (200, 400, 417, 406, 403, 500, 401)):
        raise LoadException("Site is not responding, status code: {}".format(resp.status_code))
    if '149-ФЗ'.lower() in resp.text.lower():
        raise LoadException('Прокси был заблокирован на основании 149-ФЗ, нужно сменить прокси. ' + str(resp.url))


def get_session_with_proxy(name):
    global PROXIES
    session_proxies = PROXIES[name]
    session = requests.Session()  # cfscrape.create_scraper(delay=10)  #
    session.proxies = session_proxies
    # scraper = cfscrape.create_scraper(sess=session)
    return session


def get_proxies():
    try:
        global PROXIES
        return PROXIES
    except:
        D = dict()
        # D = {
        #     # 'fonbet': {'http': '192.168.1.143:8888', 'https': '192.168.1.143:8888'},
        #     'olimp': {'http': '', 'https': ''}
        # }
        return D
