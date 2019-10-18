# coding:utf-8
from db_model import *
from json import loads, dumps

if __name__ == '__main__':
    uid = uuid1()

    # PROXY
    # user name
    user = 'RmUekb'
    # password
    pswd = 'AKmHD3'
    # ip
    ip = '194.93.24.230'
    # port
    port = '8000'

    # BK
    # olimp
    olu = '6519761'
    olp = '51381583skottY'

    # fonbet
    fbu = '7831532'
    fbp = 'uadWaBg7'

    proxy = user + ':' + pswd + '@' + ip + ':' + port
    proxies = '{`fonbet`:{`http`:`http://' + proxy + '`,`https`:`https://' + proxy + '`},`olimp`:{`http`:`http://' + proxy + '`,`https`:`https://' + proxy + '`}}'
    accounts = '{`olimp`:{`login`:`' + olu + '`,`password`:`' + olp + '`,`mirror`:`olimp.com`},`fonbet`:{`login`:' + fbu + ',`password`:`' + fbp + '`,`mirror`:`fonbet.com`}}'
    try:
        acc = Account.create(
            # user id from telegram
            user=960286150,
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
    except Exception as e:
        print(e)
    print('OK')
