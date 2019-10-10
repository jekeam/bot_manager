# coding:utf-8
from db_model import *
from json import loads, dumps

if __name__ == '__main__':
    uid = uuid1()

    # PROXY
    # user name
    user = '8Mgb7T'
    # password
    pswd = 'APbTvw'
    # ip
    ip = '37.9.38.116'
    # port
    port = '8000'

    # BK
    # olimp
    olu = '3720913'
    olp = 'W594159t'

    # fonbet
    fbu = '6601646'
    fbp = 'prosto4251'

    proxy = user + ':' + pswd + '@' + ip + ':' + port
    proxies = '{`fonbet`:{`http`:`http://' + proxy + '`,`https`:`https://' + proxy + '`},`olimp`:{`http`:`http://' + proxy + '`,`https`:`https://' + proxy + '`}}'
    accounts = '{`olimp`:{`login`:`' + olu + '`,`password`:`' + olp + '`,`mirror`:`olimp.com`},`fonbet`:{`login`:' + fbu + ',`password`:`' + fbp + '`,`mirror`:`fonbet.com`}}'
    try:
        acc = Account.create(
            # user id from telegram
            user=268653382,
            key=uid,
            # date_end=get_trunc_sysdate(30),  # cnt days
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
