# coding:utf-8
import sys
import db_model
import bot_prop
print(sys.argv)
msg = sys.argv[1]
channels_id = ['@auto_bro_scan', ]
if msg:
    # for admin in bot_prop.ADMINS:
    #     db_model.send_message_bot(admin, msg)
    for id in channels_id:
        db_model.send_message_bot(id, msg)