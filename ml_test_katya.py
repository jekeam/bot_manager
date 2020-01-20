import ml
import pandas as pd
import datetime

x_ml = [10,20,30, 5, 11, 3, 2, 2]
y_ml = [1.5, 1.4, 1.1, 0,1.23, 1.23, 1.23, 1.32]
# x_ml = [5, 11, 3, 2, 2]
# y_ml = [0,1.23, 1.23, 1.23, 1.32]
x_ml = [9, 9, 9, 4, 4, 4, 14, 5, 0, 0, 6, 9, 9, 80, 9, 9, 5, 1, 0, 10, 9, 14, 1, 0, 10, 15, 1, 0, 10, 9, 0, 0, 0, 6, 24, 9, 9, 9, 9, 9, 14, 10, 0, 0, 16, 9, 4, 4, 35, 14, 4, 9, 9, 9, 19, 5, 0, 0, 1, 9, 19, 9, 95, 5, 1, 0, 30, 65, 4, 9, 12, 1, 0, 1, 5, 0, 0, 1, 5, 4, 4, 14, 9, 3, 5, 6]
y_ml = [2.45, 2.68, 3, 3.3, 3.05, 2.9, 2.75, 3.1, 3.35, 3.1, 3.35, 3.2, 3.4, 3.57, 4, 3.57, 4, 3.57, 4, 3.57, 4, 3.5, 4, 3.5, 4, 3.5, 4, 3.5, 4, 4.65, 5.45, 4.8, 5.45, 4.8, 5.6, 4.8, 5.87, 5, 6, 5, 4.1, 3.1, 2.48, 3.1, 2.48, 2.04, 2.17, 2.23, 2.32, 2.55, 2.48, 2.25, 2.48, 2.75, 3.05, 3.35, 3.57, 3.35, 3.57, 3.75, 3.65, 3.4, 3.75, 4, 4.1, 4, 4.1, 4.35, 5, 4.35, 3.65, 4.5, 3.85, 4.5, 3.85, 4.35, 3.85, 4.35, 3.85, 3.35, 3.05, 2.95, 3.2, 2.85, 2.8, 3]

print('x_ml({}): {}'.format(type(x_ml), x_ml))
print('y_ml({}): {}'.format(type(y_ml), y_ml))
data=pd.DataFrame.from_dict({'sec': [x_ml], 'val': [y_ml],})
data=data[(data.val!='') & (data.val!='[]') & (data.sec!='') & (data.sec!='[]')]
#отсеиваю ряды у которых длина значений не равна кол-ву временных интервалов
data=data[data.val.apply(len)==data.sec.apply(len)]
#отсеиваю ряды у которых длина значений и временных интервалов 1, т.к. они статичные
data=data[data.val.apply(len)>1]
data=data.reset_index(drop=True)
parts_gradient, plt = ml.preprocessing(
    data.sec[0],
    data.val[0],
    True
)
print(parts_gradient)
data = parts_gradient
if type(data[0]) is str:
    vect = str(data[0])
else:
    vect = str(data[-1][0])
print(vect)
# print(data)
if vect.lower() != 'up'.lower():
    print('Проверка на ML не пройдена т.к. вектор не UP')
ml.save_plt(
str(0) + '/' + datetime.datetime.now().strftime('%d.%m.%Y') + '/' + str(parts_gradient[0]).lower(), 
str(1), 
plt
)