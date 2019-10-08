# coding:utf-8
from db_model import *
from json import loads, dumps

if __name__ == '__main__':
    uid = uuid1()

    # PROXY
    # user name
    user = 'vhceAP'
    # password
    pswd = 'bzm3YT'
    # ip
    ip = '196.18.2.118'
    # port
    port = '8000'

    # BK
    # olimp
    olu = '9978278'
    olp = 'sTart43sPo'

    # fonbet
    fbu = '4176860'
    fbp = 'dwz1bnDc'

    proxy = user + ':' + pswd + '@' + ip + ':' + port
    proxies = '{`fonbet`:{`http`:`http://' + proxy + '`,`https`:`https://' + proxy + '`},`olimp`:{`http`:`http://' + proxy + '`,`https`:`https://' + proxy + '`}}'
    accounts = '{`olimp`:{`login`:`' + olu + '`,`password`:`' + olp + '`,`mirror`:`olimp.com`},`fonbet`:{`login`:' + fbu + ',`password`:`' + fbp + '`,`mirror`:`fonbet.com`}}'
    try:
        acc = Account.create(
            # user id from telegram
            user=782928513,
            key=uid,
            date_end=get_trunc_sysdate(30),  # cnt days
            status='active',
            proxies=proxies,
            accounts=accounts
        )

        prop = (
            Properties.insert_from(
                Properties.select(acc.id, Properties.val, Properties.key).where(Properties.acc_id == 18),
                fields=[Properties.acc_id, Properties.val, Properties.key]
            ).execute()
        )
    except Exception as e:
        print(e)
    print('OK')
