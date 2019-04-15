# coding:utf-8
"""
import subprocess
import os
import time

# os.chdir('D:\\YandexDisk\\Парсинг\\better')
print(__file__+ ' pid ' +str(os.getpid()))
args = ['python3.6', 'broker1.py']
process = subprocess.Popen(args)
time.sleep(0.25)
process.terminate()
print(__file__+ ' end')
"""

"""
import os
import subprocess
import sys

child = os.path.join(os.path.dirname(__file__), "./child.py")
word = 'word'
file = ['./parent.py', './child.py']

pipes = []
for i in range(0, 2):
    command = [sys.executable, child]
    pipe = subprocess.Popen(command, stdin=subprocess.PIPE)
    pipes.append(pipe)
    pipe.stdin.write(word.encode("utf8") + b"\n")
    pipe.stdin.write(file[i].encode("utf8") + b"\n")
    pipe.stdin.close()

while pipes:
    pipe = pipes.pop()
    pipe.wait()
"""