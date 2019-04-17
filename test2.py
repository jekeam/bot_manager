from db_model import *

Message.update(date_send=None).where(1==1).execute
msg = Message.select().where(Message.date_send.is_null())
for x in msg:
    print(x)