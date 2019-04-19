# coding: utf-8
from peewee import *
import time
from json import dumps
from uuid import uuid1

db = SqliteDatabase('bot_manager.db', threadlocals=True)


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
    proxies = CharField(null=False, unique=True)
    accounts = CharField(null=False, unique=True)
    time_start = IntegerField(null=True)
    time_stop = IntegerField(null=True)
    date_start = IntegerField(null=False, default=get_trunc_sysdate())
    date_end = IntegerField(null=False, default=get_trunc_sysdate(30))


class Message(BaseModel):
    id = AutoField
    to_user = IntegerField(null=False)
    text = CharField(null=True)
    blob = BlobField(null=True)
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
    Message.insert({
        Message.to_user: user_id,
        Message.text: msg,
        Message.file_type: 'message'
    }).execute()

    if admin_list:
        for admin_id in admin_list:
            if admin_id != user_id:
                Message.insert({
                    Message.to_user: admin_id,
                    Message.text: msg,
                    Message.file_type: 'message'
                }).execute()


if __name__ == '__main__':
    print(uuid1())
