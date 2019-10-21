# coding:utf-8
from db_model import *
from json import loads, dumps

if __name__ == '__main__':
    uid = uuid1()

    # PROXY
    # user name
    user = 'apollo1'
    # password
    pswd = 'f0h23w'
    # ip
    ip = '176.124.34.200'
    # port
    port = '3429'

    # BK
    # olimp
    olu = '4412579'
    olp = 'Russia777'

    # fonbet
    fbu = '6504919'
    fbp = 'TT2Qq81D'

    proxy = user + ':' + pswd + '@' + ip + ':' + port
    proxies = '{`fonbet`:{`http`:`http://' + proxy + '`,`https`:`https://' + proxy + '`},`olimp`:{`http`:`http://' + proxy + '`,`https`:`https://' + proxy + '`}}'
    accounts = '{`olimp`:{`login`:`' + olu + '`,`password`:`' + olp + '`,`mirror`:`olimp.com`},`fonbet`:{`login`:' + fbu + ',`password`:`' + fbp + '`,`mirror`:`fonbet.com`}}'
    try:
        acc = Account.create(
            # user id from telegram
            user=499633131,
            key=uid,
            date_end=get_trunc_sysdate(30),  # cnt days
            status='active',
            proxies=proxies,
            accounts=accounts
        )

        prop = (
            Properties.insert_from(
                Properties.select(acc.id, Properties.val, Properties.key).where(Properties.acc_id == 62),
                fields=[Properties.acc_id, Properties.val, Properties.key]
            ).execute()
        )
        print(acc)
    except Exception as e:
        print(e)
    print('OK')
