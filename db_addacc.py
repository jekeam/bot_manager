# coding:utf-8
from db_model import *
from json import loads, dumps

if __name__ == '__main__':
    try:
        acc = Account.create(
            user=381868674,
            key='48447db4-5f9f-11e9-9fcf-2cfda1739afe',
            date_end=get_trunc_sysdate(30000),
            status='active',
            work_status='start',
            properties=r'{ "summ": 560, "random_summ_proc": 30, "fork_life_time": 3, "server_ip_test": "149.154.70.53", "server_ip": "62.109.10.57", "work_hour": 8, "round_fork": 5, "max_fork": 30, "max_fail": 4, "min_l": 1}',
            proxies=r'{ "fonbet": { "http": "http://shaggy:hzsyk4@5.188.84.73:8656", "https": "https://shaggy:hzsyk4@5.188.84.73:8656" }, "olimp": { "http": "http://shaggy:hzsyk4@5.188.84.73:8656", "https": "https://shaggy:hzsyk4@5.188.84.73:8656" } }',
            accounts=r'{ "olimp": { "login": "3318188", "password": "6ya8y4eK", "mirror": "olimp.com" }, "fonbet": { "login": 5989155, "password": "6ya8y4eK", "mirror": "fonbet.com" } }'
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
            properties=r'{"summ": 400,"random_summ_proc": 30,"fork_life_time": 3,"server_ip_test": "149.154.70.53","server_ip": "62.109.10.57","work_hour": 8, "round_fork": 5,"max_fork": 30,"max_fail": 6,"min_l": 1, "hard_bet_right": 1}',
            proxies=r'{"fonbet": {"http": "http://suineg:8veh34@212.90.108.153:3597","https": "https://suineg:8veh34@212.90.108.153:3597"},"olimp": {"http": "http://suineg:8veh34@212.90.108.153:3597","https": "https://suineg:8veh34@212.90.108.153:3597"},"bet365": {"http": "","https": ""}}',
            accounts=r'{"olimp": {"login": "6265127","password": "qvF3BwrNcRcJtB6","mirror": "olimp.com"},"fonbet": {"login": 5699838,"password": "NTe2904H11","mirror": "fonbet.com"}}'
        )
    except Exception as e:
        print(e)

    for x in Account().select():
        js = x.__dict__.get('__data__')
        print(js.get('user'), js.get('id'), js.get('key'), js.get('accounts'))
    # Account.delete().execute()
