# coding: utf-8
from peewee import *
import datetime
from json import dumps
from uuid import uuid1

db = SqliteDatabase('bot_manager.db')

def get_trunc_sysdate(days=0):
    dt = datetime.datetime.now()+datetime.timedelta(days=days)
    return datetime.datetime(year=dt.year, month=dt.month, day=dt.day)

class BaseModel(Model):
    class Meta:
        database = db
        
class User(BaseModel):
    id = PrimaryKeyField(unique=True)
    rules = CharField(null=False, default='client')
    phone = CharField(null=False)
    email = CharField(null=False)
    date_start = DateField(null=False, default=get_trunc_sysdate())
    date_end = DateField(null=False, default=get_trunc_sysdate(30))
    
class Account(BaseModel):
    id = AutoField
    key = CharField(unique=True)
    user = ForeignKeyField(User, backref='accounts')
    work_dir = CharField(null=False)
    properties = CharField(null=False)
    proxies = CharField(null=False)
    accounts = CharField(null=False)
    status = CharField(null=False, default='active')
    work_stat = CharField(null=False, default='stop')
    date_start = DateField(null=False, default=get_trunc_sysdate())
    date_end = DateField(null=False, default=get_trunc_sysdate(30))


#API
def get_user(id):
    return User.get_by_id(id)
    
def prnt_user_str(id):
    res = ''
    data = get_user(id).__data__
    for key, val in data.items():
        res = res + '*' + str(key) + '*: ' + str(val) + '\n'
    return res
    
if __name__=='__main__':
    print(uuid1())
            