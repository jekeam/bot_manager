# coding: utf-8
from random import choice, random
from json import dumps
import requests
from utils import check_status_with_resp, prnt
import time
from retry_requests import requests_retry_session

# VICTORIES
VICTS = [['П1', 921], ['Н', 922], ['П2', 923], ['П1Н', 924], ['12', 1571], ['П2Н', 925],
         ['ОЗД', 4241], ['ОЗН', 4242], ['КЗ1', 4235], ['КНЗ1', 4236], ['КЗ2', 4238], ['КНЗ2', 4239]]
# Обе забьют:да/Обе забьют:нет/Команда 1 забьет/Команда 1 не забьет/Команда 2 забьет/Команда 2 не забьет
# TOTALS
TTO = [['ТБ({})', 930], ['ТБ({})', 940], ['ТБ({})', 1696], ['ТБ({})', 1727], ['ТБ({})', 1730], ['ТБ({})', 1733]]
TTU = [['ТМ({})', 931], ['ТМ({})', 941], ['ТМ({})', 1697], ['ТМ({})', 1728], ['ТМ({})', 1731], ['ТМ({})', 1734]]
# TEAM TOTALS-1
TT1O = [['ТБ1({})', 1809], ['ТБ1({})', 1812], ['ТБ1({})', 1815]]
TT1U = [['ТМ1({})', 1810], ['ТМ1({})', 1813], ['ТМ1({})', 1816]]
# TEAM TOTALS-2
TT2O = [['ТБ2({})', 1854], ['ТБ2({})', 1873], ['ТБ2({})', 1880]]
TT2U = [['ТМ2({})', 1871], ['ТМ2({})', 1874], ['ТМ2({})', 1881]]
# FORA
FORA = [['Ф1({})', 927], ['Ф2({})', 928],
        ['Ф1({})', 937], ['Ф2({})', 938],
        ['Ф1({})', 910], ['Ф1({})', 989], ['Ф1({})', 1569],
        ['Ф2({})', 991], ['Ф2({})', 1572], ['Ф2({})', 1572]]

LENOVO_MODEL = ''

url_fonbet = 'https://line-01.ccf4ab51771cacd46d.com'

url_fonbet_matchs = url_fonbet + "/live/currentLine/en/?2lzf1earo8wjksbh22s"
url_fonbet_match = url_fonbet + "/line/eventView?eventId="

fb_payload = {
    "appVersion": "5.1.3b",
    "lang": "ru",
    "rooted": False,
    "sdkVersion": 21,
    "sysId": 4
}

fb_browser_head = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"
}

fb_headers = {
    "User-Agent": "Fonbet/5.1.3b (Android 21; Phone; com.bkfonbet)",
    "Content-Type": "application/json; charset=UTF-8",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip"
}

fonbet_header2 = {
    'User-Agent': 'Fonbet/5.1.3b (Android 21; Phone; com.bkfonbet)',
    'Connection': 'Keep-Alive',
    'Accept-Encoding': 'gzip'
}

fb_payload_bet = {
    "coupon":
        {
            "flexBet": "any",  # Изменения коэф-в, any - все, up - вверх
            "flexParam": False,  # Изменения фор и тоталов, True - принимать, False - не принимать
            "bets":
                [
                    {
                        "lineType": "LIVE",
                        "score": "",
                        "value": 0,
                        "event": 0,
                        "factor": 0,
                        "num": 0
                    },
                ],
            "amount": 0.0,
            "system": 0
        },
    "appVersion": "5.1.3b",
    "carrier": "",
    "deviceManufacturer": "LENOVO",
    "deviceModel": "Lenovo " + LENOVO_MODEL,
    "fsid": "",
    "lang": "ru",
    "platform": "mobile_android",
    "rooted": False,
    "sdkVersion": 21,
    "sysId": 4,
    "clientId": 0
}

fb_payload_max_bet = {
    "coupon":
        {
            "flexBet": "any",  # Изменения коэф-в, any - все, up - вверх
            "flexParam": False,  # Изменения фор и тоталов, True - принимать, False - не принимать
            "bets":
                [
                    {
                        "lineType": "LIVE",
                        "score": "",
                        "value": 0,
                        "event": 0,
                        "factor": 0,
                        "num": 0
                    },
                ],
            "amount": 0.0,
            "system": 0
        },
    "appVersion": "5.1.3b",
    "carrier": "",
    "deviceManufacturer": "LENOVO",
    "deviceModel": "Lenovo " + LENOVO_MODEL,
    "fsid": "",
    "lang": "ru",
    "platform": "mobile_android",
    "rooted": False,
    "sdkVersion": 21,
    "sysId": 4,
    "clientId": 0
}

payload_req = {
    "client": {"id": 0},
    "appVersion": "5.1.3b",
    "carrier": "",
    "deviceManufacturer": "LENOVO",
    "deviceModel": "Lenovo " + LENOVO_MODEL,
    "fsid": "",
    "lang": "ru",
    "platform": "mobile_android",
    "rooted": False,
    "sdkVersion": 21,
    "sysId": 4,
    "clientId": 0
}

payload_coupon_sum = {
    "clientId": "",
    "fsid": "",
    "lang": "ru",
    "platform": "mobile_android",
    "sysId": 4
}

payload_sell_check_result = {
    "requestId": 0,
    "clientId": "",
    "fsid": "",
    "lang": "ru",
    "platform": "mobile_android",
    "sysId": 4
}

payload_coupon_sell = {
    "flexSum": "up",
    "regId": 0,
    "requestId": 0,
    "sellSum": 0.0,
    "clientId": "",
    "fsid": "",
    "lang": "ru",
    "platform": "mobile_android",
    "sysId": 4
}


def get_random_str():
    result = ''
    alph_num = '0123456789'
    alph = 'abcdefghijklmnopqrstuvwxyz'
    alph = alph + alph.upper() + alph_num
    for _idx in range(48):
        result += choice(alph)
    return result


def get_dumped_payload(payload):
    dumped = dumps(payload)
    dumped = dumped.replace(": ", ":")  # remove spaces between items
    dumped = dumped.replace(", ", ",")
    return dumped


def get_urls(mirror, proxies):
    global fb_browser_head
    url = "https://" + mirror + "/urls.json?{}".format(random())
    resp = requests_retry_session().get(
        url,
        headers=fb_browser_head,
        verify=False,
        timeout=4,
        proxies=proxies
    )
    check_status_with_resp(resp)
    return resp.json()


def get_common_url(data_urls, url_api=None):
    if not url_api:
        client_url = data_urls["clients-api"][0]
    else:
        client_url = data_urls[url_api][0]
    timeout = 4  # data_urls["timeout"] / 100
    return "https:{url}/session/".format(url=client_url) + "{}", timeout


def get_new_bets_fonbet(match_id, proxies, time_out=50):
    key_id = str(match_id)
    bets_fonbet = {}
    try:
        resp = requests_retry_session().get(
            url_fonbet_match + str(match_id) + "&lang=en",
            headers=fonbet_header2,
            timeout=time_out,
            verify=False,
            proxies=proxies,
        )
        resp = resp.json()

        TT = []
        for bet in [TTO, TTU, TT1O, TT1U, TT2O, TT2U, FORA]:
            TT.extend(bet)

        for event in resp.get("events"):
            # prnts(jsondumps(event, ensure_ascii=False))
            # exit()

            score = event.get('score', '0:0').replace('-', ':')
            timer = event.get('timer')
            minute = event.get('timerSeconds', 0) / 60
            skId = event.get('skId')
            skName = event.get('skName')
            sport_name = event.get('sportName')
            name = event.get('name')
            priority = event.get('priority')
            score_1st = event.get('scoreComment', '').replace('-', ':')

            if event.get('parentId') == 0 or 'st half' in name or 'nd half' in name:
                if event.get('parentId') == 0:
                    try:
                        bets_fonbet[key_id].update({
                            'sport_id': skId,
                            'sport_name': skName,
                            'league': sport_name,
                            'name': name,
                            'priority': priority,
                            'score': score,
                            'score_1st': score_1st,
                            'time': timer,
                            'minute': minute,
                            'time_req': round(time.time())
                        })
                    except Exception as e:
                        # print(e)
                        bets_fonbet[key_id] = {
                            'sport_id': skId,
                            'sport_name': skName,
                            'league': sport_name,
                            'name': name,
                            'priority': priority,
                            'score': score,
                            'score_1st': score_1st,
                            'time': timer,
                            'minute': minute,
                            'time_req': round(time.time()),
                            'time_change_total': round(time.time()),
                            'avg_change_total': [],
                            'kofs': {}
                        }

                # prnts('event_name', event.get('name'))

                half = ''
                if 'st half' in name or 'nd half' in name:
                    half = name.replace('st half', '').replace('nd half', '')

                for cat in event.get('subcategories'):

                    cat_name = cat.get('name')
                    # prnts('cat_name', cat_name)
                    if cat_name in ('1X2 (90 min)', '1X2', 'Goal - no goal', 'Total', 'Totals', 'Team Totals-1', 'Team Totals-2', 'Hcap'):

                        for kof in cat.get('quotes'):

                            factorId = str(kof.get('factorId'))
                            pValue = kof.get('pValue', '')
                            p = kof.get('p', '').replace('+', '')
                            kof_is_block = kof.get('blocked', False)
                            if kof_is_block:
                                value = 0
                            else:
                                value = kof.get('value')
                            # {'event': '12788610', 'factor': '921', 'param': '', 'score': '1:0', 'value': '1.25'}
                            for vct in VICTS:
                                coef = half + str(vct[0])
                                if str(vct[1]) == factorId:
                                    bets_fonbet[key_id]['kofs'].update(
                                        {
                                            coef:
                                                {
                                                    'time_req': round(time.time()),
                                                    'event': event.get('id'),
                                                    'value': value,
                                                    'param': '',
                                                    'factor': factorId,
                                                    'score': score
                                                }
                                        }
                                    )

                            for stake in TT:
                                coef = half + str(stake[0].format(p))  # + num_team
                                if str(stake[1]) == factorId:
                                    bets_fonbet[key_id]['kofs'].update(
                                        {
                                            coef:
                                                {
                                                    'time_req': round(time.time()),
                                                    'event': event.get('id'),
                                                    'value': value,
                                                    'param': pValue,
                                                    'factor': factorId,
                                                    'score': score
                                                }}
                                    )
        return bets_fonbet
    except Exception as e:
        prnt(e)
        raise ValueError(e)
