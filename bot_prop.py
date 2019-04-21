# coding:utf-8
# BOI
# PY_PATH = 'python3.6'
# TOKEN = '843081630:AAFmVT4hi5R71mgJpojVxOmTGEaZJA-LWYI'
# ADMINS = [381868674, 33847743]

# TEST
PY_PATH = 'D:\\YandexDisk\\Парсинг\\bot_manager\\venv\\Scripts\\python.exe'
TOKEN = '598446286:AAEhbB2RDQ7oEe7pX2vif-IENIdIVIZ9xVk'
ADMINS = [381868674]

PROXY = {
    'http': 'socks5://shaggy:hzsyk4@191.101.104.71:14487',
    'https': 'socks5://shaggy:hzsyk4@191.101.104.71:14487'
}
PROXY2 = {
    "http": "http://shaggy:hzsyk4@191.101.104.71:4487",
    "https": "https://shaggy:hzsyk4@191.101.104.71:4487"
}
REQUEST_KWARGS = {
    'proxy_url': 'https://shaggy:hzsyk4@191.101.104.71:4487',
    'read_timeout': 60,
    'connect_timeout': 30
}

ROLE = None

MSG_START_STOP = 'Информация об аккаунте: TODO'
MSG_CHANGE_ACC = 'Пожалуйста, выберите аккаунт:'
MSG_ACC_START_WAIT = 'Аккаунт запущен, начну работу через 15 сек...'
MSG_ACC_STOP_WAIT = 'Аккаунт останавливается, пожалуйста ждите...'
MSG_ACC_STOP_WAIT_EXT = 'Аккаунт останавливается, это может занять несколько минут, пожалуйста подождите...'
