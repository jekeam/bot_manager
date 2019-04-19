# coding:utf-8
from db_model import *

for acc in User.select().where(User.id == 381868674):
    send_message_bot(acc.id, 'Прошу прощения за спам. Возникили сложно с отправкой сообщений, на работу аккаунтов это ни как ни повлияло.')
