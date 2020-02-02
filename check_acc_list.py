# coding:utf-8
import pandas as pd
import bet_fonbet
import time
from random import choice

with open('fonbet.proxy', 'r') as file:
    proxy_list = file.readlines()

with open('acc_list.csv', 'r+') as file:
    rows = file.readlines()
    for row in rows:
        login, password, domain = row.split(';')
        # prixy = choice(proxy_list).strip()
        res = bet_fonbet.check_acc(int(login), password, domain)
        print('{};{};{};{}'.format(login, password, domain, res.strip()))
