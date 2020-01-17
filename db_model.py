# coding: utf-8
from peewee import *
import time
from json import dumps, loads
from uuid import uuid1
from playhouse.sqlite_ext import SqliteExtDatabase

db = MySQLDatabase('bot_manager', user='root', password='131189_Ak', host='127.0.0.1', port=3306)
# db = MySQLDatabase('bot_manager', user='phpmyadmin', password='some_pass', host='127.0.0.1', port=3306)


# first_bet_in = ["created", "notcreator", "fonbet", "olimp", "parallel", "auto"]
first_bet_in = ["fonbet", "olimp", "auto"]

bks = ["fonbet", "olimp", "auto"]
on_off = ["вкл", "выкл"]

flex_bet_arr = ["any", "up", "no"]
flex_kof_arr = ["yes", "no"]

prop_abr = {
    "FONBET_U": {"abr": "УЗ Фонбет", "type": "account:fonbet", "max": "", "min": "", "error": ""},
    "FONBET_P": {"abr": "Прокси Фонбет", "type": "proxi:fonbet", "max": "", "min": "", "error": ""},

    "OLIMP_U": {"abr": "УЗ Олимп", "type": "account:olimp", "max": "", "min": "", "error": ""},
    "OLIMP_P": {"abr": "Прокси Олимп", "type": "proxi:olimp", "max": "", "min": "", "error": ""},

    "FONBET_MIRROR": {"abr": "Зеркало Фонбета", "type": "mirror:fonbet", "max": "", "min": "", "error": ""},
    "FONBET_S": {"abr": "Сервер Фонбета", "type": "str", "max": "", "min": "", "access_list": ["ru", "com"], "error": ""},

    "FLEX_BET1": {"abr": "1. Измен-е коэф-та", "type": "str", "max": "", "min": "", "access_list": flex_bet_arr, "default": "up", "error": ""},
    "FLEX_BET2": {"abr": "2. Измен-е коэф-та", "type": "str", "max": "", "min": "", "access_list": flex_bet_arr, "default": "no", "error": ""},

    "FLEX_KOF1": {"abr": "1. Измен-е катир-ки", "type": "str", "max": "", "min": "", "access_list": flex_kof_arr, "default": "no", "error": ""},
    "FLEX_KOF2": {"abr": "2. Измен-е катир-ки", "type": "str", "max": "", "min": "", "access_list": flex_kof_arr, "default": "no", "error": ""},

    "FORK_SLICE": {"abr": "Уникальность ставок, %", "type": "int", "max": "90", "min": "0", "access_list": [], "error": ""},

    "MIN_PROC": {"abr": "% Вилки ОТ", "type": "float", "max": "10", "min": "0", "access_list": [], "error": ""},  # !
    "MAX_PROC": {"abr": "% Вилки ДО", "type": "float", "max": "999", "min": "0.1", "access_list": [], "error": ""},  # !

    "FORK_LIFE_TIME": {"abr": "Вилки ОТ сек.", "type": "int", "max": "998", "min": "0", "access_list": [], "error": ""},  # !
    "FORK_LIFE_TIME_MAX": {"abr": "Вилки ДО сек.", "type": "int", "max": "9999", "min": "1", "access_list": [], "error": ""},  # !

    "MAX_FORK": {"abr": "MAX ставок", "type": "int", "max": "100", "min": "1", "access_list": [], "error": ""},
    "MAX_FAIL": {"abr": "MAX выкупов", "type": "int", "max": "10", "min": "1", "access_list": [], "error": ""},

    "SUMM": {"abr": "Общая ставка", "type": "int", "max": "10000", "min": "90", "access_list": [], "default": 500, "error": ""},
    "SUMM_MIN": {"abr": "Ставка ОТ", "type": "int", "max": "10000", "min": "90", "access_list": [], "default": 90, "error": ""},

    "WORK_HOUR_END": {"abr": "Остановка в", "type": "int", "max": "23", "min": "0", "access_list": [], "error": ""},
    "ROUND_FORK": {"abr": "Округление", "type": "int", "max": "", "min": "", "access_list": ["1", "5", "10", "50", "100"], "error": ""},

    "MAXBET_FACT": {"abr": "Мaxbet по ведущему", "type": "str", "max": "", "min": "", "access_list": on_off, "error": ""},
    "CHECK_MAX_BET": {"abr": "Проверка maxbet", "type": "str", "max": "", "min": "", "access_list": on_off, "error": ""},
    "SUM_BY_MAX": {"abr": "Пересчет maxbet", "type": "str", "max": "", "min": "", "access_list": on_off, "error": ""},
    "PROC_BY_MAX": {"abr": "% от maxbet", "type": "int", "max": "100", "min": "10", "access_list": [], "error": ""},

    "TIMEOUT_FORK": {"abr": "Ждать после ставки", "type": "int", "max": "5400", "min": "120", "default": 180, "access_list": [], "error": ""},

    "TEAM_RES": {"abr": "Рез-е команды", "type": "str", "max": "", "min": "", "access_list": on_off, "error": ""},
    "TEAM_STUD": {"abr": "Студ. команды", "type": "str", "max": "", "min": "", "access_list": on_off, "error": ""},
    "TEAM_FEMALE": {"abr": "Жен. команды", "type": "str", "max": "", "min": "", "access_list": on_off, "error": ""},
    "TEAM_JUNIOR": {"abr": "Юнош. команды", "type": "str", "max": "", "min": "", "access_list": on_off, "error": ""},

    "TOP": {"abr": "Только TOP матчи", "type": "str", "max": "", "min": "", "access_list": on_off, "error": ""},
    "HOT": {"abr": "Только TOP катировки", "type": "str", "max": "", "min": "", "access_list": on_off, "error": ""},
    "ONE_BET": {"abr": "1 ставка на матч", "type": "str", "max": "", "min": "", "access_list": on_off, "error": ""},
    "RANDOM_SUMM_PROC": {"abr": "% Разброс ставки", "type": "int", "max": "30", "min": "0", "access_list": [], "error": ""},
    # "FORK_TIME_TYPE": {"abr": "Тип времени вилки", "type": "str", "max": "", "min": "", "access_list": ["текущее", "общее"], "error": ""},
    "FIRST_BET_IN": {"abr": "Первая ставка в", "type": "str", "max": "", "min": "", "access_list": first_bet_in, "default": "auto", "error": ""},
    "TOTAL_FIRST": {"abr": "Первая ставка на Тот.", "type": "str", "max": "", "min": "", "access_list": ["ТМ", "ТБ", "any"], "default": "ТМ", "error": ""},
    "MAX_KOF": {"abr": "MAX коэф-т", "type": "float", "max": "1000", "min": "1.02", "access_list": [], "error": ""},
    "ML_NOISE": {"abr": "ML. Olimp UP", "type": "str", "max": "", "min": "", "access_list": on_off, "error": "", "default": "выкл", },
    # "POUR_INTO": {"abr": "Перелить в", "type": "str", "max": "", "min": "", "access_list": bks, "error": ""},
    "DOUBLE_BET": {"abr": "Дубли ставок", "type": "str", "max": "", "min": "", "access_list": on_off, "error": ""},
    "MAX_BET_FONBET":
        {
            "abr": "MAX BET в Fonbet", "type": "int", "max": "1000", "min": "0",
            "access_list": ["0", "50", "90", "100", "200", "300", "400", "500", "600", "700", "800", "900", "1000"], "error": ""
        },
    # "SERVER_OLIMP": {"abr": "Сервер Олимп", "type": "str", "max": "", "min": "", "access_list": [], "error": ""},
    "TEST_OTH_SPORT": {"abr": "Новые виды спорта", "type": "str", "max": "", "min": "", "access_list": on_off, "error": ""},

    "PLACE": {"abr": "Ставить на прематч", "type": "str", "max": "", "min": "", "access_list": ["any", "live", "pre"], "default": "live", "error": ""},
    "PLACE_TIME": {"abr": "Прематчи до(часов)", "type": "int", "max": "24", "min": "1", "access_list": "", "default": "2", "error": ""},

    "FORA": {"abr": "Ставить на форы", "type": "str", "max": "", "min": "", "access_list": on_off, "default": "вкл", "error": ""},
    "SALE_BET": {"abr": "НЕвыкуп при потере, %", "type": "int", "max": "100", "min": "0", "access_list": [], "error": ""},
    # "SERVER_IP_TEST": {"abr": "IP-адрес тест. сервера", "type": "", "max": "", "min": "", "access_list": [], "error": ""},
    # "SERVER_IP": {"abr": "IP-адрес бой сервера", "type": "", "max": "", "min": "", "access_list": [], "error": ""},
    # "WORK_HOUR": {"abr": "Работаю (ч.)", "type": "", "max": "", "min": "", "access_list": [], "error": ""},
    # "HARD_BET_RIGHT": {"abr": "Жесткая ставка второго плеча", "type": "", "max": "", "min": "", "access_list": [], "error": ""},
}

prop_spr = {
    "FLEX_BET1": "Как действует бот при первой ставке, если в момент ставки произошли изменения коф-та, например 1.35 -> 1.45, any - принимает всегда, неважно куда двинулся коф." + \
                 ", up - только если ушел вверх, no - не принимать при изменении(сделано только для 100% пересчета суммы ставки) в этом случае бот будет пересчитывать суммы ставки и все равно менять коф-т на нужный.",
    "FLEX_BET2": "Как действует бот при второй ставке, если в момент ставки произошли изменения коф-та, например 1.35 -> 1.45, any - принимает всегда, неважно куда двинулся коф." + \
                 ", up - только если ушел вверх, no - не принимать при изменении(сделано только для 100% пересчета суммы ставки) в этом случае бот будет пересчитывать суммы ставки и все равно менять коф-т на нужный.",

    "FLEX_KOF1": "Как действует бот при первой ставке, если в момент ставки исчет тотал/фора. Принимать с измененными тоталами/форами: yes-да, no-нет",
    "FLEX_KOF2": "Как действует бот при второй ставке, если в момент ставки исчет тотал/фора. Принимать с измененными тоталами/форами: yes-да, no-нет",

}

exclude_copy = ('FONBET_P', 'FONBET_S', 'FONBET_U', 'OLIMP_P', 'OLIMP_U')
exclude_all = ('ML_NOISE', 'TOTAL_FIRST', 'FLEX_BET1', 'FLEX_BET2', 'FLEX_KOF1', 'FLEX_KOF2', 'PLACE', 'PLACE_TIME')
exclude_user = ('TEST_OTH_SPORT', 'MAXBET_FACT')

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
    # TODO unique=True
    proxies = CharField(null=True, max_length=4096)
    # TODO unique=True
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
    res = prop_abr.get(key.upper(), {}).get('default', 'auto')
    try:
        res = str(Properties.select().where((Properties.acc_id == id) & (Properties.key == key)).get().val)
    except Exception as e:
        pass
    # print('key:' + str(key) + ', res: ' + str(res))
    return res


def get_prop_str(id: int) -> str:
    res = ''

    info_accs = ''
    for key, val in loads(Account.get_by_id(id).accounts.replace('`', '"')).items():
        info_accs = info_accs + key.capitalize() + ': * ' + str(val.get('login', '')) + ' / ' + str(val.get('password')) + '*\n'

    for key, val in loads(Account.get_by_id(id).proxies.replace('`', '"')).items():
        info_accs = info_accs + key.capitalize() + ': * ' + str(val.get('http', '').replace('http://', '')) + '*\n'

    for key, val in prop_abr.items():
        if key not in ('FONBET_U', 'FONBET_P', 'OLIMP_U', 'OLIMP_P'):
            res += '' + str(val.get('abr', '')) + ': *' + str(get_val_prop_id(id, key)) + '*\n'
    return info_accs + res


def send_message_bot(user_id: int, msg: str, admin_list=None):
    Message.insert({
        Message.to_user: user_id,
        Message.text: msg.strip(),
        Message.file_type: 'message'
    }).execute()

    if admin_list:
        for admin_id in admin_list:
            if user_id != admin_id:
                Message.insert({
                    Message.to_user: admin_id,
                    Message.text: msg.strip(),
                    Message.file_type: 'message'
                }).execute()
    return True


if __name__ == '__main__':
    pass
