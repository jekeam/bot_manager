import ml
import pandas as pd
import datetime

x_ml = [10,20,30, 5, 11, 3, 2, 2]
y_ml = [1.5, 1.4, 1.1, 0,1.23, 1.23, 1.23, 1.32]
# x_ml = [5, 11, 3, 2, 2]
# y_ml = [0,1.23, 1.23, 1.23, 1.32]
x_ml = [20, 13, 16, 13, 0, 0, 12, 8, 0, 0, 3, 33, 21, 28, 0, 0, 54, 10, 0, 0, 14, 0, 0, 16, 43, 20, 3, 29, 0, 0, 30, 34, 88, 0, 0, 17, 19, 34, 0, 0, 10, 0, 0, 0, 0, 14, 14, 4, 26, 13, 28, 0, 0, 14, 33, 0, 0, 0, 0, 26, 20, 44, 2]
y_ml = [1.65, 1.55, 1.6, 1.45, 1.5, 1.45, 1.5, 1.45, 1.5, 1.45, 1.5, 1.7, 1.95, 1.6, 1.35, 1.6, 1.35, 1.45, 1.4, 1.45, 1.4, 1.45, 1.4, 1.45, 1.35, 1.3, 0, 1.3, 1.35, 1.3, 1.35, 1.6, 2.65, 3.15, 2.65, 3.15, 3.05, 2.65, 2.5, 2.65, 2.5, 2.15, 2.5, 2.15, 2.5, 2.15, 2.4, 2.15, 2.5, 2.35, 1.95, 1.85, 1.95, 1.85, 2.5, 1.95, 2.5, 1.95, 2.5, 1.95, 1.85, 2.5, 3.35]

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