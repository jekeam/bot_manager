import urllib3

from time import time, sleep
from os import path
from json import dumps
import sys
import traceback
from threading import Thread
import hmac
from hashlib import sha512
import copy
import re

from retry_requests import requests_retry_session, requests_retry_session_post

from meta_ol import ol_url_api, ol_payload, ol_headers, get_xtoken_bet
from meta_fb import fb_payload, fb_payload_bet, get_random_str, get_dumped_payload, get_urls, get_common_url
from meta_fb import fb_headers, get_new_bets_fonbet, payload_req, payload_coupon_sum, payload_coupon_sell, fb_payload_max_bet
from meta_fb import payload_sell_check_result
from utils import prnt, write_file, read_file, get_account_info, get_proxies, get_prop, get_new_sum_bets
from fork_recheck import get_olimp_info, get_fonbet_info

from exceptions import SessionNotDefined, BkOppBetError, NoMoney, BetError, SessionExpired, SaleError
from exceptions import CouponBlocked, BetIsLost

if get_prop('debug'):
    DEBUG = True
else:
    DEBUG = False

# disable: InsecureRequestWarning: Unverified HTTPS request is being made.
# See: https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warningsInsecureRequestWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

package_dir = path.dirname(path.abspath(__file__))


def run_bets(shared: dict):
    ps = []
    for bk_name, bk_container in shared.items():
        bk = Thread(target=BetManager, args=(shared, bk_name, bk_container))
        ps.append(bk)
        bk.start()

    for bk in ps:
        bk.join()


class BetManager:

    def __init__(self, shared: dict, bk_name: str, bk_container: dict):

        self.bk_name = bk_name
        self.bk_container = bk_container
        self.wager = bk_container['wager']
        self.created_fork = bk_container.get('created', '')
        self.bk_name_opposite = bk_container['opposite']
        self.vector = bk_container.get('wager', {})['vector']

        # if self.vector == 'DOWN':
        #     self.flex_bet = False
        # else:
        #     self.flex_bet = True
        self.hard_bet = True
        self.override_bet = True

        self.msg_err = self.bk_name + '. {}, err: {}'
        self.msg = self.bk_name + '. {}, msg: {}'

        self.total_bet = bk_container.get('bet_total')
        self.side_team = bk_container['side_team']
        self.bet_type = bk_container['bet_type']
        self.dop_stat = dict()
        # dynamic params
        self.cur_sc = None
        self.cur_sc_main = None
        self.cur_total = None
        self.cur_total_new = None
        self.cur_half = None
        self.cur_val_bet = bk_container.get('wager', {}).get('value')
        self.val_bet_stat = self.cur_val_bet
        self.val_bet_old = self.cur_val_bet
        self.cur_minute = None
        self.total_stock = None

        self.strat_name = 'main'

        self.account = get_account_info(self.bk_name)
        self.timeout = 20
        self.match_id = None
        self.reg_id = None
        self.reqId = None
        self.reqIdSale = None
        self.payload = None
        self.sum_bet = bk_container.get('amount')
        self.sum_bet_stat = self.sum_bet
        self.sum_sell = None

        self.sum_sell_divider = 1
        if self.bk_name == 'fonbet':
            self.sum_sell_divider = 100

        self.cashout_allowed = None
        self.attempt_login = 1
        self.attempt_bet = 1
        self.attempt_sale = 1
        self.sleep_bet = 3.51
        self.sleep_add = 0
        self.proxies = self.get_proxy()
        self.server_olimp = '08'
        self.server_fb = {}
        self.mirror = self.account.get('mirror')

        self.session_file = 'session.' + self.bk_name
        self.session = {}

        self.time_start = round(time())

        self.sale_profit = 0
        self.bet_profit = 0

        self.max_bet = 0
        self.min_bet = 0

        self.first_bet_in = get_prop('first_bet_in', 'auto')

        self.time_req = 0
        self.time_req_opp = 0

        err_msg = ''

        bk_work = ('olimp', 'fonbet')
        if self.bk_name not in bk_work or self.bk_name_opposite not in bk_work:
            err_msg = 'bk not defined: bk1={}, bk2={}'.format(self.bk_name, self.bk_name_opposite)

        elif not self.mirror:
            err_msg = 'mirror not defined: {}'.format(self.mirror)

        if err_msg != '':
            err_str = self.msg_err.format(sys._getframe().f_code.co_name, err_msg)
            prnt(err_str)
            raise ValueError(err_str)

        # self.manager(shared)
        shared[self.bk_name]['self'] = self
        self.bet_simple(shared)

    def wait_sign_in_opp(self, shared: dict):
        sign_stat = shared.get('sign_in_' + self.bk_name_opposite, 'wait')

        push_ok = False
        while sign_stat == 'wait':
            if not push_ok:
                prnt(self.msg.format(
                    sys._getframe().f_code.co_name,
                    self.bk_name + ' wait stat sign in from ' +
                    self.bk_name_opposite + ': ' + str(sign_stat) + '(' + str(type(sign_stat)) + ')'))
                push_ok = True
            sign_stat = shared.get('sign_in_' + self.bk_name_opposite, 'wait')
            sleep(0.1)

        if sign_stat not in ('ok', 'wait'):
            err_str = self.msg_err.format(sys._getframe().f_code.co_name, self.bk_name + ' get error from ' + self.bk_name_opposite + ': ' + sign_stat)
            raise BkOppBetError(err_str)

        prnt(self.msg.format(sys._getframe().f_code.co_name, self.bk_name + ' get sign in from ' + self.bk_name_opposite + ': ' + str(sign_stat) + '(' + str(type(sign_stat)) + ')'))

    def wait_maxbet_check(self, shared: dict):
        maxbet_stat = shared.get('maxbet_in_' + self.bk_name_opposite, 'wait')

        push_ok = False
        while maxbet_stat == 'wait':
            if not push_ok:
                prnt(self.msg.format(
                    sys._getframe().f_code.co_name,
                    self.bk_name + ' wait maxbet from ' +
                    self.bk_name_opposite + ': ' + str(maxbet_stat)))
                push_ok = True
            maxbet_stat = shared.get('maxbet_in_' + self.bk_name_opposite, 'wait')
            sleep(0.1)
            self.opposite_stat_get(shared)

        prnt(self.msg.format(sys._getframe().f_code.co_name, self.bk_name + ' get maxbet from ' + self.bk_name_opposite + ': ' + str(maxbet_stat)))

    def opposite_stat_get(self, shared: dict):

        opposite_stat = str(shared.get(self.bk_name_opposite + '_err', 'ok'))

        if opposite_stat != 'ok':
            err_str = self.msg_err.format(sys._getframe().f_code.co_name, self.bk_name + ' get error from ' + self.bk_name_opposite + ': ' + opposite_stat)
            raise BkOppBetError(err_str)

        prnt(self.msg.format(
            sys._getframe().f_code.co_name,
            self.bk_name + ' get status bet in from ' +
            self.bk_name_opposite + ': ' + str(opposite_stat) + '(' + str(type(opposite_stat)) + ')'))

    def opposite_stat_wait(self, shared: dict):
        # if not DEBUG:
        prnt(self.msg.format(sys._getframe().f_code.co_name, self.bk_name + ' wait status bet in from ' + self.bk_name_opposite))

        opp_stat = None
        while opp_stat is None:
            opp_stat = shared.get(self.bk_name_opposite + '_err')
            sleep(0.1)

        prnt(self.msg.format(
            sys._getframe().f_code.co_name,
            self.bk_name + ' after wait, get status bet in from ' +
            self.bk_name_opposite + ': ' + str(opp_stat) + '(' + str(type(opp_stat)) + ')'))

    def opposite_wait(self, shared: dict, event: str):
        prnt(self.msg.format(sys._getframe().f_code.co_name, self.bk_name + ' wait ' + event + ' in from ' + self.bk_name_opposite))

        opp_stat = None
        sec = 0
        while opp_stat is None:
            opp_stat = shared.get(self.bk_name_opposite + '_' + event)
            s_cnt = 0.1
            sleep(s_cnt)
            sec = sec + s_cnt

        prnt(self.msg.format(sys._getframe().f_code.co_name,
                             self.bk_name + ' after wait ' + str(sec) + ' sec., get ' + event + ' in from ' + self.bk_name_opposite + ': ' + str(opp_stat)))

    def recalc_sum_by_maxbet(self, shared: dict):
        cur_bet_sum = self.max_bet * int(get_prop('proc_by_max', 90)) / 100

        prnt(' ')
        prnt(self.msg.format(
            sys._getframe().f_code.co_name,
            'RECALС BY MAX-BET: {}->{}({}%)'.format(self.max_bet, cur_bet_sum, get_prop('proc_by_max', '0'))
        ))
        # recalc sum bets
        self_opp_data = shared[self.bk_name_opposite].get('self', {})
        sum1, sum2 = get_new_sum_bets(self.cur_val_bet, self_opp_data.cur_val_bet, cur_bet_sum, True)
        prnt(self.msg.format(sys._getframe().f_code.co_name, 'new sum, ' + self.bk_name + ': ' + str(sum1) + ', ' + self.bk_name_opposite + ': ' + str(sum2)))
        if sum1 < self.min_bet or sum2 < self.min_bet:
            raise BetIsLost('Сумма одной из ставок после пересчета меньше min_bet: ' + str(self.min_bet))
        else:
            self.sum_bet, self_opp_data.sum_bet = sum1, sum2
            self.sum_bet_stat, self_opp_data.sum_bet_stat = sum1, sum2

    def recheck(self, shared):
        prnt(' ')
        prnt(self.msg.format(sys._getframe().f_code.co_name, 'RECHECK FORK'))
        match_id = self.bk_container.get('wager', {})['event']
        param = self.bk_container.get('wager', {}).get('param')
        bet_id = int(self.bk_container.get('wager', {}).get('factor'))

        if self.bk_name == 'fonbet':
            try:
                self.cur_val_bet, self.cur_sc_main, self.time_req, self.dop_stat = get_fonbet_info(match_id, bet_id, param, self.bet_type)
            except BetIsLost as e:
                raise BetIsLost(e)
            except AttributeError as e:
                err_msg = 'recheck err (' + str(e.__class__.__name__) + '): ' + str(e)
                raise BetIsLost(err_msg)
            except Exception as e:
                err_msg = 'recheck err (' + str(e.__class__.__name__) + '): ' + str(e)
                prnt(self.msg_err.format(sys._getframe().f_code.co_name, err_msg))

        if self.bk_name == 'olimp':
            try:
                self.cur_val_bet, self.cur_sc, self.time_req = get_olimp_info(match_id, self.bet_type, proxies=self.proxies)
            except Exception as e:
                err_msg = 'recheck err (' + str(e.__class__.__name__) + '): ' + str(e)
                prnt(self.msg_err.format(sys._getframe().f_code.co_name, err_msg))

        prnt(self.msg.format(sys._getframe().f_code.co_name,
                             'get kof ' + self.bk_name + ': ' + str(self.val_bet_stat) + ' -> ' + str(self.cur_val_bet) + ', time req.:' + str(self.time_req)))

        shared[self.bk_name + '_recheck'] = 'done'
        self.opposite_wait(shared, 'recheck')

        opp_cur_val_bet = shared[self.bk_name_opposite].get('self', {}).cur_val_bet
        if self.cur_val_bet > 0 < opp_cur_val_bet:
            l = (1 / self.cur_val_bet) + (1 / opp_cur_val_bet)
            l_first = (1 / self.val_bet_stat) + (1 / shared[self.bk_name_opposite].get('self', {}).val_bet_stat)

            min_proc = float(get_prop('min_proc').replace(',', '.'))
            min_l = 1 - (min_proc / 100)

            prnt(' ')
            cur_proc = str(round((1 - l) * 100, 3))
            first_proc = str(round((1 - l_first) * 100, 3))
            min_proc = str(round((1 - min_l) * 100, 3))
            prnt(self.msg.format(sys._getframe().f_code.co_name, 'min l: ' + str(min_l) + ', l: ' + str(l_first) + ' -> ' + str(l) + ', proc: ' + str(first_proc) + ' -> ' + cur_proc))
        else:
            raise BetIsLost('Один из коф-в заблокирован: ' + self.bk_name + '(' + str(self.cur_val_bet) + '), ' + self.bk_name_opposite + '(' + str(opp_cur_val_bet) + ')')

        if l > min_l:
            raise BetIsLost('Вилка ' + str(l) + ' (' + cur_proc + '%), беру вилки только >= ' + min_proc + '%')

        prnt(' ')
        prnt(self.msg.format(sys._getframe().f_code.co_name, 'RECALC SUM'))
        self.recalc_sum_bet(shared)

    def bet_simple(self, shared: dict):

        def sale_opp(e, shared):
            self.opposite_stat_wait(shared)
            self.opposite_stat_get(shared)
            prnt(self.msg.format(sys._getframe().f_code.co_name, 'Ошибка при проставлении ставки в ' + self.bk_name + ', делаю выкуп ставки в ' + self.bk_name_opposite))

            self_opp = shared[self.bk_name_opposite].get('self', {})

            while True:
                try:
                    if self.attempt_sale > 50:
                        self.attempt_sale = 1
                        raise BetIsLost('To many attempt sale!')
                    else:
                        self.attempt_sale = self.attempt_sale + 1
                    self_opp.sale_bet(shared)
                    break
                except (SaleError, CouponBlocked) as e:
                    prnt(self.msg.format(sys._getframe().f_code.co_name,
                                         'Ошибка: ' + e.__class__.__name__ + ' - ' + str(e) + '. Пробую проставить и пробую выкупить еще! (' + str(self.attempt_sale) + ')'))
                    sleep(15)

        def bet_done(shared):

            shared[self.bk_name]['new_bet_sum'] = self.sum_bet
            shared[self.bk_name]['new_bet_kof'] = self.cur_val_bet

            if not shared[self.bk_name].get('time_bet'):
                shared[self.bk_name]['time_bet'] = round(time() - self.time_start)
                prnt(self.msg.format(sys._getframe().f_code.co_name, 'Завершил работу в ' + self.bk_name))
            shared[self.bk_name]['balance'] = self.session.get('balance')

        try:
            try:
                self.sign_in(shared)
                self.wait_sign_in_opp(shared)

                self.recheck(shared)

                if self.created_fork == '' and 'created' in self.first_bet_in:
                    raise BetIsLost('Создалтель вилки не определен: ' + str(self.created_fork))

                if self.first_bet_in == 'created':
                    if self.created_fork == self.bk_name:
                        self.first_bet_in = self.bk_name
                    else:
                        self.first_bet_in = self.bk_name_opposite

                if self.first_bet_in == 'notcreator':
                    if self.created_fork == self.bk_name:
                        self.first_bet_in = self.bk_name_opposite
                    else:
                        self.first_bet_in = self.bk_name

                prnt(self.msg.format(
                    sys._getframe().f_code.co_name,
                    'FIRST BET IN: {}, prop:{}, bk_name:{}, bk_opp_name:{}'.format(self.first_bet_in, get_prop('first_bet_in', 'auto'), self.bk_name, self.bk_name_opposite)
                ))

                # if self.bk_name == 'fonbet':
                recalc_sum_if_maxbet = get_prop('sum_by_max', 'выкл')

                if get_prop('check_max_bet', 'выкл') == 'вкл' or recalc_sum_if_maxbet == 'вкл':
                    if self.bk_name == 'fonbet':
                        prnt(' ')
                        prnt(self.msg.format(sys._getframe().f_code.co_name, 'CHECK MAX-BET, BEFORE BET'))
                        try:
                            self.check_max_bet(shared)
                        except BetIsLost as e:
                            if recalc_sum_if_maxbet == 'вкл':
                                self.recalc_sum_by_maxbet(shared)
                            else:
                                raise BetIsLost(e)
                        shared['maxbet_in_' + self.bk_name] = 'ok'
                    else:
                        self.wait_maxbet_check(shared)
                        self.opposite_stat_get(shared)

                if (self.first_bet_in == 'auto' and self.vector == 'UP') or self.bk_name_opposite == self.first_bet_in:
                    self.opposite_stat_wait(shared)
                    self.opposite_stat_get(shared)
                if self.first_bet_in == 'parallel':
                    pass

                self.bet_place(shared)
                bet_done(shared)
            except BetError as e:
                shared[self.bk_name + '_err'] = str(e.__class__.__name__) + ': ' + str(e)
                prnt(e)

                self.opposite_stat_wait(shared)
                self.opposite_stat_get(shared)

                prnt(self.msg.format(sys._getframe().f_code.co_name, 'Ошибка при проставлении ставки в ' + self.bk_name + ', передаю его завершающему'))
                self.bet_safe(shared)

            except BkOppBetError as e:
                raise BkOppBetError(e)
            except (BetIsLost, NoMoney, SessionExpired, Exception) as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                err_msg = 'Ошибка: ' + str(e.__class__.__name__) + ' - ' + str(e) + '. ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                shared[self.bk_name + '_err'] = err_msg
                prnt(err_msg)

                self.opposite_stat_wait(shared)
                self.opposite_stat_get(shared)

                if shared.get(self.bk_name_opposite, {}).get('reg_id'):
                    sale_opp(e, shared)
                    raise ValueError(err_msg)
                else:
                    raise BkOppBetError(err_msg)
        except BkOppBetError as e:
            # В обоих БК ошибки, выкидываем вилку
            shared[self.bk_name + '_err'] = str(e.__class__.__name__) + ': ' + str(e)
            shared[self.bk_name_opposite + '_err'] = str(e.__class__.__name__) + ': ' + str(e)
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            err_msg = 'Неизвестная ошибка: ' + str(e.__class__.__name__) + ' - ' + str(e) + '. ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
            err_str = self.msg_err.format(sys._getframe().f_code.co_name, err_msg)
            prnt(err_str)
        finally:
            bet_done(shared)

    def set_param(self):

        def set_strategy(strat_name: str, side: str):
            self.side_bet = side
            self.strat_name = strat_name

        self.side_bet = None
        self.side_bet_half = None

        bet_type_sub = re.sub('\(.*\)', '', self.bet_type)

        msk_match_per = '^\d\w.*\d$'
        msk_team = '^\w.*\d$'
        msk_period = '^\d\w.*'

        bet_type_exclude = bet_type_sub != '12'

        bet_depends = 'Уставки есть привязкa:'
        if re.match(msk_match_per, bet_type_sub):
            self.side_bet = bet_type_sub[-1]
            self.side_bet_helf = bet_type_sub[0:1]
            bet_depends = bet_depends + ' команада=' + self.side_bet + ' и период=' + self.side_bet_half
        elif re.match(msk_team, bet_type_sub) and bet_type_exclude:
            self.side_bet = bet_type_sub[-1]
            bet_depends = bet_depends + ' команада=' + self.side_bet
        elif re.match(msk_period, bet_type_sub) and bet_type_exclude:
            self.side_bet_half = bet_type_sub[0:1]
            bet_depends = bet_depends + ' период=' + self.side_bet_half
        elif 'КЗ' in bet_type_sub or 'КНЗ' in bet_type_sub:
            set_strategy('КЗ', re.sub('\D', '', bet_type_sub))
            bet_depends = bet_depends + ' команада=' + self.side_bet
        elif bet_type_sub[0:1] == 'П':
            set_strategy(bet_type_sub[0:1], bet_type_sub[1:2])
            bet_depends = bet_depends + ' команада=' + self.side_bet
        else:
            bet_depends = 'Ставка не привязана ни к периоду, ни к команде'
            if 'ОЗ' in bet_type_sub:
                set_strategy('ОЗ', None)
        prnt(self.msg.format(sys._getframe().f_code.co_name, bet_depends))

    def recalc_sum_bet(self, shared):
        self_opp_data = shared[self.bk_name_opposite].get('self', {})
        k_opp = self_opp_data.cur_val_bet
        sum_opp = self_opp_data.sum_bet_stat

        if self.cur_val_bet and self.val_bet_old != self.cur_val_bet:
            prnt(' ')
            prnt(self.msg.format(sys._getframe().f_code.co_name, 'RECALC SUM BET'))

            # round_rang = int(get_prop('round_fork'))
            self.sum_bet = round(self.sum_bet_stat * self.val_bet_stat / self.cur_val_bet / 5) * 5

            total_new_sum = self.sum_bet + sum_opp

            bk1_profit = sum_opp * k_opp - total_new_sum
            bk2_profit = self.sum_bet * self.cur_val_bet - total_new_sum
            self.bet_profit = round((bk1_profit + bk2_profit) / 2)

            prnt(self.msg.format(
                sys._getframe().f_code.co_name,
                'Пересчет суммы ставки: {}->{}({}:{}/{}) [k: {}->{}, k_opp:{}, sum_opp:{}]'.
                    format(self.sum_bet_stat, self.sum_bet, self.bet_profit, bk1_profit, bk2_profit, self.val_bet_stat, self.cur_val_bet, k_opp, sum_opp)))

    def bet_safe(self, shared: dict):

        def data_update():
            prnt(' ')
            prnt(self.msg.format(sys._getframe().f_code.co_name, 'UPDATE DATA'))
            match_id = self.bk_container.get('wager', {})['event']
            param = self.bk_container.get('wager', {}).get('param')
            bet_id = int(self.bk_container.get('wager', {}).get('factor'))

            if self.bk_name == 'fonbet' or self.bk_name_opposite == 'fonbet':
                try:
                    if self.bk_name_opposite == 'fonbet':
                        self_opp = shared[self.bk_name_opposite].get('self', {})
                        match_id_opp = self_opp.bk_container.get('wager', {})['event']
                        bet_id_opp = int(self_opp.bk_container.get('wager', {}).get('factor'))
                        param_opp = self_opp.bk_container.get('wager', {}).get('param')
                        bet_type_opp = self_opp.bk_container.get('bet_type')
                        k_val, self.cur_sc_main, self.time_req_opp, self.dop_stat = get_fonbet_info(match_id_opp, bet_id_opp, param_opp, bet_type_opp)
                    elif self.bk_name == 'fonbet':
                        self.cur_val_bet, self.cur_sc_main, self.time_req, self.dop_stat = get_fonbet_info(match_id, bet_id, param, self.bet_type)

                    prnt(self.msg.format(sys._getframe().f_code.co_name, 'get data from fonbet: ' + dumps(self.dop_stat, ensure_ascii=False)))
                except BetIsLost as e:
                    raise BetIsLost(e)
                except AttributeError as e:
                    err_msg = 'recheck err (' + str(e.__class__.__name__) + '): ' + str(e)
                    raise BetIsLost(err_msg)
                except Exception as e:
                    err_msg = 'recheck err (' + str(e.__class__.__name__) + '): ' + str(e)
                    prnt(self.msg_err.format(sys._getframe().f_code.co_name, err_msg))

            if self.bk_name == 'olimp':
                try:
                    self.cur_val_bet, self.cur_sc, self.time_req = get_olimp_info(match_id, self.bet_type, proxies=self.proxies)
                except Exception as e:
                    err_msg = 'recheck err (' + str(e.__class__.__name__) + '): ' + str(e)
                    prnt(self.msg_err.format(sys._getframe().f_code.co_name, err_msg))

            try:
                if self.side_bet == '1':
                    self.cur_total = int(self.cur_sc_main.split(':')[0])
                elif self.side_bet == '2':
                    self.cur_total = int(self.cur_sc_main.split(':')[1])
                else:
                    self.cur_total = sum(map(int, self.cur_sc_main.split(':')))
            except AttributeError as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                prnt(
                    self.msg.format(
                        sys._getframe().f_code.co_name,
                        'Ошибка парсинга счета: (' + e.__class__.__name__ + ') ' + str(e) + ' ' + str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                    )
                )

            if not self.cur_total_new:
                self.cur_total_new = self.cur_total

            self.cur_half = self.dop_stat['period']
            self.cur_minute = self.dop_stat['minutes']

            if self.cur_total is not None and self.total_bet is not None:
                self.total_stock = self.total_bet - self.cur_total

            vector = self.dop_stat.get('vector')
            if vector:
                if self.bk_name_opposite == 'fonbet':
                    if vector == 'UP':
                        vector = 'DOWN'
                    else:
                        vector = 'UP'

            if vector != self.vector:
                prnt(self.msg.format(sys._getframe().f_code.co_name, 'Вектор изменен: {} -> {}'.format(self.vector, vector)))
                self.vector = vector

            prnt(self.msg.format(
                sys._getframe().f_code.co_name,
                'Получил данные: bet_type:{}, vector:{}, total:{}, half:{}, val_bet:{}({}),minute:{}, sc_main:{}, sc:{}'.
                    format(self.bet_type, self.vector, self.cur_total, self.cur_half, self.cur_val_bet, self.val_bet_stat, self.cur_minute, self.cur_sc_main, self.cur_sc)))

            prnt(self.msg.format(sys._getframe().f_code.co_name, 'Запас тотала: total_stock:{}, total_bet:{}, cur_total:{}'.format(self.total_stock, self.total_bet, self.cur_total)))

            # CHECK SUM SELL
            prnt(' ')
            prnt(self.msg.format(sys._getframe().f_code.co_name, 'GET SUM SELL'))
            self_opp_data = shared[self.bk_name_opposite].get('self', {})
            k_opp = self_opp_data.cur_val_bet
            sum_opp = self_opp_data.sum_bet_stat
            try:
                self_opp_data.get_sum_sell()
            except CouponBlocked as e:
                prnt(self.msg.format(sys._getframe().f_code.co_name, 'Ошибка: ' + e.__class__.__name__ + ' - ' + str(e)))

            # CALC PROFIT IF EXISTS SUMM SELL
            self.sale_profit = 0
            if self_opp_data.sum_sell:
                prnt(' ')
                prnt(self.msg.format(sys._getframe().f_code.co_name, 'CALC PROFIT IF EXISTS SUMM SELL'))
                self.sale_profit = (self_opp_data.sum_sell / self_opp_data.sum_sell_divider) - sum_opp

                if self.sale_profit > 0:
                    err_str = self.msg_err.format(sys._getframe().f_code.co_name, 'Сумма выкупа больше чем ставка на ' + str(self.sale_profit) + ', пробую выкупить')
                    prnt(err_str)
                    raise BetIsLost(err_str)
                else:
                    prnt(self.msg.format(sys._getframe().f_code.co_name, 'Потеря при выкупе: ' + str(self.sale_profit)))
            else:
                prnt(self.msg.format(sys._getframe().f_code.co_name, 'Сумма выкупа неизвестна'))

            self.recalc_sum_bet(shared)

            if self.sum_bet_stat >= self.sum_bet:
                prnt(self.msg.format(sys._getframe().f_code.co_name, 'Сумма ставки не изменилась или уменьшилась, делаем ставку'))
            elif self_opp_data.sum_sell and self.sale_profit > self.bet_profit:
                # sell bet
                err_str = 'Выкуп за: {} выгоднее, чем возможные потери после перерасчета: {}'.format(self.sale_profit, self.bet_profit)
                prnt(err_str)
                raise BetIsLost(err_str)
            else:
                prnt(self.msg.format(sys._getframe().f_code.co_name, 'Ставка: {} выгоднее выкупа: {}, работаю дальше'.format(self.bet_profit, self.sale_profit)))

            prnt(self.msg.format(sys._getframe().f_code.co_name, 'Коф-т ставки должен быть изменен: {}->{}'.format(self.val_bet_stat, self.cur_val_bet)))
            self.val_bet_old = self.cur_val_bet
            # override abt
            if self.override_bet:

                if self.bk_name == 'olimp':
                    self.wager['factor'] = self.cur_val_bet
                elif self.bk_name == 'fonbet':
                    self.wager['value'] = self.cur_val_bet

                prnt(self.msg.format(sys._getframe().f_code.co_name, 'Коф-т для ставки в ' + self.bk_name + ': ' + str(self.cur_val_bet)))

        self.set_param()  # set self.side_bet, self.side_bet_half
        self.time_start = round(int(time()))
        self.time_left = -1

        prnt(self.msg.format(sys._getframe().f_code.co_name, 'Завершающий принял работу'))

        prnt(self.msg.format(sys._getframe().f_code.co_name, 'Жесткая ставка второго плеча: ' + str(self.hard_bet)))
        prnt(self.msg.format(sys._getframe().f_code.co_name, 'Переопределять изначальный коэф-т при его изменении: ' + str(self.override_bet)))

        is_go = True
        cnt_attempt_sale = 5
        while is_go:
            try:
                # UPDATE DATA
                data_update()

                # UPDATE TIME LEFT
                prnt(' ')
                prnt(self.msg.format(sys._getframe().f_code.co_name, 'UPDATE TIME LEFT'))

                if self.vector == 'UP':
                    self.timeout_left = float(60 * 10)
                    if DEBUG:
                        self.timeout_left = float(45)
                elif self.vector == 'DOWN':
                    self.timeout_left = round(float(60 * 2.5))
                    if DEBUG:
                        self.timeout_left = float(20)

                cur_time = round(int(time()))
                self.time_left = (self.time_start + self.timeout_left) - cur_time

                prnt(self.msg.format(sys._getframe().f_code.co_name, 'Vector: {}, время на работу(сек): {} из {}'.format(self.vector, self.time_left, self.timeout_left)))

                # Пока убрал фичю, тут можно делать запас тотола
                if self.time_left < 0:
                    prnt(self.msg.format(
                        sys._getframe().f_code.co_name,
                        'timeout: time_start:{}, time_left:{}, cur_time:{}'.format(self.time_start, self.time_left, cur_time)))
                    raise BetIsLost('Время проставления истекло!')

                # CHECK FOR LOSS
                prnt(' ')
                prnt(self.msg.format(sys._getframe().f_code.co_name, 'CHECK FOR LOSS'))
                if self.side_bet_half == '1' and self.cur_minute >= 43.0:
                    err_str = 'Bet is lost: side_bet_half={} and cur_minute many 43({})'.format(self.side_bet_half, self.cur_minute)
                    prnt(err_str)
                    raise BetIsLost(err_str)
                elif self.cur_minute >= 88.0:
                    err_str = 'Bet is lost: side_bet_half={} and cur_minute many 88({})'.format(self.side_bet_half, self.cur_minute)
                    prnt(err_str)
                    raise BetIsLost(err_str)

                # CHECK: SCORE CHANGED?
                if self.cur_total != self.cur_total_new:
                    self.cur_total_new = self.cur_total
                    prnt(self.msg.format(sys._getframe().f_code.co_name, 'SCORE CHANGED!'))
                    # strategy definition
                    if self.strat_name in ('П'):
                        if self.cur_minute >= 80:
                            err_str = 'Strategy ' + self.strat_name + ': bet is lost, cur_minute many 80({})'.format(self.cur_minute)
                            prnt(err_str)
                            raise BetIsLost(err_str)
                    # strategy definition
                    elif self.strat_name == 'КЗ':
                        try:
                            if self.side_bet == '1' and int(self.cur_sc_main.split(':')[0]) > 0 or \
                                    self.side_bet == '2' and int(self.cur_sc_main.split(':')[1]) > 0:
                                err_str = 'Strategy ' + self.strat_name + ': bet is lost, side_bet:{}, score:{}'.format(self.side_bet, self.cur_sc_main)
                                prnt(err_str)
                                raise BetIsLost(err_str)
                        except AttributeError as e:
                            exc_type, exc_value, exc_traceback = sys.exc_info()
                            prnt(
                                self.msg.format(
                                    sys._getframe().f_code.co_name,
                                    'Ошибка парсинга счета: (' + e.__class__.__name__ + ') ' + str(e) + ' ' +
                                    str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                                )
                            )
                    elif self.strat_name == 'ОЗ':
                        if self.cur_total > 0:
                            err_str = 'Strategy ' + self.strat_name + ': bet is lost, score:{}, cur_total:{}'.format(self.cur_sc_main, self.cur_total)
                            prnt(err_str)
                            raise BetIsLost(err_str)
                    # strategy definition
                    else:
                        if self.total_stock is not None and self.total_stock <= 0:
                            if self.vector == 'UP':
                                err_str = 'Strategy total: total_bet < cur_total ({} < {}), bet lost'.format(self.total_bet, self.cur_total)
                                prnt(err_str)
                                raise BetIsLost(err_str)
                            elif self.vector == 'DOWN':
                                prnt(self.msg.format(sys._getframe().f_code.co_name, 'Greetings! You won, brain!'))
                                is_go = False
                        elif self.total_stock is None:
                            raise BetIsLost('Totals not found!')

                if self.cur_val_bet:
                    prnt(self.msg.format(sys._getframe().f_code.co_name, 'Пробую сделать ставку'))
                    self.bet_place(shared)
                    is_go = False
                else:
                    prnt(self.msg.format(sys._getframe().f_code.co_name, 'Ставка не возможна'))

            except BetIsLost as e:
                if shared.get(self.bk_name + '_err', 'err') != 'ok':
                    err_msg = str(e.__class__.__name__) + ': ' + str(e)
                    shared[self.bk_name + '_err'] = err_msg
                    prnt(self.msg.format(sys._getframe().f_code.co_name,
                                         'Ошибка при проставлении ставки в ' + self.bk_name +
                                         ', делаю выкуп ставки в ' + self.bk_name_opposite))
                    try:
                        shared[self.bk_name_opposite].get('self', {}).sale_bet(shared)
                        is_go = False
                        break
                    except CouponBlocked as e:
                        prnt(self.msg.format(
                            sys._getframe().f_code.co_name,
                            'Ошибка: ' + e.__class__.__name__ + ' - ' + str(e) + '. Пробую проставить и пробую выкупить еще! (' + str(self.attempt_sale) + ')'
                        ))
                        sleep(5)
                        self.attempt_sale = self.attempt_sale + 1
                    if (self.total_stock is not None and self.total_stock <= 0) or self.attempt_sale > 500:
                        self.attempt_sale = 1
                        raise BetIsLost(err_msg)

            except SessionExpired as e:
                prnt(self.msg.format(
                    sys._getframe().f_code.co_name,
                    'Ошибка: (' + e.__class__.__name__ + ') ' + str(e) + ' ' +
                    str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback))) +
                    '. Делаю повторный вход'))
                self.sign_in(shared)

            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                prnt(self.msg.format(
                    sys._getframe().f_code.co_name,
                    'Ошибка: (' + e.__class__.__name__ + ') ' + str(e) + ' ' +
                    str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback))) +
                    '. Работаю еще: ' + str(self.time_left) + ' сек'))
            finally:
                sleep(5)

    def sign_in(self, shared: dict):

        try:
            if self.bk_name == 'olimp':
                # # sign_in
                # sleep(10)
                # try:
                #     1 / 0
                # except Exception as e:
                #     #raise SessionNotDefined(e)
                #     raise ValueError(e)

                payload = copy.deepcopy(ol_payload)
                payload.update({'login': self.account['login'], 'password': self.account['password']})

                headers = copy.deepcopy(ol_headers)
                headers.update(get_xtoken_bet(payload))
                headers.update({'X-XERPC': '1'})

                prnt(self.msg.format(sys._getframe().f_code.co_name, 'rq: ' + str(payload) + ' ' + str(headers)), 'hide')
                resp = requests_retry_session_post(
                    # ol_url_api.format(self.server_olimp, 'autorize'),
                    ol_url_api.format('autorize'),
                    headers=headers,
                    data=payload,
                    verify=False,
                    timeout=self.timeout,
                    proxies=self.proxies)
                prnt(self.msg.format(sys._getframe().f_code.co_name, 'rs: ' + str(resp.status_code) + ' ' + str(resp.text.strip())), 'hide')
                data_js = resp.json()

                err_code = data_js.get('error', {}).get('err_code', 0)
                if err_code == 404 and self.attempt_login <= 6:
                    sleep(2)
                    self.attempt_login += 1
                    return self.sign_in(shared)

                data = data_js.get('data', {})

                self.session['session'] = data.get('session')
                self.session['balance'] = float(dict(data).get('s'))
                self.session['currency'] = dict(data).get('cur')

            elif self.bk_name == 'fonbet':

                # # sign_in
                # sleep(5)
                # try:
                #     1 / 0
                # except Exception as e:
                #     #raise SessionNotDefined(e)
                #     raise ValueError(e)

                fb_payload['platform'] = 'mobile_android'
                fb_payload['clientId'] = self.account['login']

                payload = copy.deepcopy(fb_payload)
                payload['random'] = get_random_str()
                payload['sign'] = 'secret password'

                msg = get_dumped_payload(payload)
                sign = hmac.new(key=self.account['password'].encode(), msg=msg.encode(), digestmod=sha512).hexdigest()
                payload['sign'] = sign
                data = get_dumped_payload(payload)

                self.server_fb = get_urls(self.mirror, self.proxies)
                url, self.timeout = get_common_url(self.server_fb)

                prnt(self.msg.format(sys._getframe().f_code.co_name, 'rq: ' + str(data)), 'hide')

                resp = requests_retry_session_post(
                    url.format('login'),
                    headers=fb_headers,
                    data=data,
                    verify=False,
                    timeout=self.timeout,
                    proxies=self.proxies)
                prnt(self.msg.format(sys._getframe().f_code.co_name, 'rs: ' + str(resp.status_code) + ' ' + str(resp.text.strip())), 'hide')
                res = resp.json()

                self.session['session'] = res.get('fsid')
                self.session['balance'] = float(res.get('saldo'))
                self.session['currency'] = res.get('currency').get('currency')

            if not self.session.get('session'):
                raise SessionNotDefined(self.msg_err.format(sys._getframe().f_code.co_name, 'session_id not defined'))

            prnt(self.msg.format(sys._getframe().f_code.co_name, 'session: ' + str(self.session['session'])))
            prnt(self.msg.format(sys._getframe().f_code.co_name, 'balance: ' +
                                 str(self.session.get('balance')) + ' ' +
                                 str(self.session.get('currency'))))
            # write_file(self.session_file, self.session['session'].strip())

            shared['sign_in_' + self.bk_name] = 'ok'

        except SessionNotDefined as e:
            shared['sign_in_' + self.bk_name] = str(e.__class__.__name__) + ': ' + str(e)
            raise SessionNotDefined(e)
        except Exception as e:
            shared['sign_in_' + self.bk_name] = str(e.__class__.__name__) + ': ' + str(e)

            exc_type, exc_value, exc_traceback = sys.exc_info()
            err_msg = 'unknown err(' + str(e.__class__.__name__) + '): ' + str(e) + '. ' + \
                      str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))

            err_str = self.msg_err.format(sys._getframe().f_code.co_name, err_msg)
            raise ValueError(err_str)

    def bet_place(self, shared: dict):

        # # for test
        # if self.bk_name == 'fonbet':
        #     sleep(15)
        self.opposite_stat_get(shared)

        cur_bal = self.session.get('balance')

        if cur_bal:
            if cur_bal < self.sum_bet:
                err_str = self.msg_err.format(
                    sys._getframe().f_code.co_name,
                    self.bk_name + ' balance ({}) < sum_bet({})'.format(str(cur_bal), str(self.sum_bet)))
                raise NoMoney(err_str)

        if self.bk_name == 'olimp':

            # # bet_place
            # if self.vector == 'UP':
            #     sleep(20)
            #     try:
            #         1 / 0
            #     except Exception as e:
            #         raise BetError(e)

            payload = copy.deepcopy(ol_payload)

            save_any = 3
            if self.hard_bet:
                save_any = 2

            payload.update({
                'coefs_ids': '[["{apid}",{factor},1]]'.format(apid=self.wager.get('apid'), factor=self.wager.get('factor')),
                'sport_id': self.wager.get('sport_id'),
                'sum': self.sum_bet,
                'save_any': save_any,
                'fast': 1,
                'any_handicap': 1,
                'session': self.session['session']
            })
            # Принимать с изменёнными коэффициентами:
            # save_any: 1 - никогда, 2 - при повышении, 3 - всегда

            # Принимать с измененными тоталами/форами:
            # any_handicap: 1 - Нет, 2 - Да

            headers = copy.deepcopy(ol_headers)
            headers.update(get_xtoken_bet(payload))

            prnt(self.msg.format(sys._getframe().f_code.co_name, 'rq: ' + str(payload) + ' ' + str(headers)), 'hide')
            self.opposite_stat_get(shared)
            resp = requests_retry_session().post(
                # ol_url_api.format(self.server_olimp, 'basket/fast'),
                ol_url_api.format('basket/fast'),
                headers=headers,
                data=payload,
                verify=False,
                timeout=self.timeout,
                proxies=self.proxies)
            prnt(self.msg.format(sys._getframe().f_code.co_name, 'rs: ' + str(resp.status_code) + ' ' + str(resp.text.strip())), 'hide')
            res = resp.json()

            err_code = res.get('error', {}).get('err_code')
            err_msg = res.get('error', {}).get('err_desc')

            if err_code == 404 and self.attempt_bet <= 6:
                sleep(2)
                self.attempt_bet += 1
                return self.bet_place(shared)

            self.check_responce(err_msg)

            if err_code == 0:
                self.match_id = self.wager['event']

                self.get_cur_max_bet_id()

                shared[self.bk_name]['reg_id'] = self.reg_id

                prnt(self.msg.format(sys._getframe().f_code.co_name, 'bet successful, reg_id: ' + str(self.reg_id)))
                shared[self.bk_name + '_err'] = 'ok'

            elif 'Такой исход не существует' in err_msg:
                raise BetIsLost(err_msg)

            elif 'максимальная ставка' in err_msg:
                raise BetIsLost(err_msg)

            elif res.get('data') is None:
                err_str = self.msg_err.format(sys._getframe().f_code.co_name, err_msg)
                raise BetError(err_str)

        elif self.bk_name == 'fonbet':

            # # bet_place
            # if self.vector == 'UP':
            #     sleep(4)
            #     try:
            #         1 / 0
            #     except Exception as e:
            #         raise BetError(e)

            if not self.server_fb:
                self.server_fb = get_urls(self.mirror, self.proxies)

            url, self.timeout = get_common_url(self.server_fb)

            payload = copy.deepcopy(fb_payload_bet)
            headers = copy.deepcopy(fb_headers)

            payload['client'] = {'id': self.account['login']}
            payload['coupon']['amount'] = self.sum_bet

            if self.wager.get('param'):
                payload['coupon']['bets'][0]['param'] = int(self.wager['param'])
            payload['coupon']['bets'][0]['score'] = self.wager['score']
            payload['coupon']['bets'][0]['value'] = float(self.wager['value'])
            payload['coupon']['bets'][0]['event'] = int(self.wager['event'])
            payload['coupon']['bets'][0]['factor'] = int(self.wager['factor'])
            payload['fsid'] = self.session['session']
            payload['clientId'] = self.account['login']

            self.payload = copy.deepcopy(payload)

            self.check_max_bet(shared)

            self.attempt_get_req_id = 5
            while True:
                if self.attempt_get_req_id <= 0:
                    err_str = 'get_request_id: no data found'
                    raise BetIsLost(err_str)
                try:
                    self.attempt_get_req_id = self.attempt_get_req_id - 1
                    self.get_request_id()
                    break
                except Exception as e:
                    prnt(self.msg_err.format(sys._getframe().f_code.co_name, 'get_request_id err: ' + str(e) + ', replay'))
                    sleep(3)

            self.payload['requestId'] = self.reqId

            if self.hard_bet:
                self.payload['coupon']['flexBet'] = 'up'

            self.opposite_stat_get(shared)
            prnt(self.msg.format(sys._getframe().f_code.co_name, 'rq: ' + str(self.payload) + ' ' + str(headers)), 'hide')
            resp = requests_retry_session_post(
                url.format('coupon/register'),
                headers=headers,
                json=self.payload,
                verify=False,
                timeout=self.timeout,
                proxies=self.proxies)
            prnt(self.msg.format(sys._getframe().f_code.co_name, 'rs: ' + str(resp.status_code) + ' ' + str(resp.text.strip())), 'hide')
            res = resp.json()

            result = res.get('result')
            msg_str = res.get('errorMessage')
            self.check_responce(msg_str)

            if result == 'betDelay':
                self.sleep_bet = (float(res.get('betDelay')) / 1000)
                shared[self.bk_name]['bet_delay'] = self.sleep_bet
                prnt(self.msg.format(sys._getframe().f_code.co_name, 'bet_delay: ' + str(self.sleep_bet) + ' sec.'))
                sleep(self.sleep_bet)
            else:
                shared[self.bk_name]['bet_delay'] = 0

            self.check_result(shared)

    def get_sum_sell(self, url: str = None):
        self.sum_sell = 0
        if self.bk_name == 'olimp':
            coupon = self.get_cur_max_bet_id()

            self.cashout_allowed = coupon.get('cashout_allowed', False)
            self.sum_sell = coupon.get('cashout_amount', 0)

            prnt(self.msg.format(sys._getframe().f_code.co_name, 'coupon cashout allowed: ' + str(self.cashout_allowed)))
            prnt(self.msg.format(sys._getframe().f_code.co_name, 'coupon sum sell: ' + str(self.sum_sell)))

        elif self.bk_name == 'fonbet':
            if not self.server_fb:
                self.server_fb = get_urls(self.mirror, self.proxies)

            if not url:
                url, self.timeout = get_common_url(self.server_fb)
                url = url.replace('session/', '')

            payload = copy.deepcopy(payload_coupon_sum)
            headers = copy.deepcopy(fb_headers)

            payload['clientId'] = self.account['login']
            payload['fsid'] = self.session['session']

            prnt(self.msg.format(sys._getframe().f_code.co_name, 'rq: ' + str(payload) + ' ' + str(headers)), 'hide')
            resp = requests_retry_session_post(url.format('coupon/sell/conditions/getFromVersion'),
                                               headers=headers,
                                               json=payload,
                                               verify=False,
                                               timeout=self.timeout)
            prnt(self.msg.format(sys._getframe().f_code.co_name, 'rs: ' + str(resp.status_code) + ' ' + str(resp.text)), 'hide')
            res = resp.json()
            result = res.get('result')
            msg_str = res.get('errorMessage')
            msg_code = res.get('errorCode', -1)
            self.check_responce(msg_str)

            timer_update = float(res.get('recommendedUpdateFrequency', 3))

            coupon_found = False

            conditions = None
            conditions = res.get('conditions', None)
            if conditions:
                for coupon in conditions:
                    if str(coupon.get('regId')) == str(self.reg_id):
                        coupon_found = True

                        prnt(self.msg.format(sys._getframe().f_code.co_name, 'canSell: ' + str(coupon.get('canSell', True))), 'hide')
                        prnt(self.msg.format(sys._getframe().f_code.co_name, 'tempBlock: ' + str(coupon.get('tempBlock', False))), 'hide')

                        if coupon.get('canSell', True) and not coupon.get('tempBlock', False):
                            self.sum_sell = float(coupon.get('completeSellSum'))
                            prnt(self.msg.format(sys._getframe().f_code.co_name, 'coupon sum sell: ' + str(self.sum_sell / self.sum_sell_divider)))
                        else:
                            err_str = self.msg_err.format(sys._getframe().f_code.co_name, 'coupon is lock, time sleep ' + str(timer_update) + ' sec.')
                            sleep(timer_update)
                            raise CouponBlocked(err_str)
            if msg_code == 2:
                raise CouponBlocked(msg_str)
            if not coupon_found:
                err_str = self.msg_err.format(
                    sys._getframe().f_code.co_name,
                    'coupon regId ' + str(self.reg_id) +
                    ' not found, retry, after sec: ' + str(timer_update))
                self.sale_bet(shared)

    def sale_bet(self, shared: dict):
        # добвить возможность перед выкупом еще раз попробовать проставить второе плечо, если оно было упущено по времени а не потерено

        # кажется это не нужно
        # self.opposite_stat_get(shared)

        if self.bk_name == 'olimp':

            # # sale_bet
            # try:
            #     1 / 0
            # except Exception as e:
            #     raise CouponBlocked(e)
            self.get_sum_sell()
            self.sale_profit = round(self.sum_sell - self.sum_bet)
            shared[self.bk_name]['sale_profit'] = round((self.sum_sell/self.sum_sell_divider) - self.sum_bet)

            if self.cashout_allowed and self.sum_sell > 0:
                payload = {}
                payload['bet_id'] = self.reg_id
                if self.bk_name == 'olimp':
                    self.sum_bet = 0
                payload['amount'] = self.sum_sell
                payload['session'] = self.session['session']
                payload.update(copy.deepcopy(ol_payload))
                payload.pop('time_shift')

                headers = copy.deepcopy(ol_headers)
                headers.update(get_xtoken_bet(payload))
                headers.update({'X-XERPC': '1'})

                prnt(self.msg.format(sys._getframe().f_code.co_name, 'rq: ' + str(payload) + ' ' + str(headers)), 'hide')
                resp = requests_retry_session_post(
                    # ol_url_api.format(self.server_olimp, 'user/cashout'),
                    ol_url_api.format('user/cashout'),
                    headers=headers,
                    data=payload,
                    verify=False,
                    timeout=self.timeout,
                    proxies=self.proxies)
                prnt(self.msg.format(sys._getframe().f_code.co_name, 'rs: ' + str(resp.status_code) + ' ' + str(resp.text.strip())), 'hide')
                res = resp.json()

                err_code = res.get('error', {}).get('err_code')
                err_msg = res.get('error', {}).get('err_desc')
                self.check_responce(err_msg)

                if res.get('data') and res.get('data').get('status', 'err') == 'ok':
                    prnt(self.msg.format(sys._getframe().f_code.co_name, 'code: ' + str(err_code) + ', ' + res.get('data', {}).get('msg')))
                else:
                    raise SaleError(err_msg)

            else:
                err_msg = 'coupon ' + str(self.reg_id) + ' blocked'
                raise CouponBlocked(err_msg)

        elif self.bk_name == 'fonbet':

            # # sale_bet
            # try:
            #     1 / 0
            # except Exception as e:
            #     raise CouponBlocked(e)

            if self.reg_id:
                # step1 get from version and sell sum
                if not self.server_fb:
                    self.server_fb = get_urls(self.mirror, self.proxies)
                url, self.timeout = get_common_url(self.server_fb)
                url = url.replace('session/', '')

                self.get_sum_sell(url)
                shared[self.bk_name]['sale_profit'] = round((self.sum_sell/self.sum_sell_divider) - self.sum_bet)

                # step2 get rqid for sell coupn
                payload = copy.deepcopy(payload_coupon_sum)
                headers = copy.deepcopy(fb_headers)

                payload['clientId'] = self.account['login']
                payload['fsid'] = self.session['session']

                prnt(self.msg.format(sys._getframe().f_code.co_name, 'rq: ' + str(payload) + ' ' + str(headers)), 'hide')
                resp = requests_retry_session_post(
                    url.format('coupon/sell/requestId'),
                    headers=headers,
                    json=payload,
                    verify=False,
                    timeout=self.timeout,
                    proxies=self.proxies)
                prnt(self.msg.format(sys._getframe().f_code.co_name, 'rs: ' + str(resp.status_code) + ' ' + str(resp.text)), 'hide')
                res = resp.json()
                result = res.get('result')
                msg_str = res.get('errorMessage')
                self.check_responce(msg_str)

                if res.get('result') == 'requestId':
                    self.reqIdSale = res.get('requestId')

                # step3 sell
                payload = copy.deepcopy(payload_coupon_sell)
                headers = copy.deepcopy(fb_headers)

                payload['regId'] = int(self.reg_id)
                payload['requestId'] = int(self.reqIdSale)
                payload['sellSum'] = self.sum_sell
                payload['clientId'] = self.account['login']
                payload['fsid'] = self.session['session']

                prnt(self.msg.format(sys._getframe().f_code.co_name, 'rq: ' + str(payload) + ' ' + str(headers)), 'hide')
                resp = requests_retry_session_post(
                    url.format('coupon/sell/completeSell'),
                    headers=headers,
                    json=payload,
                    verify=False,
                    timeout=self.timeout,
                    proxies=self.proxies)
                prnt(self.msg.format(sys._getframe().f_code.co_name, 'rs: ' + str(resp.status_code) + ' ' + str(resp.text)), 'hide')
                res = resp.json()
                result = res.get('result')
                msg_str = res.get('errorMessage')
                self.check_responce(msg_str)

                if result == 'sellDelay':
                    sell_delay_sec = (float(res.get('sellDelay')) / 1000)
                    prnt(self.msg.format(sys._getframe().f_code.co_name,
                                         'sell, delay: ' + str(sell_delay_sec) + ' sec.'))
                    sleep(sell_delay_sec)

                return self.check_sell_result(shared)

    def check_responce(self, err_msg):

        if err_msg:
            if 'не вошли в систему'.lower() in err_msg.lower() or \
                    'Not token access'.lower() in err_msg.lower() or \
                    'invalid session id'.lower() in err_msg.lower():
                err_str = self.msg_err.format(sys._getframe().f_code.co_name, 'session expired: ' + self.session['session'])
                raise SessionExpired(err_msg + ' ' + err_str)
            elif 'Продажа ставки недоступна'.lower() in err_msg.lower() or 'Изменилась сумма продажи ставки'.lower() in err_msg.lower():
                raise CouponBlocked(self.msg.format(sys._getframe().f_code.co_name, err_msg))
            elif 'Слишком частые ставки на событие'.lower() in err_msg.lower():
                raise BetIsLost(err_msg)
            elif 'Нет прав на выполнение операции'.lower() in err_msg.lower() or \
                    'No rights for operation'.lower() in err_msg.lower():
                shared[self.bk_name + '_err_fatal'] = err_msg
                raise BetIsLost(err_msg)

    def get_proxy(self) -> str:
        return get_proxies().get(self.bk_name)

    def check_max_bet(self, shared: dict):
        self.opposite_stat_get(shared)

        payload = copy.deepcopy(fb_payload_max_bet)
        headers = copy.deepcopy(fb_headers)

        if not self.server_fb:
            self.server_fb = get_urls(self.mirror, self.proxies)
        url, self.timeout = get_common_url(self.server_fb)

        if self.wager.get('param'):
            payload['coupon']['bets'][0]['param'] = int(self.wager['param'])
        payload['coupon']['bets'][0]['score'] = self.wager['score']
        payload['coupon']['bets'][0]['value'] = float(self.wager['value'])
        payload['coupon']['bets'][0]['event'] = int(self.wager['event'])
        payload['coupon']['bets'][0]['factor'] = int(self.wager['factor'])
        payload['coupon']['amount'] = 0.0

        payload['fsid'] = self.session['session']
        payload['clientId'] = self.account['login']

        payload['coupon'].pop('flexBet')
        payload['coupon'].pop('flexParam')
        payload['coupon']['bets'][0].pop('lineType')

        data = get_dumped_payload(payload)

        prnt(self.msg.format(sys._getframe().f_code.co_name, 'rq: ' + str(payload) + ' ' + str(headers)), 'hide')
        resp = requests_retry_session_post(
            # url.format('coupon/getMinMax'), Not working, why?
            url.format('coupon/getMinMax'),
            headers=headers,
            data=data,
            verify=False,
            timeout=self.timeout,
            proxies=self.proxies)
        prnt(self.msg.format(sys._getframe().f_code.co_name, 'rs: ' + str(resp.status_code) + ' ' + str(resp.text.strip())), 'hide')
        res = resp.json()

        result = res.get('result')
        msg_str = res.get('errorMessage')
        self.check_responce(msg_str)

        if 'min' not in res:
            err_str = self.msg_err.format(sys._getframe().f_code.co_name, 'min sum not found')
            raise BetIsLost(err_str)

        min_amount, max_amount = res['min'] // 100, res['max'] // 100

        shared[self.bk_name]['max_bet'] = max_amount

        prnt(self.msg.format(sys._getframe().f_code.co_name, 'sum bet=' + str(self.sum_bet)))
        prnt(self.msg.format(sys._getframe().f_code.co_name, 'min_amount=' + str(min_amount) + ', max_amount=' + str(max_amount)))
        if min_amount > self.sum_bet:
            err_str = self.msg_err.format(sys._getframe().f_code.co_name, 'min bet')
            self.min_bet = min_amount
            raise BetIsLost(err_str)
        if self.sum_bet > max_amount:
            err_str = self.msg_err.format(sys._getframe().f_code.co_name, 'max bet')
            self.max_bet = max_amount
            raise BetIsLost(err_str)
        if self.session.get('balance') and self.session['balance'] < self.sum_bet:
            err_str = self.msg_err.format(sys._getframe().f_code.co_name, 'mo money')
            raise NoMoney(err_str)

    def check_result(self, shared: dict):

        def replay_bet(n: str):
            if self.max_bet and ((self.first_bet_in == 'auto' and self.vector == 'DOWN') or self.bk_name == self.first_bet_in):
                wait_bet = self.sleep_bet * 2
                prnt(self.msg.format(sys._getframe().f_code.co_name, 'Получен неявный максбет #' + n + ': ' + str(self.max_bet) + ', wait: ' + str(wait_bet)))
                self.recalc_sum_by_maxbet(shared)
                sleep(wait_bet)
                return self.bet_place(shared)
            else:
                raise AttributeError(err_msg)

        payload = copy.deepcopy(self.payload)

        url, timeout = get_common_url(self.server_fb)

        try:
            del payload['coupon']
        except:
            pass

        headers = copy.deepcopy(fb_headers)

        prnt(self.msg.format(sys._getframe().f_code.co_name, 'rs: ' + str(payload)), 'hide')
        resp = requests_retry_session_post(
            url.format('coupon/result'),
            headers=headers,
            json=payload,
            verify=False,
            timeout=self.timeout)
        prnt(self.msg.format(sys._getframe().f_code.co_name, 'rs: ' + str(resp.status_code) + ' ' + str(resp.text.strip())), 'hide')
        res = resp.json()

        result = res.get('result')
        msg_str = res.get('errorMessage')

        err_code = res.get('coupon', {}).get('resultCode')
        err_msg = res.get('coupon', {}).get('errorMessageRus')
        err_msg_eng = res.get('coupon', {}).get('errorMessageEng')

        self.opposite_stat_get(shared)
        self.check_responce(err_msg)

        if result == 'couponResult':
            if err_code == 0:
                self.reg_id = res.get('coupon').get('regId')

                shared[self.bk_name]['reg_id'] = self.reg_id

                prnt(self.msg.format(sys._getframe().f_code.co_name, 'bet successful, reg_id: ' + str(self.reg_id)))
                shared[self.bk_name + '_err'] = 'ok'

            if err_code == 1:

                self.opposite_stat_get(shared)
                if 'Допустимая сумма ставки' in err_msg:
                    try:
                        substr = err_msg.replace(' ', '').replace('.', '').replace(',', '')
                        self.min_bet = int(re.search('(\d{1,})(-)(\d{1,})', substr).group(1))
                        self.max_bet = int(re.search('(\d{1,})(-)(\d{1,})', substr).group(3))
                        replay_bet(str(err_code))
                    except AttributeError as e:
                        prnt(self.msg.format(sys._getframe().f_code.co_name, e + ': ' + err_msg))
                        self.max_bet = 0

                    if self.max_bet == 0:
                        raise BetIsLost(err_msg)
                else:
                    err_str = self.msg.format(sys._getframe().f_code.co_name, err_msg)
                    raise BetIsLost(err_str)

            elif err_code == 100:
                self.opposite_stat_get(shared)
                if 'Превышена cуммарная ставка для события' in err_msg:
                    try:
                        self.max_bet = int(re.search('=(\d{1,})\D', err_msg.replace(' ', '').replace('.', '').replace(',', '')).group(1))
                        replay_bet(str(err_code))
                    except AttributeError as e:
                        prnt(self.msg.format(sys._getframe().f_code.co_name, e + ': ' + err_msg))
                        self.max_bet = 0

                    if self.max_bet == 0:
                        raise BetIsLost(err_msg)
                else:
                    err_str = err_msg + ', новая котировка:' + str(res.get('coupon', {}).get('bets')[0].get('value', 0))
                    sleep(self.sleep_bet)
                    err_str = self.msg_err.format(sys._getframe().f_code.co_name, err_str)
                    raise BetError(err_str)
            elif err_code == 2:
                self.opposite_stat_get(shared)
                # Котировка вообще ушла
                if res.get('coupon', {}).get('bets')[0]['value'] == 0:
                    err_str = 'current bet is lost: ' + str(err_msg)
                    raise BetIsLost(err_str)
                # Изменился ИД тотола или значение катировки
                else:
                    new_wager = res.get('coupon').get('bets')[0]

                    if str(new_wager.get('param', '')) == str(self.wager.get('param', '')) and \
                            int(self.wager.get('factor', 0)) != int(new_wager.get('factor', 0)):

                        err_str = self.msg.format(sys._getframe().f_code.co_name, 'Изменилась ИД ставки: old: ' + str(self.wager) + ', new: ' + str(new_wager))
                        prnt(err_str)
                        self.wager.update(new_wager)
                        return self.bet_place(shared)

                    elif str(new_wager.get('param', '')) != str(self.wager.get('param', '')) and \
                            int(self.wager.get('factor', 0)) == int(new_wager.get('factor', 0)):

                        prnt(self.msg_err.format(sys._getframe().f_code.co_name,
                                                 'Изменилась тотал ставки, param не совпадает: ' +
                                                 'new_wager: ' + str(new_wager) + ', old_wager: ' + str(self.wager)))

                        if self.bk_container.get('bet_type'):

                            prnt(self.msg.format(sys._getframe().f_code.co_name, 'поиск нового id тотала: ' + self.bk_container.get('bet_type')))

                            match_id = self.wager.get('event')
                            new_wager = get_new_bets_fonbet(match_id, self.proxies, self.timeout)
                            new_wager = new_wager.get(str(match_id), {}).get('kofs', {}).get(self.bk_container.get('bet_type'))
                            if new_wager:
                                err_str = self.msg.format(sys._getframe().f_code.co_name, 'Тотал найден: ' + str(new_wager))
                                self.wager.update(new_wager)
                                prnt(err_str)
                                return self.bet_place(shared)
                            else:
                                err_str = self.msg_err.format(sys._getframe().f_code.co_name, 'Тотал не найден: ' + str(new_wager))
                                prnt(err_str)
                                raise BetIsLost(err_str)
                        else:
                            err_str = self.msg_err.format(
                                sys._getframe().f_code.co_name,
                                'Тип ставки, например 1ТМ(2.5) - не задан, выдаю ошибку: bet_type:' +
                                self.bk_container.get('bet_type') + ', bk_container:' + str(self.bk_container))
                            raise BetIsLost(err_str)
                    # Изменилась катировка
                    elif 'Odds changed'.lower() in err_msg_eng.lower():
                        if self.vector == 'DOWN':
                            err_str = self.msg_err.format(sys._getframe().f_code.co_name, err_msg)
                            raise BetIsLost(err_str)
                        else:
                            err_str = self.msg_err.format(sys._getframe().f_code.co_name, err_msg)
                            raise BetError(err_str)
                    else:
                        err_str = self.msg_err.format(
                            sys._getframe().f_code.co_name,
                            'неизвестная ошибка: ' + str(err_msg) +
                            ', new_wager: ' + str(new_wager) +
                            ', old_wager: ' + str(self.wager))
                        raise BetIsLost(err_str)
        elif result == 'error' and 'temporary unknown result' in msg_str:
            err_str = 'Get temporary unknown result: ' + str(msg_str)
            prnt(self.msg.format(sys._getframe().f_code.co_name, err_str))
            return self.check_result(shared)
        else:
            self.opposite_stat_get(shared)
            err_str = self.msg_err.format(sys._getframe().f_code.co_name, err_msg)
            raise BetError(err_str)

    def set_session_state(self):

        if not self.session.get('session'):
            self.session['session'] = read_file(self.session_file)

    def get_request_id(self):

        if not self.server_fb:
            self.server_fb = get_urls(self.mirror, self.proxies)

        url, self.timeout = get_common_url(self.server_fb)

        headers = copy.deepcopy(fb_headers)

        payload = copy.deepcopy(payload_req)
        payload['fsid'] = self.payload['fsid']
        payload['clientId'] = self.account['login']
        payload['client']['id'] = self.account['login']

        prnt(self.msg.format(sys._getframe().f_code.co_name, 'rq: ' + str(payload) + ' ' + str(headers)), 'hide')
        resp = requests_retry_session_post(
            url.format('coupon/requestId'),
            headers=headers,
            json=payload,
            verify=False,
            timeout=self.timeout,
            proxies=self.proxies)
        prnt(self.msg.format(sys._getframe().f_code.co_name, 'rs: ' + str(resp.status_code) + ' ' + str(resp.text)), 'hide')
        res = resp.json()

        result = res.get('result')
        msg_str = res.get('errorMessage')
        self.check_responce(msg_str)

        if 'requestId' not in res:
            err_str = self.msg_err.format(sys._getframe().f_code.co_name, 'key requestId not found in response')
            raise BetError(err_str)
        else:
            self.reqId = res['requestId']
            prnt(self.msg.format(sys._getframe().f_code.co_name, 'get requestId=' + str(self.reqId)))

    def check_sell_result(self, shared: dict):
        if not self.server_fb:
            self.server_fb = get_urls(self.mirror, self.proxies)

        url, self.timeout = get_common_url(self.server_fb)
        url = url.replace('session/', '')

        payload = copy.deepcopy(payload_sell_check_result)
        headers = copy.deepcopy(fb_headers)

        payload['requestId'] = self.reqIdSale
        payload['clientId'] = self.account['login']
        payload['fsid'] = self.session['session']

        prnt(self.msg.format(sys._getframe().f_code.co_name, 'rq: ' + str(payload) + ' ' + str(headers)), 'hide')
        resp = requests_retry_session_post(
            url.format('coupon/sell/result'),
            headers=headers,
            json=payload,
            verify=False,
            timeout=self.timeout,
            proxies=self.proxies)
        prnt(self.msg.format(sys._getframe().f_code.co_name, 'rs: ' + str(resp.status_code) + ' ' + str(resp.text)), 'hide')
        res = resp.json()
        result = res.get('result')
        msg_str = res.get('errorMessage')
        self.check_responce(msg_str)

        if result == 'error' and 'temporary unknown result' in msg_str:
            raise CouponBlocked('Get temporary unknown result: ' + str(msg_str))

        elif result == 'sellDelay':
            sell_delay_sec = (float(res.get('sellDelay')) / 1000)
            prnt(self.msg.format(sys._getframe().f_code.co_name, 'sell, delay: ' + str(sell_delay_sec) + ' sec.'))
            sleep(sell_delay_sec)
            return self.check_sell_result(shared)

        elif result == 'unableToSellCoupon':
            if res.get('reason') == 2:
                raise BetIsLost(self.msg_err.format(sys._getframe().f_code.co_name, 'unable to sell coupon, reason=' + str(res.get('reason'))))
            elif res.get('reason') == 3:
                raise CouponBlocked('coupon ' + str(self.reg_id) + ' blocked')
            else:
                raise CouponBlocked(self.msg.format(sys._getframe().f_code.co_name, 'new actualSellSum: ' + str(res.get('actualSellSum') / 100)))

        elif result == 'couponCompletelySold':
            prnt(self.msg.format(sys._getframe().f_code.co_name, 'sell successful, sum sold: ' + str(res.get('soldSum') / 100)))
        else:
            raise BetIsLost

    def get_cur_max_bet_id(self, filter='0100', offset='0'):

        # req_url = ol_url_api.format(self.server_olimp, 'user/history')
        req_url = ol_url_api.format('user/history')

        payload = copy.deepcopy(ol_payload)
        payload['filter'] = filter  # только не расчитанные
        payload['offset'] = offset
        payload['session'] = self.session['session']

        headers = copy.deepcopy(ol_headers)
        headers.update(get_xtoken_bet(payload))
        headers.update({'X-XERPC': '1'})

        prnt(self.msg.format(sys._getframe().f_code.co_name, 'rq: ' + str(payload) + ' ' + str(headers)), 'hide')
        resp = requests_retry_session_post(
            req_url,
            headers=headers,
            data=payload,
            verify=False,
            timeout=self.timeout,
            proxies=self.proxies)
        prnt(self.msg.format(sys._getframe().f_code.co_name, 'rs: ' + str(resp.status_code) + ' ' + str(resp.text.strip())), 'hide')
        res = resp.json()

        err_code = res.get('error', {}).get('err_code')
        err_msg = res.get('error', {}).get('err_desc')
        self.check_responce(err_msg)

        max_bet_id = 0
        coupon_data = {}

        # reg_id - мы знаем заранее - только при ручном выкупе как правило
        if self.reg_id:
            coupon_found = False
            for bet_list in res.get('data').get('bet_list', {}):
                cur_bet_id = bet_list.get('bet_id')
                if cur_bet_id == self.reg_id:
                    coupon_found = True
                    max_bet_id = cur_bet_id
                    coupon_data = bet_list
            if not coupon_found:
                err_str = 'coupon reg_id: ' + str(self.reg_id) + ', not found'
                raise BetIsLost(err_str)

        # Мы не знаем reg_id и берем последний по матчу
        elif self.match_id:
            for bet_list in res.get('data').get('bet_list', []):
                if str(bet_list.get('events')[0].get('matchid')) == str(self.match_id):
                    cur_bet_id = bet_list.get('bet_id')
                    if cur_bet_id > max_bet_id:
                        max_bet_id = cur_bet_id
                        coupon_data = bet_list
        # Мы не знаем мата и берем просто последний
        else:
            for bet_list in res.get('data').get('bet_list', []):
                cur_bet_id = bet_list.get('bet_id')
                if cur_bet_id > max_bet_id:
                    max_bet_id = cur_bet_id
                    coupon_data = bet_list

        if max_bet_id:
            self.reg_id = max_bet_id
            return coupon_data


if __name__ == '__main__':
    shared = {}

    FONBET_USER = {"login": get_account_info('fonbet', 'login'), "password": get_account_info('fonbet', 'password')}

    OLIMP_USER = {"login": get_account_info('olimp', 'login'), "password": get_account_info('olimp', 'password')}

    wager_olimp = {
        'apid': '1174307310:46807570:1:3:-9999:2:0:0:1',
        'factor': '1.06',
        'sport_id': 1,
        'event': '46807570'}

    FONBET_USER = {'login': 5447708, 'password': 'tStseFuY'}
    wager_fonbet = {
        'event': '13446124',
        'factor': '922',
        'param': '',
        'score': '1:0',
        'value': '5'}

    shared = {}
    shared['wager'] = wager_olimp  # wager_olimp
    shared['amount'] = 30
    bk1 = Thread(target=BetManager, args=(shared, 'olimp', 'fonbet'))
    bk1.start()

    # shared = {}
    # shared['wager'] = wager_fonbet  # wager_olimp
    # shared['amount'] = 45
    # bk2 = Thread(target=BetManager, args=(shared, 'fonbet', 'olimp'))
    # bk2.start()

    bk1.join()
    # bk2.join()
