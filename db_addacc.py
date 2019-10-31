# coding:utf-8
from db_model import *
from json import loads, dumps

if __name__ == '__main__':
    uid = uuid1()

    CNT_DAYS = 0
    USER_ID = 381868674
    COPY_PROP_ACC_ID = 18

    # PROXY
    # user name
    user = 'yuAQgR'
    # password
    pswd = 'E9tBqq'
    # ip
    ip = '5.8.22.190'
    # port
    port = '8000'

    # BK
    # fonbet
    fbu = '6690827'
    fbp = 'KbqNK7m6'
    # olimp
    olu = '7751409'
    olp = 'KbqNK7m6'

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
