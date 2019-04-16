# coding: utf-8
from db_model import *

db.connect()
db.create_tables([User, Account, Message])

try:
    sasha = User.create(
        id=381868674,
        role='admin',
        phone='+79226727926',
        email='suinegne@gmail.com',
        date_end=get_trunc_sysdate(30000)
    )
except Exception as e:
    print(e)

try:
    ai = User.create(
        id=33847743,
        role='admin',
        phone='+79823703090',
        email='a89823703090@gmail.com',
        date_end=get_trunc_sysdate(30000)
    )
except Exception as e:
    print(e)
