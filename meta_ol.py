# coding: utf-8
from hashlib import md5
from utils import get_prop
import re
import utils

# ol_url_api = "https://{}.olimp-proxy.ru/api/{}"
ol_url_api = 'https://' + get_prop('server_olimp', 'api2.olimp.bet') + '/api/{}'
# ol_url_api_http = 'http://' + get_prop('server_olimp', 'olimpkzapi.ru')
# olimp_url_https = 'https://10.olimp-proxy.ru'
# olimp_url_random = 'https://{}.olimp-proxy.ru'  # c 13 по 18й
ol_payload = {"time_shift": 0, "lang_id": "0", "platforma": "ANDROID1"}
olimp_secret_key = "b2c59ba4-7702-4b12-bef5-0908391851d9"

ol_headers = {
    'Accept-Encoding': 'gzip',
    'Connection': 'Keep-Alive',
    'Content-Type': 'application/x-www-form-urlencoded',
    'User-Agent': 'okhttp/3.9.1'
}

olimp_data = {
    "live": 1,
    # "sport_id": 1,
    "platforma": "ANDROID1",
    "lang_id": 0,
    "time_shift": 0
}

abbreviations = {
    "Победапервой": "П1",
    "Победавторой": "П2",

    "Ничья": "Н",
    "Перваянепроиграет": "П1Н",
    "Втораянепроиграет": "П2Н",
    "Ничьейнебудет": "12",

    "Обезабьют:да": "ОЗД",
    "Обезабьют:нет": "ОЗН",
    "Т1забьет:да": "КЗ1",
    "Т1забьет:нет": "КНЗ1",
    "Т2забьет:да": "КЗ2",
    "Т2забьет:нет": "КНЗ2",
    "Тоталбол": "ТБ({})",
    "Тоталмен": "ТМ({})",
    "Тотал1-готаймабол": "1ТБ({})",
    "Тотал1-готаймамен": "1ТМ({})",
    "Тотал2-готаймабол": "2ТБ({})",
    "Тотал2-готаймамен": "2ТМ({})",
    # "Т1бол":"ИТБ1({})",
    # "Т1мен":"ИТМ1({})",
    # "Т2бол":"ИТБ2({})",
    # "Т2мен":"ИТМ2({})"
    "Т1бол": "ТБ1({})",
    "Т1мен": "ТМ1({})",
    "Т2бол": "ТБ2({})",
    "Т2мен": "ТМ2({})",

    "П1сфорой": "Ф1({})",
    "П2сфорой": "Ф2({})",

    "П1в1-мт.сфорой": "1Ф1({})",
    "П2в1-мт.сфорой": "1Ф2({})",
}


def to_abb(sbet):
    sbet = sbet.replace(' ', '').replace('\t', '')
    value = re.findall('\((.*)\)', sbet)[0]
    key = re.sub('\((.*)\)', '', sbet)
    abr = ''
    try:
        abr = abbreviations[key].format(value)
    except Exception as e:
        utils.prnt('error: ' + str(e) + ', to_abb("' + sbet + '"), value=' + value + ', key=' + key)
    return abr


def get_xtoken_bet(payload):
    global olimp_secret_key
    sorted_values = [str(payload[key]) for key in sorted(payload.keys())]
    to_encode = ";".join(sorted_values + [olimp_secret_key])
    return {"X-TOKEN": md5(to_encode.encode()).hexdigest()}
