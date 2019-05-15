# encoding:utf-8
import numpy as np
from sklearn import linear_model
import matplotlib.pyplot as plt
import json
from utils import prnt
import os

noise = 2
access_vect = {'UP': 'DOWN', 'DOWN': 'UP'}


def reject_outliers(data):
    data = np.asarray(data)
    prnt('mean: {}, std: {}, std*noise: {}'.format(np.mean(data), np.std(data), noise * np.std(data)))
    return data[abs(data - np.mean(data)) <= noise * np.std(data)].tolist()


def get_std(data):
    data = np.asarray(data)
    return np.std(data).tolist() * noise


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


def get_vect(x, y, x2, y2):
    y = y[-len(x):]
    y2 = y2[-len(x2):]

    kof_cur1 = y[-1]
    kof_cur2 = y2[-1]

    arr = list(zip(x, y))
    x = []
    y = []
    n = 1
    for p in arr:
        for t in range(1, p[0]):
            x.append(n)
            y.append(p[1])
            n += 1

    arr2 = list(zip(x2, y2))
    x2 = []
    y2 = []
    n2 = 1
    for p2 in arr2:
        for t2 in range(1, p2[0]):
            x2.append(n2)
            y2.append(p2[1])
            n2 += 1

    regr = linear_model.LinearRegression()
    regr2 = linear_model.LinearRegression()

    if x > x2:
        x2 = x[-len(x2):]
        n3 = min(x2)
    else:
        x = x2[-len(x):]
        n3 = min(x)

    x_max = max(x)
    x2_max = max(x2)

    p = list(zip(reversed(y), reversed(y2)))

    x_predict1 = x[-1] + x_max
    x_predict2 = x2[-1] + x2_max

    for k in reversed(p):
        k1, k2 = k[0], k[1]
        if k1 and k2:
            l = 1 / k1 + 1 / k2
            if l < 1:
                proc = (1 - l) * 100
                if proc > 0:
                    if proc >= 3:
                        color = 'pink'
                    elif proc >= 2:
                        color = 'red'
                    elif proc >= 1:
                        color = 'yellow'
                    elif proc >= 0.5:
                        color = 'orange'
                    elif proc < 0.5:
                        color = 'black'
                    plt.plot([n3, n3], [min(k1, k2) + 0.05, max(k1, k2) - 0.05], color=color, markersize=1)
                    # live += 1
        n3 += 1
    plt.scatter(x, y, color='blue', marker=',')
    plt.scatter(x2, y2, color='red', marker=',')
    x_save, y_save = np.asarray(x).reshape(len(x), 1), np.asarray(y).reshape(len(y), 1)
    x2_save, y2_save = np.asarray(x2).reshape(len(x2), 1), np.asarray(y2).reshape(len(y2), 1)

    # x = x[-len(x2):]
    # y = y[-len(x2):]
    y, x = del_zerro(y, x)
    y_for_check_noise = np.asarray(y).reshape(len(y), 1)
    x_for_check_noise = np.asarray(x).reshape(len(x), 1)
    # plt.scatter(x, y, color='blue', marker=',')
    y, x = del_noise(y, x)
    px, py = x[0], y[0]
    px2, py2 = x[-1], y[-1]
    x = np.asarray(x).reshape(len(x), 1)
    y = np.asarray(y).reshape(len(y), 1)
    regr.fit(x, y)

    # x2 = x2[-len(x):]
    # y2 = y2[-len(x):]
    y2, x2 = del_zerro(y2, x2)
    # plt.scatter(x2, y2, color='red', marker=',')
    y2_for_check_noise = np.asarray(y2).reshape(len(y2), 1)
    x2_for_check_noise = np.asarray(x2).reshape(len(x2), 1)
    y2, x2 = del_noise(y2, x2)
    ppx, ppy = x2[0], y2[0]
    ppx2, ppy2 = x2[-1], y2[-1]
    y2 = np.asarray(y2).reshape(len(y2), 1)
    x2 = np.asarray(x2).reshape(len(x2), 1)
    regr2.fit(x2, y2)

    check_noise_up = zip(y_for_check_noise, regr.predict(x_for_check_noise) + get_std(y))
    check_noise_down = zip(y_for_check_noise, regr.predict(x_for_check_noise) - get_std(y))
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
    if list(check_noise_down)[-1][1][0] > kof_cur1 > list(check_noise_up)[-1][1][0]:
        k1_is_noise = kof_cur1

    plt.plot(x_save, regr.predict(x_save) + get_std(y), color='blue', linestyle='dotted', markersize=1)
    plt.plot(x_save, regr.predict(x_save), color='black', linestyle='dashed', markersize=1)
    plt.plot(x_save, regr.predict(x_save) - get_std(y), color='blue', linestyle='dotted', markersize=1)

    check_noise_up2 = zip(y2_for_check_noise, regr2.predict(x2_for_check_noise) + get_std(y2))
    check_noise_down2 = zip(y2_for_check_noise, regr2.predict(x2_for_check_noise) - get_std(y2))

    noise2 = 0
    for n2 in check_noise_up2:
        if n2[0].tolist()[0] > n2[1].tolist()[0]:
            noise2 = n2[0].tolist()[0]
            break
    if not noise2:
        for n2 in check_noise_down2:
            if n2[0].tolist()[0] < n2[1].tolist()[0]:
                noise2 = n2[0].tolist()[0]
                break
    # chech last kof is noise
    k2_is_noise = 0
    if list(check_noise_down2)[-1][1][0] > kof_cur2 > list(check_noise_up2)[-1][1][0]:
        k2_is_noise = kof_cur2
        
    plt.plot(x2_save, regr2.predict(x2_save) + get_std(y2), color='red', linestyle='dotted', markersize=1)
    plt.plot(x2_save, regr2.predict(x2_save), color='black', linestyle='dashed', markersize=1)
    plt.plot(x2_save, regr2.predict(x2_save) - get_std(y2), color='red', linestyle='dotted', markersize=1)

    kof_predict11 = round(float(regr.predict([[x_max]])[0]), 2)
    kof_predict21 = round(float(regr.predict([[x_predict1]])[0]), 2)

    kof_predict12 = round(float(regr2.predict([[x2_max]])[0]), 2)
    kof_predict22 = round(float(regr2.predict([[x_predict2]])[0]), 2)

    if kof_predict21 > kof_predict11:
        vect_fb = 'UP'
    elif kof_predict21 == kof_predict11:
        vect_fb = 'STAT'
    else:
        vect_fb = 'DOWN'
    prnt('Fonbet: {}, {}->{}. {}. Noise: {}'.format(vect_fb, kof_predict11, kof_predict21, kof_cur1, noise1))

    if kof_predict22 > kof_predict12:
        vect_ol = 'UP'
    elif kof_predict22 == kof_predict12:
        vect_ol = 'STAT'
    else:
        vect_ol = 'DOWN'
    prnt('Olimp: {}, {}->{}. {}. Noise: {}'.format(vect_ol, kof_predict12, kof_predict22, kof_cur2, noise2))
    return vect_fb, vect_ol, noise1, noise2, k1_is_noise, k2_is_noise, plt


# 01 - vects up-down/down/up, noises=0
def check_vect(vect1, vect2):
    global access_vect
    if access_vect.get(vect1) == vect2 and access_vect.get(vect2) == vect1:
        return True
    else:
        return False


def check_noise(noise1, noise2):
    if noise1 == noise2 == 0:
        return True
    else:
        return False
        
def get_creater(k1_is_noise, k2_is_noise):
    if k1_is_noise == 0 and k2_is_noise > 0:
        return 2
    elif k2_is_noise == 0 and k1_is_noise > 0:
        return 1
    else:
        return 0


def checks(x, y, x2, y2):
    vect1, vect2, noise1, noise2 = get_vect(x, y, x2, y2)
    if check_vect(vect1, vect2) and check_noise(noise1, noise2):
        return True
    else:
        return False


def str_to_list_float(s: str) -> list:
    return list(map(float, s.replace('[', '').replace(']', '').replace(' ', '').split(',')))


def str_to_list_int(s: str) -> list:
    return list(map(int, s.replace('[', '').replace(']', '').replace(' ', '').split(',')))


if __name__ == '__main__':
    pass
