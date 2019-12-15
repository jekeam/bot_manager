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
    prnt('Fonbet: min: {}, cur: {}, max: {}'.format(check_noise_down[-1][1][0], kof_cur1, check_noise_up[-1][1][0]))
    if check_noise_down[-1][1][0] > kof_cur1 or kof_cur1 > check_noise_up[-1][1][0]:
        k1_is_noise = kof_cur1

    plt.plot(x_save, regr.predict(x_save) + get_std(y), color='blue', linestyle='dotted', markersize=1)
    plt.plot(x_save, regr.predict(x_save), color='black', linestyle='dashed', markersize=1)
    plt.plot(x_save, regr.predict(x_save) - get_std(y), color='blue', linestyle='dotted', markersize=1)

    check_noise_up2 = list(zip(y2_for_check_noise, regr2.predict(x2_for_check_noise) + get_std(y2)))
    check_noise_down2 = list(zip(y2_for_check_noise, regr2.predict(x2_for_check_noise) - get_std(y2)))

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
    prnt('Olimp: min: {}, cur: {}, max: {}'.format(check_noise_down2[-1][1][0], kof_cur2, check_noise_up2[-1][1][0]))
    if check_noise_down2[-1][1][0] > kof_cur2 or kof_cur2 > check_noise_up2[-1][1][0]:
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
    prnt('Fonbet: {}, {}->{}. {}. Noise: {}. Last_noise: {}'.format(vect_fb, kof_predict11, kof_predict21, kof_cur1, noise1, k1_is_noise))

    if kof_predict22 > kof_predict12:
        vect_ol = 'UP'
    elif kof_predict22 == kof_predict12:
        vect_ol = 'STAT'
    else:
        vect_ol = 'DOWN'
    prnt('Olimp: {}, {}->{}. {}. Noise: {}. Last_noise: {}'.format(vect_ol, kof_predict12, kof_predict22, kof_cur2, noise2, k2_is_noise))
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
    x = [5, 106, 29, 27, 121, 114, 37, 17, 67, 30, 29, 122, 29, 89, 31, 28, 122, 120, 121, 20, 39, 90, 29, 29, 91, 29, 90, 29, 89, 119, 93, 121,
         58, 91, 795, 379, 59, 88, 29, 15, 43, 58, 59, 59, 59, 29, 58, 29, 29, 29, 29, 59, 29, 59, 29, 29, 28, 29, 29, 59, 29, 28, 59, 29, 59, 28, 59, 45]
    y = [2.3, 2.15, 2.17, 2.18, 2.2, 2.25, 0, 2.25, 2.05, 2.07, 2.08, 2.1, 2.12, 2.15, 2.17, 2.18, 2.2, 2.25, 2.3, 2.35, 2.03, 2.05, 2.07, 2.08, 2.1, 2.12, 2.15, 2.17, 2.2, 2.25, 2.3, 2.35, 2.4, 2.45, 2.5, 2.7, 2.75,
         2.8, 2.85, 2.9, 3.15, 3.2, 3.25, 3.3, 3.35, 3.4, 3.45, 3.5, 3.55, 3.6, 3.65, 3.7, 3.75, 3.8, 3.85, 3.9, 3.95, 4.0, 4.05, 4.1, 4.15, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8]

    x2 = [16, 15, 23, 7, 15, 87, 30, 15, 134, 20, 15, 7, 7, 103, 43, 35, 43, 19, 54, 14, 31, 51, 47, 19, 15, 19, 43, 36, 17, 53, 16, 7, 35, 19
        , 31, 39, 40, 2, 19, 11, 19, 77, 7, 12, 17, 39, 111, 11, 87, 35, 15, 27, 18, 65, 59, 11, 95, 27, 78, 61, 71, 63, 35, 108, 56, 4
        , 63, 163, 31, 102, 15, 151, 91, 434, 59, 35, 19, 15, 84, 51, 47, 19, 59, 107, 57, 9, 70, 23, 15, 31, 15, 15, 27, 77, 120, 107,
          11, 15, 23, 15, 51, 27, 15, 51, 52]

    y2 = [1.65, 1.7, 1.6, 0, 1.6, 1.65, 1.7, 1.75, 1.7, 1.65, 1.6, 1.55, 1.6, 0, 1.6, 1.65,
          1.6, 1.7, 1.6, 1.7, 1.65, 1.75, 1.7, 1.75, 1.8, 1.75, 1.8, 1.7, 1.65, 1.6, 1.65, 1.6, 1.65, 1.7, 1.65, 1.6, 1.55, 1.6, 1.55, 1.5, 1.6,
          1.55, 1.6, 1.55, 1.45, 1.47, 0, 1.5, 1.55, 1.6, 1.55, 0, 1.55, 1.6, 1.55, 1.6, 1.55, 1.5, 1.55, 1.5, 1.47, 1.5, 1.47, 1.5, 1.47, 1.45, 1.42,
          1.4, 1.42, 1.4, 1.45, 1.47, 1.42, 1.4, 1.35, 1.42, 1.4, 1.42, 1.4, 1.35, 1.3, 1.35, 1.33, 1.3, 1.27, 1.3,
          1.27, 1.25, 1.22, 1.25, 1.27, 1.25, 1.27, 1.25, 1.22, 1.2, 1.17, 1.15, 1.17, 1.2, 1.22, 1.2, 1.22, 1.27, 1.3]

    vect1, vect2 = 'UP', 'DOWN'

    ACC_ID = 0
    ml_ok = False
    real_vect2, real_vect1, noise2, noise1, k2_is_noise, k1_is_noise, plt = get_vect(x, y, x2, y2)

    from better import save_plt

    filename = 'test'.replace('.', '')
    # ML #1 - CHECK VECTS
    if check_vect(real_vect1, real_vect2) and check_noise(noise1, noise2) and sum(x) >= 2 <= sum(x2):
        ml_ok = True
        prnt('Fork key: ' + str(filename) + ', успешно прошел проверку 1 (векторы строго сонаправлены и нет шума)')
        if vect1 != real_vect1:
            prnt('Вектор в Олимп измнен: {}->{}'.format(vect1, real_vect1))
            # shared['olimp']['vect'] = real_vect1
        if vect2 != real_vect2:
            prnt('Вектор в Фонбет измнен: {}->{}'.format(vect2, real_vect2))
            # shared['fonbet']['vect'] = real_vect2
        save_plt(str(ACC_ID) + '_I_ok', filename, plt)
    else:
        prnt('Fork key: ' + str(filename) + ', не прошел проверку 1 (векторы строго сонаправлены и нет шума)')
        save_plt(str(ACC_ID) + '_I_err', filename, plt)

    # ML #2 CHECK CREATER-NOISE
    if not ml_ok:
        side_created = get_creater(k1_is_noise, k2_is_noise)
        if side_created == 1:
            fake_vect1 = 'DOWN'
            fake_vect2 = 'UP'
        elif side_created == 2:
            fake_vect2 = 'DOWN'
            fake_vect1 = 'UP'
        else:
            prnt('Fork key: ' + str(filename) + ', не прошел проверку 2 (Шумный создатель вилки)')
            save_plt(str(ACC_ID) + '_II_err', filename, plt)

        if side_created:
            ml_ok = True
            prnt('Fork key: ' + str(filename) + ', успешно прошел проверку 2 (Шумный создатель вилки)')
            if vect1 != fake_vect1:
                prnt('Вектор в Олимп измнен: {}->{}'.format(vect1, fake_vect1))
                # shared['olimp']['vect'] = fake_vect1
            print(vect2, fake_vect2)
            if vect2 != fake_vect2:
                prnt('Вектор в Фонбет измнен: {}->{}'.format(vect2, fake_vect2))
                # shared['fonbet']['vect'] = fake_vect2
            save_plt(str(ACC_ID) + '_II_ok', filename, plt)
