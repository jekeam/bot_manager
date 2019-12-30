import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import time

#функции для обработки данных при считывании
def str_to_list_int(s: str) -> list:
    """
    Конвертация к int
    """
    try:
        return list(map(int, s.strip('[]').split(', ')))
    except Exception as ex:
        print(ex , s)
        return s
        
def str_to_list_float(s: str) -> list:
    """
    Конвертация к float
    """
    try:
        return list(map(float, s.strip('[]').split(', ')))
    except Exception as ex:
        print(ex ,  s)
        return s


def replace_outliers(x: list, y: list):
    """
    Функция заменяет все 0, которые держались менее 30 секунд
    и выбросы которые держались меньше 20 секунд 
    на среднее между значениями, до и после этого нуля
    """
    xy=np.array([x, y]).T
    outliers_indexes=np.argwhere(((xy[:, 1]==0) & (xy[:, 0]<30)) | (xy[:, 0]<20))
    outliers_indexes=outliers_indexes[(outliers_indexes!=0) & (outliers_indexes!=len(x)-1)]
    
    for i in outliers_indexes:
        #только если нет резкого скачка значений
        left=xy[i-1, 1]+1
        right=xy[i+1, 1]+1
        attitude=left/right
        if (attitude<2) & (attitude>0.5):
            xy[i, 1]=np.mean([xy[i-1, 1], xy[i+1, 1]])
        
    return xy[:, 1]

def splits(series: list):
    """
    Функция для разделения ряда на куски при изменении значений 
    больше чем в два раза
    
    Пример: было значение 2, стало 4 или 1.
    """
    diff=np.array([(series[i]+1)/(series[i-1]+1) for i in range(1, len(series))])
    return np.argwhere((diff>=2) | (diff<=0.5))+1


def plot(t: list, series: list, gradient: list, idx_splits: list, parts_gradient: str):
    """
    Для графиков ряда, градиента, нижнего и верхнего интервала,
    и точек разделения ряда
    """
    plt.figure(figsize=(15,8))
    plt.plot(t, series, label='Ряд')
    plt.plot(t, gradient, label='Градиент')
    plt.figtext(.13, .13, parts_gradient)
    plt.scatter(idx_splits[1:]-1, series[idx_splits[1:]-1], color='red', marker='o', s=50, label='Точки разделения ряда из-за скачков значений')
    plt.legend()
    return plt
    
def save_plt(folder: str, filename: str, plt):
    if not os.path.exists(folder):
        os.makedirs(folder)
    plt.savefig(os.path.join(folder, filename))

def get_label(gradient:float):
    if gradient > 0:
        label='UP'
    elif gradient < 0:
        label='DOWN'
    else:
        label='STAT'
    
    return label

def preprocessing(x: list, y: list, is_plot: bool, acc_id: str, fork_id: str):
    """
    Функция для получения из списка длительности и значений - ряда
    """
    #замена коротких нулевых интервалов и выбросов
    y=replace_outliers(x,y)

    #значения из y размножаем сколько раз, сколько указано в х
    series=np.repeat(y, x)
    t=range(sum(x))
    # считаем градиент функции. Если градиент =0 - статичная функция, если возрастает >0, если убывает < 0 
    gradient=np.gradient(series)

    #получение индексов по которым нужно дробить ряд
    idx_splits=splits(series)
    #Если ряд делится на промежутки:
    if len(idx_splits)!=0:
        #добавляем 0 и последнее значение, чтобы негородить сложные циклы с if
        idx_splits=np.insert(idx_splits, [0, idx_splits.size], [0, len(series)])
        #деление ряда на отрезки из-за сильного скачка значений
        splitted_series=[series[idx_splits[i-1]:idx_splits[i]]
                                     for i in range(1, len(idx_splits))]
    
        parts_gradient=[get_label(sum(np.gradient(series_part))) if len(series_part)>1 else 'SHORT' for series_part in splitted_series ]
            
    else:
        #если ряд не делится
        parts_gradient=get_label(sum(np.gradient(series)))

        
    #построение графиков
    if is_plot:
        plt = plot(t, series, gradient, idx_splits, parts_gradient)
        if type(parts_gradient) is str:
            save_plt(acc_id + '/' + parts_gradient.lower(), fork_id, plt)
        else:
            save_plt(acc_id + '/' + 'slices', fork_id, plt)
    return parts_gradient