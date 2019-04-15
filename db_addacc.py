#coding:utf-8
from db_model import *

if __name__=='__main__':
    try:
        acc = Account.create(
            user = 381868674,
            key = 'b1e6737e-5f62-11e9-9329-0242ac110011',
            work_dir = '\\broker\\better.py',
            date_end = get_trunc_sysdate(30000),
            properties = '{ "summ": 560, "random_summ_proc": 30, "fork_life_time": 3, "server_ip_test": "149.154.70.53", "server_ip": "62.109.10.57", "work_hour": 8, "account_name": "cl", "round_fork": 5, "max_fork": 35, "max_fail": 5, "min_l": 0.985 }',
            proxies = '{ "fonbet": { "http": "http://shaggy:hzsyk4@5.188.84.73:8656", "https": "https://shaggy:hzsyk4@5.188.84.73:8656" }, "olimp": { "http": "http://shaggy:hzsyk4@5.188.84.73:8656", "https": "https://shaggy:hzsyk4@5.188.84.73:8656" } }',
            accounts = '{ "olimp": { "login": "3318188", "password": "6ya8y4eK", "mirror": "" }, "fonbet": { "login": 5989155, "password": "6ya8y4eK", "mirror": "fonbet.com" } }'
        )
    except Exception as e:
        print(e)
    for x in Account().select().where(Account.id == 1):
        print(type(x))
        print(str(x.user))
    # Account.delete().execute()