# coding:utf-8
from db_model import *
from json import loads, dumps

if __name__ == '__main__':
    # USERS
    try:
        sasha = User.create(
            id=381868674,
            role='admin',
            phone='+79226727926',
            email='suinegne@gmail.com',
            date_end=get_trunc_sysdate(30000)
        )
    except Exception as e:
        print(e)
    
    try:
        ai = User.create(
            id=33847743,
            role='admin',
            phone='+79823703090',
            email='a89823703090@gmail.com',
            date_end=get_trunc_sysdate(30000)
        )
    except Exception as e:
        print(e)
        
        
    # ACCS
    try:
        acc = Account.create(
            user=381868674,
            key='48447db4-5f9f-11e9-9fcf-2cfda1739afe',
            date_end=get_trunc_sysdate(30000),
            status='active',
            work_status='start',
            proxies=r'{ "fonbet": { "http": "http://shaggy:hzsyk4@5.188.84.73:8656", "https": "https://shaggy:hzsyk4@5.188.84.73:8656" }, "olimp": { "http": "http://shaggy:hzsyk4@5.188.84.73:8656", "https": "https://shaggy:hzsyk4@5.188.84.73:8656" } }',
            accounts=r'{ "olimp": { "login": "3318188", "password": "6ya8y4eK", "mirror": "olimp.com" }, "fonbet": { "login": 5989155, "password": "6ya8y4eK", "mirror": "fonbet.com" } }'
        )
        p = {
            "SUMM": 560, 
            "RANDOM_SUMM_PROC": 30, 
            "FORK_LIFE_TIME": 3, 
            "SERVER_IP_TEST": "149.154.70.53", 
            "SERVER_IP": "62.109.10.57", 
            "WORK_HOUR": 8, 
            "ROUND_FORK": 5, 
            "MAX_FORK": 30, 
            "MAX_FAIL": 4, 
            "MIN_L": 1
        }
        for k, v in p.items():
            prop = Properties.create(acc=acc.id, key=k, val=v)
            
    except Exception as e:
        print(e)

    try:
        acc = Account.create(
            # user=33847743,
            user=381868674,
            key='a28ad3f4-5f9e-11e9-8d15-DELETE',
            date_end=get_trunc_sysdate(30000),
            status='inactive',
            proxies=r'{"fonbet": {"http": "http://suineg:8veh34@212.90.108.153:3597","https": "https://suineg:8veh34@212.90.108.153:3597"},"olimp": {"http": "http://suineg:8veh34@212.90.108.153:3597","https": "https://suineg:8veh34@212.90.108.153:3597"},"bet365": {"http": "","https": ""}}',
            accounts=r'{"olimp": {"login": "6265127","password": "qvF3BwrNcRcJtB6","mirror": "olimp.com"},"fonbet": {"login": 5699838,"password": "NTe2904H11","mirror": "fonbet.com"}}'
        )
         
    except Exception as e:
        print(e)
        

    try:
        acc = Account.create(
            # user=33847743,
            user=381868674,
            key='a28ad3f4-5f9e-11e9-8d15-2cfda1739afe',
            date_end=get_trunc_sysdate(30000),
            status='active',
            proxies=r'{"fonbet": {"http": "http://suineg:8veh34@212.90.108.153:3597","https": "https://suineg:8veh34@212.90.108.153:3597"},"olimp": {"http": "http://suineg:8veh34@212.90.108.153:3597","https": "https://suineg:8veh34@212.90.108.153:3597"},"bet365": {"http": "","https": ""}}',
            accounts=r'{"olimp": {"login": "6265127","password": "qvF3BwrNcRcJtB6","mirror": "olimp.com"},"fonbet": {"login": 5699838,"password": "NTe2904H11","mirror": "fonbet.com"}}'
        )
         
        p = {
            "SUMM": 400,
            "RANDOM_SUMM_PROC": 30,
            "FORK_LIFE_TIME": 3,
            "SERVER_IP_TEST": "149.154.70.53",
            "SERVER_IP": "62.109.10.57",
            "WORK_HOUR": 8, 
            "ROUND_FORK": 5,
            "MAX_FORK": 30,
            "MAX_FAIL": 6,
            "MIN_L": 1,
            "HARD_BET_RIGHT": 1
        }
        for k, v in p.items():
            prop = Properties.create(acc=acc.id, key=k, val=v)
    except Exception as e:
        print(e)        

    for x in Account().select():
        js = x.__dict__.get('__data__')
        print(js.get('user'), js.get('id'), js.get('key'), js.get('accounts'))
    # Account.delete().execute()
