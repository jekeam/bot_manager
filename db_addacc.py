# coding:utf-8
from db_model import *
from json import loads, dumps

if __name__ == '__main__':
    uid = uuid1()

    CNT_DAYS = 30
    USER_ID = 94974020
    COPY_PROP_ACC_ID = 62

    # PROXY
    # user name
    user = 'gregorantonenko'
    # password
    pswd = 'Y1p3PeY'
    # ip
    ip = '191.101.89.187'
    # port
    port = '65233'

    # BK
    # olimp
    olu = '3510429'
    olp = 'R588321Q'

    # fonbet
    fbu = '7860574'
    fbp = 'tdP0468r'

    proxy = user + ':' + pswd + '@' + ip + ':' + port
    proxies = '{`fonbet`:{`http`:`http://' + proxy + '`,`https`:`https://' + proxy + '`},`olimp`:{`http`:`http://' + proxy + '`,`https`:`https://' + proxy + '`}}'
    accounts = '{`olimp`:{`login`:`' + olu + '`,`password`:`' + olp + '`,`mirror`:`olimp.com`},`fonbet`:{`login`:' + fbu + ',`password`:`' + fbp + '`,`mirror`:`fonbet.com`}}'
    try:
        acc = Account.create(
            # user id from telegram
            user=USER_ID,
            key=uid,
            date_end=get_trunc_sysdate(CNT_DAYS),  # cnt days
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
