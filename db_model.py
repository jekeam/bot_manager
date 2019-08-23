# coding: utf-8
from peewee import *
import time
from json import dumps, loads
from uuid import uuid1
from playhouse.sqlite_ext import SqliteExtDatabase

db = MySQLDatabase('bot_manager_test', user='root', password='131189_Ak13', host='127.0.0.1', port=3306)

first_bet_in = ["created", "notcreator", "fonbet", "olimp", "parallel", "auto"]

bks = ["fonbet", "olimp", "auto"]

prop_abr = {
    "SUMM": {"abr": "Общая ставка", "type": "int", "max": "10000", "min": "400", "access_list": [], "error": ""},
    "RANDOM_SUMM_PROC": {"abr": "% Разброс ставки", "type": "int", "max": "30", "min": "0", "access_list": [], "error": ""},
    "MIN_PROC": {"abr": "% Вилки от", "type": "float", "max": "10", "min": "0", "access_list": [], "error": ""},
    "FORK_LIFE_TIME": {"abr": "Вилки от сек.", "type": "int", "max": "500", "min": "2", "access_list": [], "error": ""},
    "FORK_TIME_TYPE": {"abr": "Тип времени вилки", "type": "str", "max": "", "min": "", "access_list": ["текущее", "общее"], "error": ""},
    "WORK_HOUR_END": {"abr": "Остановка в", "type": "int", "max": "23", "min": "0", "access_list": [], "error": ""},
    "ROUND_FORK": {"abr": "Округление", "type": "int", "max": "100", "min": "5", "access_list": ["5", "10", "50", "100"], "error": ""},
    "MAX_FORK": {"abr": "MAX ставок", "type": "int", "max": "50", "min": "1", "access_list": [], "error": ""},
    "MAX_FAIL": {"abr": "MAX выкупов", "type": "int", "max": "7", "min": "1", "access_list": [], "error": ""},
    "FIRST_BET_IN": {"abr": "Первая ставка в", "type": "str", "max": "", "min": "", "access_list": first_bet_in, "error": ""},
    "MAX_KOF": {"abr": "MAX коэф-т", "type": "float", "max": "1000", "min": "1.02", "access_list": [], "error": ""},
    "CHECK_MAX_BET": {"abr": "Проверка maxbet", "type": "str", "max": "", "min": "", "access_list": ["вкл", "выкл"], "error": ""},
    "SUM_BY_MAX": {"abr": "Пересчет maxbet", "type": "str", "max": "", "min": "", "access_list": ["вкл", "выкл"], "error": ""},
    "PROC_BY_MAX": {"abr": "% от maxbet", "type": "int", "max": "100", "min": "10", "access_list": [], "error": ""},
    "TIMEOUT_FORK": {"abr": "Ждать после ставки", "type": "int", "max": "5400", "min": "30", "access_list": [], "error": ""},
    "TEAM_RES": {"abr": "Рез-е команды", "type": "str", "max": "", "min": "", "access_list": ["вкл", "выкл"], "error": ""},
    "TEAM_STUD": {"abr": "Студ. команды", "type": "str", "max": "", "min": "", "access_list": ["вкл", "выкл"], "error": ""},
    "TEAM_FEMALE": {"abr": "Жен. команды", "type": "str", "max": "", "min": "", "access_list": ["вкл", "выкл"], "error": ""},
    "TEAM_JUNIOR": {"abr": "Юнош. команды", "type": "str", "max": "", "min": "", "access_list": ["вкл", "выкл"], "error": ""},
    "TOP": {"abr": "Только TOP", "type": "str", "max": "", "min": "", "access_list": ["вкл", "выкл"], "error": ""},
    "ML_NOISE": {"abr": "ML: исключить шум", "type": "str", "max": "", "min": "", "access_list": ["вкл", "выкл"], "error": ""},
    "POUR_INTO": {"abr": "Перелить в", "type": "str", "max": "", "min": "", "access_list": bks, "error": ""},
    "DOUBLE_BET": {"abr": "Дубли ставок", "type": "str", "max": "", "min": "", "access_list": ["вкл", "выкл"], "error": ""},
    "MAX_BET_FONBET": {"abr": "MAX BET в Fonbet", "type": "int", "max": "500", "min": "0", "access_list": ["0", "100", "200", "300", "400", "500"], "error": ""},
    "SERVER_OLIMP": {"abr": "Сервер Олимп", "type": "str", "max": "", "min": "", "access_list": [], "error": ""},

    # "SERVER_IP_TEST": {"abr": "IP-адрес тест. сервера", "type": "", "max": "", "min": "", "access_list": [], "error": ""},
    # "SERVER_IP": {"abr": "IP-адрес бой сервера", "type": "", "max": "", "min": "", "access_list": [], "error": ""},
    # "WORK_HOUR": {"abr": "Работаю (ч.)", "type": "", "max": "", "min": "", "access_list": [], "error": ""},
    # "HARD_BET_RIGHT": {"abr": "Жесткая ставка второго плеча", "type": "", "max": "", "min": "", "access_list": [], "error": ""},
}


def get_trunc_sysdate(days=0):
    return round(time.time() + days * 60 * 60 * 24)


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    id = PrimaryKeyField(unique=True)
    role = CharField(null=False, default='client')
    phone = CharField(null=False)
    email = CharField(null=False)
    date_start = IntegerField(null=False, default=get_trunc_sysdate())
    date_end = IntegerField(null=True)


class Account(BaseModel):
    id = AutoField
    key = CharField(unique=True)
    user = ForeignKeyField(User, backref='accounts')
    status = CharField(null=False, default='active')
    work_stat = CharField(null=False, default='stop')
    pid = IntegerField(null=False, default=0)
    work_dir = CharField(null=True)
    proxies = CharField(null=True, max_length=4096)
    accounts = CharField(null=True, max_length=4096)
    time_start = IntegerField(null=True)
    time_stop = IntegerField(null=True)
    date_start = IntegerField(null=False, default=get_trunc_sysdate())
    date_end = IntegerField(null=True)


class Message(BaseModel):
    id = AutoField
    to_user = IntegerField(null=False)
    text = CharField(null=True, max_length=4096)
    blob = BlobField(default='')
    file_name = CharField(null=True)
    file_type = CharField(null=True)
    date_send = IntegerField(null=True)


class Properties(BaseModel):
    acc = ForeignKeyField(Account, backref='properties')
    key = CharField(null=False)
    val = CharField(null=True)

    class Meta:
        indexes = ((('acc', 'key'), True),)


# API
def get_user(id: int):
    return User.get_by_id(id)


def get_user_str(id: int) -> str:
    res = ''
    data = get_user(id).__data__
    for key, val in data.items():
        if key and val:
            res = res + '*' + str(key) + '*: ' + str(val) + '\n'
    return res


def get_val_prop_id(id: int, key: str) -> str:
    res = 'auto'
    try:
        res = str(Properties.select().where((Properties.acc_id == id) & (Properties.key == key)).get().val)
    except Exception as e:
        print('key:' + key + ', ' + str(e))
    return res


def get_prop_str(id: int) -> str:
    res = ''

    info_accs = ''
    for key, val in loads(Account.get_by_id(id).accounts.replace('`', '"')).items():
        info_accs = info_accs + key.capitalize() + ': * ' + str(val.get('login')) + ' / ' + str(val.get('password')) + '*\n'

    for key, val in loads(Account.get_by_id(id).proxies.replace('`', '"')).items():
        info_accs = info_accs + key.capitalize() + ': * ' + str(val.get('http').replace('http://', '')) + '*\n'

    for key, val in prop_abr.items():
        res += '' + str(val.get('abr', '')) + ': *' + get_val_prop_id(id, key) + '*\n'
    return info_accs + res


def send_message_bot(user_id: int, msg: str, admin_list: dict = None):
    try:
        send_stat = str(Properties.select().where((Properties.key == 'SEND_MESSAGE') & (Properties.acc_id == 2)).get().val)
    except Exception:
        send_stat = '0'

    is_send_admin = False
    if admin_list:
        is_send_admin = user_id in admin_list

    if send_stat != '0' and not is_send_admin:
        Message.insert({
            Message.to_user: user_id,
            Message.text: msg,
            Message.file_type: 'message'
        }).execute()

    if admin_list:
        for admin_id in admin_list:
            Message.insert({
                Message.to_user: admin_id,
                Message.text: msg,
                Message.file_type: 'message'
            }).execute()


if __name__ == '__main__':
    pass
