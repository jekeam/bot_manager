# coding:utf-8
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from db_model import Account, send_message_bot
import bot_prop

from threading import Thread
import subprocess
import os
import time
from random import uniform


def prntbs(vstr, filename='bot_starter.log'):
    Outfile = open(filename, "a+", encoding='utf-8')
    Outfile.write(vstr + '\n')
    Outfile.close()


if __name__ == '__main__':
    def start(acc_id: str, wait_sec: str=''):  # abs_path:str
        # os.chdir(abs_path)
        if os.path.isfile('better.py'):
            call_str = bot_prop.PY_PATH + ' better.py --acc_id ' + str(acc_id) + ' ' + wait_sec
            prntbs('dir: ' + str(os.getcwd()) + ', command: ' + call_str)
            subprocess.call(call_str, shell=True)
        else:
            prntbs('file better.py not found in ' + str(os.getcwd()))


    if __name__ == '__main__':
        Account.update(pid=0).where(Account.pid > 0).execute()
        while True:
            for acc in Account.select().where((Account.status == 'active') & ((Account.work_stat == 'start_sleep')|(Account.work_stat == 'start')) & (Account.pid == 0)):
                Account.update(pid=1).where(Account.id == acc.id).execute()
                prntbs(''.ljust(120, '*'))
                random_time = uniform(0, 1)
                prntbs('random_time: ' + str(random_time))
                time.sleep(random_time)
                if acc.work_stat == 'start':
                    prntbs('start: ' + str(acc.id))  # acc.work_dir,
                    acc_start = Thread(target=start, args=(acc.id,))  # acc.work_dir,
                else:
                    prntbs('start_sleep: ' + str(acc.id))  # acc.work_dir,
                    acc_start = Thread(target=start, args=(acc.id, 'start_sleep'))  # acc.work_dir,
                acc_start.start()
            time.sleep(5)
