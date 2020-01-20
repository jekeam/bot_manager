import ml
import pandas as pd
import datetime

x_ml = [10,20,30, 5, 11, 3, 2, 2]
y_ml = [1.5, 1.4, 1.1, 0,1.23, 1.23, 1.23, 1.32]
# x_ml = [5, 11, 3, 2, 2]
# y_ml = [0,1.23, 1.23, 1.23, 1.32]

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
if type(data) is str:
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