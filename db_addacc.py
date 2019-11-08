# coding:utf-8
from db_model import *
from json import loads, dumps

if __name__ == '__main__':
    uid = uuid1()

    CNT_DAYS = 30
    USER_ID = 370304750
    COPY_PROP_ACC_ID = 5

    # PROXY
    # user name
    user = 'r0nin87'
    # password
    pswd = 'I8w0JmG'
    # ip
    ip = 'XXX'
    # port
    port = '65233'

    # BK
    # fonbet
    fbu = '7948863'
    fbp = 'A161616a'
    # olimp
    olu = 'petrovichvan@bk.ru'
    olp = 'A161616a'

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
