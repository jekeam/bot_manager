from db_model import Message, db
from multiprocessing import Process
from threading import Thread
import time


def read1():
    try:
        while True:
            for acc in Message.select():
                Message.update(text='x').where(Message.id == 135).execute()
                time.sleep(1)
                # print('1: ' + str(acc))
    except Exception as e:
        print('1: ' + str(e))


def read2():
    try:
        while True:
            for acc in Message.select():
                pass
                # print('2: ' + str(acc))
    except Exception as e:
        print('2: ' + str(e))


def read3():
    try:
        while True:
            Message.insert(to_user=1, text='x').execute()
            time.sleep(1)
            # print('1: ' + str(acc))
    except Exception as e:
        print('3: ' + str(e))


def read4():
    try:
        while True:
            for acc in Message.select():
                pass
                # print('2: ' + str(acc))
    except Exception as e:
        print('4: ' + str(e))


if __name__ == '__main__':
    ps1 = Thread(target=read2)
    ps1.start()

    ps2 = Thread(target=read1)
    ps2.start()

    ps3 = Process(target=read3)
    ps3.start()

    ps4 = Thread(target=read4)
    ps4.start()
