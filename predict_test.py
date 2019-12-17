# encoding:utf-8
import pandas as pd
import numpy as np
from sklearn import linear_model
import matplotlib.pyplot as plt

NOIZE_KOF = 2


def str_to_list_int(s: str) -> list:
    return list(map(int, s.replace('[', '').replace(']', '').replace(' ', '').split(',')))


def reject_outliers(data):
    data = np.asarray(data)
    print('mean: {}, std: {}, std*noise: {}'.format(round(np.mean(data), 2), round(np.std(data), 2), round(NOIZE_KOF * np.std(data), 2)))
    return data[abs(data - np.mean(data)) <= NOIZE_KOF * np.std(data)].tolist()


def get_std(data):
    data = np.asarray(data)
    return np.std(data).tolist() * NOIZE_KOF


def del_noise(val_arr: list, line_arr: list):
    l = val_arr.copy()
    val_white = list(set(reject_outliers(l)))
    if val_white and l:
        slip = 0
        for idx, val in enumerate(l):
            if val not in val_white:
                val_arr.pop(idx - slip)
                line_arr.pop(idx - slip)
                slip += 1

    return val_arr, line_arr


# del zerro values in line
def del_zerro(val_arr: list, line_arr: list):
    l = val_arr.copy()

    if len(val_arr) > len(line_arr):
        val_arr = val_arr[-len(line_arr):]
    elif len(line_arr) > len(val_arr):
        line_arr = line_arr[-len(val_arr):]

    slip = 0
    for idx, val in enumerate(l):
        if val == 0:
            val_arr.pop(idx - slip)
            line_arr.pop(idx - slip)
            slip += 1

    return val_arr, line_arr


def get_vect(x, y):
    y = y[-len(x):]

    kof_cur1 = y[-1]

    arr = list(zip(x, y))
    x = []
    y = []
    n = 1
    for p in arr:
        for t in range(1, p[0]):
            x.append(n)
            y.append(p[1])
            n += 1

    regr = linear_model.LinearRegression()
    x_max = max(x)
    x_predict1 = x[-1] + x_max

    plt.scatter(x, y, color='blue', marker=',')
    x_save, y_save = np.asarray(x).reshape(len(x), 1), np.asarray(y).reshape(len(y), 1)

    y, x = del_zerro(y, x)
    y_for_check_noise = np.asarray(y).reshape(len(y), 1)
    x_for_check_noise = np.asarray(x).reshape(len(x), 1)
    plt.scatter(x, y, color='blue', marker=',')
    y, x = del_noise(y, x)
    # px, py = x[0], y[0]
    x = np.asarray(x).reshape(len(x), 1)
    y = np.asarray(y).reshape(len(y), 1)
    regr.fit(x, y)

    check_noise_up = list(zip(y_for_check_noise, regr.predict(x_for_check_noise) + get_std(y)))
    check_noise_down = list(zip(y_for_check_noise, regr.predict(x_for_check_noise) - get_std(y)))
    noise1 = 0
    for n1 in check_noise_up:
        if n1[0].tolist()[0] > n1[1].tolist()[0]:
            noise1 = n1[0].tolist()[0]
            break
    if not noise1:
        for n1 in check_noise_down:
            if n1[0].tolist()[0] < n1[1].tolist()[0]:
                noise1 = n1[0].tolist()[0]
                break
    # chech last kof is noise
    k1_is_noise = 0
    print('Fonbet: min: {}, cur: {}, max: {}'.format(round(check_noise_down[-1][1][0], 2), kof_cur1, round(check_noise_up[-1][1][0], 2)))
    if check_noise_down[-1][1][0] > kof_cur1 or kof_cur1 > check_noise_up[-1][1][0]:
        k1_is_noise = kof_cur1

    plt.plot(x_save, regr.predict(x_save) + get_std(y), color='blue', linestyle='dotted', markersize=1)
    plt.plot(x_save, regr.predict(x_save), color='black', linestyle='dashed', markersize=1)
    plt.plot(x_save, regr.predict(x_save) - get_std(y), color='blue', linestyle='dotted', markersize=1)

    kof_predict11 = round(float(regr.predict([[x_max]])[0]), 2)
    kof_predict21 = round(float(regr.predict([[x_predict1]])[0]), 2)

    if kof_predict21 > kof_predict11:
        vect_fb = 'UP'
    elif kof_predict21 == kof_predict11:
        vect_fb = 'STAT'
    else:
        vect_fb = 'DOWN'
    print('Vector: {}, start_with:{} sec({}, real_kof:{}) -> end:{} sec({}). Noise: {}. Last_noise: {}'.format(vect_fb, x_max, kof_predict11, kof_cur1, x_predict1, kof_predict21, noise1, k1_is_noise))
    return vect_fb, NOIZE_KOF, k1_is_noise, plt


# 01 - vects up-down/down/up, noises=0
def check_vect(vect1, vect2):
    global access_vect
    if access_vect.get(vect1) == vect2 and access_vect.get(vect2) == vect1:
        return True
    else:
        return False


def check_noise(noise):
    if noise == 0:
        return True
    else:
        return False


def str_to_list_float(s: str) -> list:
    return list(map(float, s.replace('[', '').replace(']', '').replace(' ', '').split(',')))


def str_to_list_int(s: str) -> list:
    return list(map(int, s.replace('[', '').replace(']', '').replace(' ', '').split(',')))


if __name__ == '__main__':
    df = pd.read_csv('./test_filter1.csv', encoding='utf-8', sep=';')
    for i, r in df.iterrows():
        if r['sec'] != '[]':
            print(''.rjust(100, '-'))
            x = str_to_list_int(r['sec'])
            y = str_to_list_float(r['val'])
            try:
                real_vect, NOIZE_KOF, k_is_noise, plt = get_vect(x, y)
                plt.show()
            except Exception as e:
                print(e)
    # x = [102, 58, 88, 89, 31, 2]
    # y = [3.3, 3.35, 3.4, 3.45, 3.5, 5.2]
    # try:
    #     real_vect, NOIZE_KOF, k_is_noise, plt = get_vect(x, y)
    #     plt.show()
    # except Exception as e:
    #     print(e)
