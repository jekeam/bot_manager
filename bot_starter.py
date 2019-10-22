# coding:utf-8
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from db_model import Account, send_message_bot
import bot_prop

from threading import Thread
import subprocess
import os
import time

if __name__ == '__main__':
    def start(acc_id: str, wait_sec: str=''):  # abs_path:str
        # os.chdir(abs_path)
        if os.path.isfile('better.py'):
            call_str = bot_prop.PY_PATH + ' better.py --acc_id ' + str(acc_id) + ' ' + wait_sec
            print('dir: ' + str(os.getcwd()) + ', command: ' + call_str)
            subprocess.call(call_str, shell=True)
        else:
            print('file better.py not found in ' + str(os.getcwd()))


    if __name__ == '__main__':
        Account.update(pid=0).where(Account.pid > 0).execute()
        while True:
            for acc in Account.select().where((Account.status == 'active') & (Account.work_stat == 'start_sleep') & (Account.pid == 0)):
                Account.update(pid=1).where(Account.id == acc.id).execute()
                print(''.ljust(120, '*'))
                if acc.work_stat == 'start':
                    print('start: ', acc.id)  # acc.work_dir,
                    acc_start = Thread(target=start, args=(acc.id,))  # acc.work_dir,
                else:
                    print('start_sleep: ', acc.id)  # acc.work_dir,
                    acc_start = Thread(target=start, args=(acc.id, 'start_sleep'))  # acc.work_dir,
                acc_start.start()
            time.sleep(1)
