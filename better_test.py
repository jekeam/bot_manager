import os
import time
from multiprocessing import Process
import db_model

def work():
    sleep_sel = 30
    print(__file__+ ' proc pid ' +str(os.getpid()))
    print(__file__+' wait ' + str(sleep_sel) + '...')
    time.sleep(sleep_sel)

print(__file__ + ' start') 
print(__file__+' dir ' + os.getcwd())
print(__file__+ ' pid ' +str(os.getpid()))
p = Process(target=work)
p.start()
p.join()
print(__file__+' end')