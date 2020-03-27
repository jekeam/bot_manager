# coding:utf-8
import sys
import db_model
import bot_prop
print(sys.argv)
msg = sys.argv[1]
for_admin = sys.argv[2]
channels_id = ['-1001334950920', ]
if msg:
    if for_admin == 'True':
        for admin in bot_prop.ADMINS:
            db_model.send_message_bot(admin, msg)
    else:
        for id in channels_id:
            db_model.send_message_bot(id, msg)