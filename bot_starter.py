# coding:utf-8
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from db_model import Account

from multiprocessing import Process
import subprocess
import os
import time


def starter():
    def start(key: str):  # abs_path:str
        # os.chdir(abs_path)
        if os.path.isfile('better.py'):
            call_str = 'python3.6 better.py --key ' + key
            print('dir: ' + str(os.getcwd()) + ', command: ' + call_str)
            subprocess.call(call_str, shell=True)
        else:
            print('file better.py not found in ' + str(os.getcwd()))

    if __name__ == '__main__':
        Account.update(pid=0).where(Account.pid > 0).execute()
        while True:
            for acc in Account.select().where((Account.status == 'active') & (Account.work_stat == 'start') & (Account.pid == 0)):
                print(''.ljust(120, '*'))
                print('start: ', acc.key)  # acc.work_dir,
                acc_start = Process(target=start, args=(acc.key,))  # acc.work_dir,
                acc_start.start()
            time.sleep(3)


if __name__ == '__main__':
    starter()
