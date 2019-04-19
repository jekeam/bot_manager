# coding: utf-8
from db_model import *

db.connect()
db.create_tables([User, Account, Message, Properties])