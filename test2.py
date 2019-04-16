from db_model import *

for acc in Account.select():
    print(acc.get().pid)