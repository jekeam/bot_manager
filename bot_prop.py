# coding:utf-8
from emoji import emojize

# old_proxy = 'socks5://shaggy:hzsyk4@191.101.104.71:14487'
# new_proxy = 'socks5://suineg:8veh34@185.161.211.100:12974'
# new_proxy_http = 'http://suineg:8veh34@185.161.211.100:2974'

new_proxy = 'socks5://Selsuinegne:R5v7JwJ@181.214.107.89:45786'
new_proxy_http = 'http://Selsuinegne:R5v7JwJ@181.214.107.89:45785'

# BOI

PY_PATH = 'python3.6'
TOKEN = '843081630:AAFmVT4hi5R71mgJpojVxOmTGEaZJA-LWYI'
ADMINS = [381868674, 33847743, 337186802]
IP_SERVER = '62.109.10.57:80'

# TEST
# PY_PATH = 'D:\\YandexDisk\\Парсинг\\bot_manager\\venv\\Scripts\\python.exe'
# TOKEN = '598446286:AAEhbB2RDQ7oEe7pX2vif-IENIdIVIZ9xVk'
# ADMINS = [381868674]
# IP_SERVER = '149.154.70.53:80'

PROXY = {
    'http': new_proxy,
    'https': new_proxy
}

REQUEST_KWARGS = {
    'proxy_url': new_proxy_http,
    'read_timeout': 60,
    'connect_timeout': 30
}

ROLE = None

MSG_START_STOP = 'Информация об аккаунте:'
MSG_CHANGE_ACC = 'Пожалуйста, выберите аккаунт:'
MSG_ACC_START_WAIT = 'Аккаунт запущен, начну работу через 15 сек...'
MSG_ACC_STOP_WAIT = 'Аккаунт останавливается, пожалуйста ждите...'
MSG_ACC_STOP_WAIT_EXT = 'Аккаунт останавливается, это может занять несколько минут, пожалуйста подождите...'
MSG_PROP_LIST = 'Пожалуйста, выберите настройку'
MSG_PUT_VAL = 'Введите новое значение:'

BTN_CLOSE = emojize(':heavy_multiplication_x:', use_aliases=True) + ' Закрыть'
BTN_BACK = emojize(':back:', use_aliases=True) + ' Назад'
BTN_SETTINGS = emojize(':wrench:', use_aliases=True) + ' Настройка'
BTN_GET_STAT = emojize(':chart_with_upwards_trend:', use_aliases=True) + ' Статистика'
