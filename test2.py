from db_model import *

for acc in Account.select().where((Account.status == 'active')):
    print(acc.pid, acc.id)