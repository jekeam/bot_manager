# coding:utf-8
from db_model import *
from json import loads, dumps

if __name__ == '__main__':
    uid = uuid1()

    CNT_DAYS = 30
    USER_ID = 442965345
    COPY_PROP_ACC_ID = 62

    # PROXY
    # user name
    user = 'kirill102'
    # password
    pswd = '8m5fuz'
    # ip
    ip = '91.188.220.28'
    # port
    port = '9666'

    # BK
    # fonbet
    fbu = '6066930'
    fbp = 'BeD063ns'
    # olimp
    olu = 'kirillnazarov102@mail.ru'
    olp = 'zmnation102'

    proxy = user + ':' + pswd + '@' + ip + ':' + port
    proxies = '{`fonbet`:{`http`:`http://' + proxy + '`,`https`:`https://' + proxy + '`},`olimp`:{`http`:`http://' + proxy + '`,`https`:`https://' + proxy + '`}}'
    accounts = '{`olimp`:{`login`:`' + olu + '`,`password`:`' + olp + '`,`mirror`:`olimp.com`},`fonbet`:{`login`:' + fbu + ',`password`:`' + fbp + '`,`mirror`:`fonbet.com`}}'
    if CNT_DAYS:
        date_end = get_trunc_sysdate(CNT_DAYS)
    else:
        date_end = None
    try:
        acc = Account.create(
            # user id from telegram
            user=USER_ID,
            key=uid,
            date_end=date_end,  # cnt days
            status='active',
            proxies=proxies,
            accounts=accounts
        )

        prop = (
            Properties.insert_from(
                Properties.select(acc.id, Properties.val, Properties.key).where(Properties.acc_id == COPY_PROP_ACC_ID),
                fields=[Properties.acc_id, Properties.val, Properties.key]
            ).execute()
        )
        print(acc)
    except Exception as e:
        print(e)
    print('OK')
