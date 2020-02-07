# coding:utf-8
import sys
import db_model
import bot_prop

arg = sys.argv[1]
val = sys.argv[2]
if arg == '--m':
    msg = val
    for admin in bot_prop.ADMINS:
        db_model.send_message_bot(admin, msg)