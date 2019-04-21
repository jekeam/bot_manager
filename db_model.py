# coding: utf-8
from peewee import *
import time
from json import dumps
from uuid import uuid1
from playhouse.sqlite_ext import SqliteExtDatabase

# db = SqliteExtDatabase(
#     'bot_manager.db',
#     pragmas=(
#         ('cache_size', -1024 * 64),  # 64MB page-cache.
#         ('journal_mode', 'wal'),  # Use WAL-mode (you should always use this!).
#         ('foreign_keys', 1)),
#     timeout=10
# )  # Enforce foreign-key constraints.

# db = SqliteDatabase('bot_manager.db', thread_safe=False, check_same_thread=False, )
db = MySQLDatabase('bot_manager', user='root', password='131189_Ak13', host='127.0.0.1', port=3306)
print('init DB')


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
def get_user(id):
    return User.get_by_id(id)


def prnt_user_str(id):
    res = ''
    data = get_user(id).__data__
    for key, val in data.items():
        if key and val:
            res = res + '*' + str(key) + '*: ' + str(val) + '\n'
    return res


def send_message_bot(user_id: int, msg: str, admin_list: dict = None):
    print('send_message_bot')
    try:
        send_stat = str(Properties.select().where((Properties.key == 'SEND_MESSAGE') & (Properties.acc_id == 2)).get().val)
    except Exception:
        send_stat = '0'

    print('send_stat: ' + str(send_stat) + ' ' + str(type(send_stat)))
    if send_stat != '0' and user_id not in admin_list:
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
    print(uuid1())
    # send_message_bot(381868674, 'HI')
