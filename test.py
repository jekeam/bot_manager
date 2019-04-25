# import json
#
#
# def print_stat(acc_id: str) -> str:
#     cnt_fail = 0
#     black_list_matches = 0
#     cnt_fork_success = 0
#
#     try:
#         with open(acc_id + '_id_forks.txt') as f:
#             for line in f:
#                 js = json.loads(line)
#                 for key, val in js.items():
#                     err_bk1, err_bk2 = val.get('olimp').get('err'), val.get('fonbet').get('err')
#                     bet_skip = False
#
#                     if err_bk1 and err_bk2:
#                         if 'BkOppBetError' in err_bk1 and 'BkOppBetError' in err_bk2:
#                             bet_skip = True
#
#                     if err_bk1 != 'ok' or err_bk2 != 'ok':
#                         if not bet_skip:
#                             cnt_fail += 1
#                             black_list_matches += 1
#
#                     elif not bet_skip:
#                         cnt_fork_success += 1
#
#             return 'Успешных ставок: ' + str(cnt_fork_success) + '\n' + \
#                    'Кол-во ставок с ошибками/выкупом: ' + str(cnt_fail) + '\n'
#
#     except FileNotFoundError:
#         return 'Нет данных'
#     except Exception as e:
#         return 'Возникла ошибка: ' + str(e)
#
#
# print(print_stat('1'))
