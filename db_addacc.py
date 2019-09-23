# coding:utf-8
from db_model import *
from json import loads, dumps

if __name__ == '__main__':
    uid = uuid1()

    # PROXY
    # user name
    user = 'Selpodpoyasannyi'

    # password
    pswd = 'I5x7OsO'

    # ip
    ip = '91.200.150.28'

    # port
    port = '45785'

    # BK
    # olimp
    olu = '3177428'
    olp = 'dramma19'

    # fonbet
    fbu = '6539320'
    fbp = 'dramma19'

    proxy = user + ':' + pswd + '@' + ip + ':' + port
    proxies = '{`fonbet`:{`http`:`http://' + proxy + '`,`https`:`https://' + proxy + '`},`olimp`:{`http`:`http://' + proxy + '`,`https`:`https://' + proxy + '`}}'
    accounts = '{`olimp`:{`login`:`' + olu + '`,`password`:`' + olp + '`,`mirror`:`olimp.com`},`fonbet`:{`login`:' + fbu + ',`password`:`' + fbp + '`,`mirror`:`fonbet.com`}}'
    try:
        # acc = Account.create(
        #     # user id from telegram
        #     user=304415738,
        #     key=uid,
        #     date_end=get_trunc_sysdate(30),  # cnt days
        #     status='active',
        #     proxies=proxies,
        #     accounts=accounts
        # )

        # print(acc.id)

        prop = (
            Properties.insert_from(
                Properties.select(41, Properties.val, Properties.key).where(Properties.acc_id == 18),
                fields=[Properties.acc_id, Properties.val, Properties.key]
            ).execute()
        )
    except Exception as e:
        print(e)
    print('OK')

    # USERS
    # try:
    #     sasha = User.create(
    #         id=381868674,
    #         role='admin',
    #         phone='+79226727926',
    #         email='suinegne@gmail.com'
    #     )
    # except Exception as e:
    #     print(e)
    #
    # try:
    #     ai = User.create(
    #         id=33847743,
    #         role='admin',
    #         phone='+79823703090',
    #         email='a89823703090@gmail.com'
    #     )
    # except Exception as e:
    #     print(e)
    #
    # try:
    #     ruslan = User.create(
    #         id=103096112,
    #         role='user',
    #         phone='+79124023040',
    #         email='ruslan.fatyh@gmail.com'
    #     )
    # except Exception as e:
    #     print(e)
    #
    # try:
    #     azat = User.create(
    #         id=268653382,
    #         role='user',
    #         phone='+79033563426',
    #         email='azat.sharip@gmail.com'
    #     )
    # except Exception as e:
    #     print(e)
    #
    # try:
    #     pasha = User.create(
    #         id=204766698,
    #         role='user',
    #         phone='+79634744600',
    #         email='pa5ha.b9@gmail.com'
    #     )
    # except Exception as e:
    #     print(e)
    #
    # # ACCS
    # # 1
    # try:
    #     acc = Account.create(
    #         user=381868674,
    #         key='48447db4-5f9f-11e9-9fcf-2cfda1739afe',
    #         status='active',
    #         work_status='start',
    #         proxies=r'{"fonbet":{"http":"http://shaggy:hzsyk4@5.188.84.73:8656","https":"https://shaggy:hzsyk4@5.188.84.73:8656"},"olimp":{"http":"http://shaggy:hzsyk4@5.188.84.73:8656","https":"https://shaggy:hzsyk4@5.188.84.73:8656"}}',
    #         accounts=r'{"olimp":{"login":"3318188","password":"6ya8y4eK","mirror":"olimp.com"},"fonbet":{"login":5989155,"password":"6ya8y4eK","mirror":"fonbet.com"}}'
    #     )
    #     p = {
    #         "SUMM": 560,
    #         "RANDOM_SUMM_PROC": 30,
    #         "FORK_LIFE_TIME": 3,
    #         "SERVER_IP_TEST": "149.154.70.53",
    #         "SERVER_IP": "62.109.10.57",
    #         "WORK_HOUR": 8,
    #         "ROUND_FORK": 5,
    #         "MAX_FORK": 30,
    #         "MAX_FAIL": 4,
    #         "MIN_L": 1
    #     }
    #     for k, v in p.items():
    #         prop = Properties.create(acc=acc.id, key=k, val=v)
    #
    # except Exception as e:
    #     print('1')
    #     print(e)
    #
    # # 2
    # try:
    #     acc = Account.create(
    #         user=381868674,
    #         key='a28ad3f4-5f9e-11e9-8d15-DELETE',
    #         date_end=get_trunc_sysdate(),
    #         status='inactive',
    #         accounts=r'{}'
    #     )
    #
    #     p = {
    #         "SEND_MESSAGE": 0
    #     }
    #     for k, v in p.items():
    #         prop = Properties.create(acc=acc.id, key=k, val=v)
    # except Exception as e:
    #     print('FIX')
    #     print(e)
    # # 3
    # try:
    #     acc = Account.create(
    #         user=381868674,
    #         key='a28ad3f4-5f9e-11e9-8d15-2cfda1739afe',
    #         status='active',
    #         proxies=r'{"fonbet":{"http":"http://suineg:8veh34@212.90.108.153:3597","https":"https://suineg:8veh34@212.90.108.153:3597"},"olimp":{"http":"http://suineg:8veh34@212.90.108.153:3597","https":"https://suineg:8veh34@212.90.108.153:3597"}',
    #         accounts=r'{"olimp":{"login":"6265127","password":"qvF3BwrNcRcJtB6","mirror":"olimp.com"},"fonbet":{"login":5699838,"password":"NTe2904H11","mirror":"fonbet.com"}}'
    #     )
    #
    #     p = {
    #         "SUMM": 400,
    #         "RANDOM_SUMM_PROC": 30,
    #         "FORK_LIFE_TIME": 3,
    #         "SERVER_IP_TEST": "149.154.70.53",
    #         "SERVER_IP": "62.109.10.57",
    #         "WORK_HOUR": 8,
    #         "ROUND_FORK": 5,
    #         "MAX_FORK": 30,
    #         "MAX_FAIL": 6,
    #         "MIN_L": 1,
    #         "HARD_BET_RIGHT": 1
    #     }
    #     for k, v in p.items():
    #         prop = Properties.create(acc=acc.id, key=k, val=v)
    # except Exception as e:
    #     print('2')
    #     print(e)
    #
    # # 1
    # # 4
    # try:
    #     acc = Account.create(
    #         user=33847743,
    #         key='bbf009d6-62a8-11e9-b379-0242ac110019',
    #         status='active',
    #         proxies=r'{"fonbet":{"http":"http://shaggy:hzsyk4@191.101.104.71:4487","https":"https://shaggy:hzsyk4@191.101.104.71:4487"},"olimp":{"http":"http://shaggy:hzsyk4@191.101.104.71:4487","https":"https://shaggy:hzsyk4@191.101.104.71:4487"}}',
    #         accounts=r'{"olimp":{"login":"8834798","password":"!qRVcRUXz23","mirror":"olimp.com"},"fonbet":{"login":5987993,"password":"qRVcRUXz23","mirror":"fonbet.com"}}'
    #     )
    #
    #     p = {
    #         "SUMM": 2000,
    #         "RANDOM_SUMM_PROC": 0,
    #         "FORK_LIFE_TIME": 3,
    #         "SERVER_IP_TEST": "149.154.70.53",
    #         "SERVER_IP": "62.109.10.57",
    #         "WORK_HOUR": 13,
    #         "ROUND_FORK": 10,
    #         "MAX_FORK": 35,
    #         "MAX_FAIL": 3,
    #         "MIN_L": 0.988,
    #         "JUNIOR_TEAM_EXCLUDE": "YES"
    #     }
    #     for k, v in p.items():
    #         prop = Properties.create(acc=acc.id, key=k, val=v)
    # except Exception as e:
    #     print('3')
    #     print(e)
    #
    # # 7
    # # 5
    # try:
    #     acc = Account.create(
    #         user=33847743,
    #         key='16cb113c-62ab-11e9-a9f6-0242ac110019',
    #         status='active',
    #         proxies=r'{"fonbet":{"http":"http://shaggy:hzsyk4@185.20.187.33:6293","https":"https://shaggy:hzsyk4@185.20.187.33:6293"},"olimp":{"http":"http://shaggy:hzsyk4@185.20.187.33:6293","https":"https://shaggy:hzsyk4@185.20.187.33:6293"}}',
    #         accounts=r'{"olimp":{"login":"7751409","password":"KbqNK7m6","mirror":"olimp.com"},"fonbet":{"login":6690827,"password":"KbqNK7m6","mirror":"fonbet.com"}}'
    #     )
    #
    #     p = {
    #         "SUMM": 1750,
    #         "RANDOM_SUMM_PROC": 0,
    #         "FORK_LIFE_TIME": 3,
    #         "SERVER_IP_TEST": "149.154.70.53",
    #         "SERVER_IP": "62.109.10.57",
    #         "WORK_HOUR": 13,
    #         "ROUND_FORK": 10,
    #         "MAX_FORK": 35,
    #         "MAX_FAIL": 3,
    #         "MIN_L": 0.985,
    #         "JUNIOR_TEAM_EXCLUDE": "YES"
    #     }
    #     for k, v in p.items():
    #         prop = Properties.create(acc=acc.id, key=k, val=v)
    # except Exception as e:
    #     print('4')
    #     print(e)
    #
    # # 9
    # # 6
    # try:
    #     acc = Account.create(
    #         user=33847743,
    #         key='4ccb9568-62ab-11e9-bdab-0242ac110019',
    #         status='active',
    #         proxies=r'{"fonbet":{"http":"http://suineg:8veh34@193.22.96.101:4003","https":"https://suineg:8veh34@193.22.96.101:4003"},"olimp":{"http":"http://suineg:8veh34@193.22.96.101:4003","https":"https://suineg:8veh34@193.22.96.101:4003"}}',
    #         accounts=r'{"olimp":{"login":"5511370","password":"1n7vGT52","mirror":"olimp.com"},"fonbet":{"login":6698906,"password":"1n7vGT52","mirror":"fonbet.com"}}'
    #     )
    #
    #     p = {
    #         "SUMM": 590,
    #         "RANDOM_SUMM_PROC": 0,
    #         "FORK_LIFE_TIME": 3,
    #         "SERVER_IP_TEST": "149.154.70.53",
    #         "SERVER_IP": "62.109.10.57",
    #         "WORK_HOUR": 13,
    #         "ROUND_FORK": 10,
    #         "MAX_FORK": 35,
    #         "MAX_FAIL": 3,
    #         "MIN_L": 0.99,
    #         "JUNIOR_TEAM_EXCLUDE": "YES"
    #     }
    #     for k, v in p.items():
    #         prop = Properties.create(acc=acc.id, key=k, val=v)
    # except Exception as e:
    #     print('5')
    #     print(e)
    #
    # # 10
    # # 7
    # try:
    #     acc = Account.create(
    #         user=268653382,
    #         key='081b1414-62ad-11e9-bbd5-0242ac110019',
    #         date_end=get_trunc_sysdate(30),
    #         status='active',
    #         proxies=r'{"fonbet":{"http":"http://user23348:jkon1c@185.161.210.75:8979","https":"https://user23348:jkon1c@185.161.210.75:8979"},"olimp":{"http":"http://user23348:jkon1c@185.161.210.75:8979","https":"https://user23348:jkon1c@185.161.210.75:8979"}}',
    #         accounts=r'{"olimp":{"login":"azat.sharip@gmail.com","password":"o1l2i3m4p5","mirror":"olimp.com"},"fonbet":{"login":6839460,"password":"AB7NfBpe","mirror":"fonbet.com"}}'
    #     )
    #
    #     p = {
    #         "SUMM": 1000,
    #         "RANDOM_SUMM_PROC": 0,
    #         "FORK_LIFE_TIME": 3,
    #         "SERVER_IP_TEST": "149.154.70.53",
    #         "SERVER_IP": "62.109.10.57",
    #         "WORK_HOUR": 5,
    #         "ROUND_FORK": 10,
    #         "MAX_FORK": 10,
    #         "MAX_FAIL": 3,
    #         "MIN_L": 0.984,
    #         "JUNIOR_TEAM_EXCLUDE": "YES"
    #     }
    #     for k, v in p.items():
    #         prop = Properties.create(acc=acc.id, key=k, val=v)
    # except Exception as e:
    #     print('6')
    #     print(e)
    #
    # # 11
    # # 8
    # try:
    #     acc = Account.create(
    #         user=103096112,
    #         key='2223a4ba-62ae-11e9-96f0-0242ac110019',
    #         date_end=get_trunc_sysdate(30),
    #         status='active',
    #         proxies=r'{"fonbet":{"http":"http://user20426:5yrbn7@185.161.211.221:4223","https":"http://user20426:5yrbn7@185.161.211.221:4223"},"olimp":{"http":"http://user20426:5yrbn7@185.161.211.221:4223","https":"http://user20426:5yrbn7@185.161.211.221:4223"}}',
    #         accounts=r'{"olimp":{"login":"4722604","password":"alrusft174","mirror":"olimp.com"},"fonbet":{"login":6851562,"password":"alrusft174","mirror":"fonbet.com"}}'
    #     )
    #
    #     p = {
    #         "SUMM": 560,
    #         "RANDOM_SUMM_PROC": 0,
    #         "FORK_LIFE_TIME": 3,
    #         "SERVER_IP_TEST": "149.154.70.53",
    #         "SERVER_IP": "62.109.10.57",
    #         "WORK_HOUR": 13,
    #         "ROUND_FORK": 10,
    #         "MAX_FORK": 30,
    #         "MAX_FAIL": 3,
    #         "MIN_L": 0.99,
    #         "JUNIOR_TEAM_EXCLUDE": "YES"
    #     }
    #     for k, v in p.items():
    #         prop = Properties.create(acc=acc.id, key=k, val=v)
    # except Exception as e:
    #     print('7')
    #     print(e)
    #
    # # 12
    # # 9
    # try:
    #     acc = Account.create(
    #         user=204766698,
    #         key='c8f8f470-62ae-11e9-8a2c-0242ac110019',
    #         date_end=get_trunc_sysdate(30),
    #         status='active',
    #         proxies=r'{"fonbet":{"http":"http://user23688:unprt4@185.20.184.48:1482", {"https":"https://user23688:unprt4@185.20.184.48:1482"},"olimp":{"http":"http://user23688:unprt4@185.20.184.48:1482","https":"https://user23688:unprt4@185.20.184.48:1482"}}',
    #         accounts=r'{"olimp":{"login":"436652","password":"kUemDVnCTkhpkg68","mirror":"olimp.com"},"fonbet":{"login":6840364,"password":"bwzRNq48vK9rxpBt","mirror":"fonbet.com"}}'
    #     )
    #
    #     p = {
    #         "SUMM": 400,
    #         "RANDOM_SUMM_PROC": 0,
    #         "FORK_LIFE_TIME": 3,
    #         "SERVER_IP_TEST": "149.154.70.53",
    #         "SERVER_IP": "62.109.10.57",
    #         "WORK_HOUR": 12,
    #         "ROUND_FORK": 10,
    #         "MAX_FORK": 15,
    #         "MAX_FAIL": 3,
    #         "MIN_L": 0.98,
    #         "JUNIOR_TEAM_EXCLUDE": "YES"
    #     }
    #     for k, v in p.items():
    #         prop = Properties.create(acc=acc.id, key=k, val=v)
    # except Exception as e:
    #     print('8')
    #     print(e)
    #
    # for x in Account().select():
    #     js = x.__dict__.get('__data__')
    #     print(js.get('user'), js.get('id'), js.get('key'), js.get('accounts'))
    # # Account.delete().execute()
