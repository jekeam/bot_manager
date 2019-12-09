import pandas as pd
import os
import datetime
from utils import csv_head

def join_csv(cur_date_str):
    li = []
    is_first = True
    for num in range(0, 10000):
        s = './'+ cur_date_str + '_{}' + '_statistics.csv'
        f_name = s.format(num)
        if os.path.isfile(f_name):
            
            df = pd.read_csv(f_name, encoding='utf-8', sep=';', index_col=None)
            df.insert(0, 'ACC_ID', num)
            if is_first:
                is_first = False
                
            li.append(df)
    if li:
        frame = pd.concat(li, axis=0, ignore_index=True)
        frame = frame[csv_head]
        frame_name_f = cur_date_str + '_join_statistics.csv'
        frame.to_csv(frame_name_f, encoding='utf-8', sep=';', index=False)
        return frame_name_f
if __name__=='__main__':
    # cur_date_str = (datetime.datetime.now()-datetime.timedelta(days=1)).strftime("%d_%m_%Y")
    cur_date_str = datetime.datetime.now().strftime("%d_%m_%Y")
    dtt = input('Укажите день выгрузки, по умолчанию, ' + cur_date_str + ': ')
    if dtt:
        cur_date_str = dtt
    join_csv(cur_date_str)