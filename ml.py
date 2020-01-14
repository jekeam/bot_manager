import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import time


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
    Функция заменяет все 0, которые держались менее 3% секунд от длительности ряда
    и выбросы которые держались меньше  3% секунд от длительности ряда
    на предыдущее значение
    """
    length_outliers=sum(x)*0.03
    xy=np.array([x, y]).T
    outliers_indexes=np.argwhere(((xy[:, 1]==0) & (xy[:, 0]<length_outliers)) | (xy[:, 0]<length_outliers))
    outliers_indexes=outliers_indexes[(outliers_indexes!=0) & (outliers_indexes!=len(x)-1)]
    
    for i in outliers_indexes:
        #только если нет резкого скачка значений
        left=xy[i-1, 1]+1
        right=xy[i+1, 1]+1
        attitude=left/right
        if (attitude<2) & (attitude>0.5):
            xy[i, 1]=xy[i-1, 1]
    return xy[:, 1]


def splits(series: list):
    """
    Функция для разделения ряда на куски при изменении значений 
    больше чем в два раза
    
    Пример: было значение 2, стало 4 или 1.
    """
    diff=np.array([(series[i]+1)/(series[i-1]+1) for i in range(1, len(series))])
    return np.argwhere((diff>=2) | (diff<=0.5))+1


def plot(t: list, series: list, gradient: list, idx_splits: list, parts_gradient: str): # parts_gradient-ADD
    """
    Для графиков ряда, градиента, нижнего и верхнего интервала,
    и точек разделения ряда
    """
    plt.figure(figsize=(15,8))
    plt.plot(t, series, label='Ряд')
    plt.plot(t, gradient, label='Градиент')
    plt.figtext(.13, .13, parts_gradient) # ADD
    if len(idx_splits)!=0:
        plt.scatter(idx_splits[1:]-1, series[idx_splits[1:]-1], color='red', marker='o', s=50, label='Точки разделения ряда')
    plt.legend()
    return plt
    
def save_plt(folder: str, filename: str, plt):
    if not os.path.exists(folder):
        os.makedirs(folder)
    plt.savefig(os.path.join(folder, filename))

def get_label(gradient:float):
    """Метка самого распространненого движения участка ряда"""
    if gradient > 0:
        label='UP'
    elif gradient < 0:
        label='DOWN'
    else:
        label='STAT'
    return label


def get_quality(x, y, label, gradient):
    """
    Считаем коэффициент качества участка ряда с меткой 
    (какова доля движений в зависимости от метки вверх\вниз относительно всех изменений)   
    """
    x=np.array(x)
    
    if label=='UP':
        #если метка UP, сколько секунд были движения вверх относительно всей длительности участка ряда
        positive=np.where(gradient>0)[0]
        quality = round(sum(x[positive])/sum(x)*100, 2)
    elif label=='DOWN':
        #Если метка DOWN, сколько секунд были движения вниз относительно всей длительности участка ряда
        negative=np.where(gradient<0)[0]
        quality = round(sum(x[negative])/sum(x)*100, 2)
    return quality


def check_last(length, quality, label, gradient):
    """
    По длине участка ряда, качеству и движению впоследних котировок определяем есть ли шум в данном ряде
    """    
    if (length>=300) & ((quality<80) 
        | ((label=='UP') & (gradient[-1]<0)) 
        | ((label=='DOWN') & (gradient[-1]>0))):
        return '_NOISE'
    return ''


def analyze_part(part:list):
    """
    Функция обрабатывает отдельный кусок ряда, возвращает метку, сколько секунд держалась,
    ср.скорость возрастания\убывания функции округленную до 5 знаков, коэфициент качества
    """
    y, x = part
    series_part=np.repeat(*part)
    
    if len(y)==1 and set(y)!=set([0]): 
        return['SHORT', len(series_part), 0, 0]
    elif set(y)==set([0]):
        return['ZEROS', len(series_part), 0, 0]
    else:
        gradient=np.gradient(y)
        label=get_label(sum(gradient))
        length=len(series_part)
        
        #считаем ср.скорость возрастания\убывания ряда. если ряд статичен скорость 0
        speed=abs(round(np.mean(gradient[gradient!=0]), 5)) if label!='STAT' else 0
        
        #считаем коэф. качества ряда
        quality=get_quality(x, y, label, gradient) if label!='STAT' else 100
        
        #проверка последних котировок
        label+=check_last(length, quality, label, gradient)
        return [label, length, speed, quality]


def preprocessing(x: list, y: list, is_plot: bool):
    """
    Функция обработки ряда
    """
    #замена коротких нулевых интервалов и выбросов
    y=replace_outliers(x,y)
    #получение индексов по которым нужно дробить ряд
    idx_splits=splits(y).reshape(-1)
    #если число перестало возрастать\убывать
    extremums=[i-1 for i in range(2, len(y)) if (y[i-2]>y[i-1] and y[i-1]<y[i]) or (y[i-2]<y[i-1] and y[i-1]>y[i])]
    #если близко к изменению направления разрыв в ноль не берем эту точку для деления
    extremums=[ex for ex in extremums if np.where((idx_splits<=ex+1) & (ex-1<=idx_splits))[0].size==0]
    #объединяем точки разрывов в ноль и смены направления
    if len(extremums)!=0:
        idx_splits = np.sort(np.unique(np.append(idx_splits, extremums)))
    #Если ряд делится на промежутки:
    if len(idx_splits)!=0:
        #добавляем 0 и последнее значение, чтобы негородить сложные циклы с if
        idx_splits=np.insert(idx_splits, [0, idx_splits.size], [0, len(y)])
        #деление ряда на отрезки из-за сильного скачка значений
        splitted_series=[(y[idx_splits[i-1]:idx_splits[i]], x[idx_splits[i-1]:idx_splits[i]]) for i in range(1, len(idx_splits))]
        parts_gradient=[analyze_part(series_part)  for series_part in splitted_series ]
    else:
        #если ряд не делится
        parts_gradient=analyze_part((y, x))

    #построение графиков
    plt = None
    if is_plot:
        # plt = plot(t, series, gradient, idx_splits, parts_gradient)
        #значения из y размножаем сколько раз, сколько указано в х
        series=np.repeat(y, x)
        t=range(sum(x))
        # считаем градиент функции. Если градиент =0 - статичная функция, если возрастает >0, если убывает < 0 
        gradient=np.gradient(series)
        idx_splits_plot=np.array([sum(x[:i]) for i in idx_splits])
        
        plt = plot(t, series, gradient, idx_splits_plot, parts_gradient) # parts_gradient - ADD
    return parts_gradient, plt