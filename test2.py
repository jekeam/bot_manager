# val = 'asfasdf'
# type_ = 'int'

# if type_ == 'int':
#     type_ = int
# elif type_ == 'float':
#     type_ = float
    
# val = type_(val)

# # def check_limits(val, type_, min_, max_, access_list):
# #     err_str = ''
# #     if max_:
# #             max_ = type_(max_)
# #     if min_:
# #         min_ = type_(min_)
# #     if access_list:
# #         access_list = list(map(type_, access_list))
        
# #     if val < min_ or val > max_:
# #         err_str = 'Нарушены границы пределов, min: {}, max: {}, вы указали: {}'.format(min_, max_, val) + '\n'
        
# #     if access_list:
# #         if val not in access_list:
# #             err_str = err_str + 'Недопустимое значение: {}, резрешено: {}'.format(val, access_list)
        
# #     return err_str

# # def check_type(val:str, type_:str, min_:str, max_:str, access_list):
# #     err_str = ''
    
# #     try:
# #         if type_ == 'int':
# #             type_ = int
# #         elif type_ == 'float':
# #             type_ = float
# #         val = type_(val)
# #     except ValueError as e:
# #         err_str = 'Неверный тип значения, val:{}, type:{}'.format(val, type_)
       
# #     err_limits = check_limits(val, type_, min_, max_, access_list) 
# #     if err_limits:
# #         err_str = err_str + '\n' + err_limits
    
# #     return err_str.strip()

# # prop_abr = {
# #     "SUMM": {"abr": "Общая ставка", "type": "int", "max": "10000", "min": "400", "access_list": [], "error": ""},
# #     "RANDOM_SUMM_PROC": {"abr": "Отклонение от суммы (в %)", "type": "int", "max": "30", "min": "0", "access_list": [], "error": ""},
# #     "FORK_LIFE_TIME": {"abr": "Время вилки от (сек.)", "type": "int", "max": "500", "min": "3", "access_list": [], "error": ""},
# #     # "SERVER_IP_TEST": {"abr": "IP-адрес тест. сервера", "type": "", "max": "", "min": "", "access_list": [], "error": ""},
# #     # "SERVER_IP": {"abr": "IP-адрес бой сервера", "type": "", "max": "", "min": "", "access_list": [], "error": ""},
# #     # "WORK_HOUR": {"abr": "Работаю (ч.)", "type": "", "max": "", "min": "", "access_list": [], "error": ""},
# #     "WORK_HOUR_END": {"abr": "Остановка в (ч.)", "type": "int", "max": "23", "min": "0", "access_list": [], "error": ""},
# #     "ROUND_FORK": {"abr": "Округление вилки/ставки", "type": "int", "max": "100", "min": "5", "access_list": ["5","10","50", "100"], "error": ""},
# #     "MAX_FORK": {"abr": "Max успешных вилок", "type": "int", "max": "50", "min": "1", "access_list": [], "error": ""},
# #     "MAX_FAIL": {"abr": "Max выкупов", "type": "int", "max": "7", "min": "1", "access_list": [], "error": ""},
# #     "MIN_PROC": {"abr": "Min профит вилки", "type": "float", "max": "10", "min": "0.5", "access_list": [], "error": ""},
# #     # "HARD_BET_RIGHT": {"abr": "Жесткая ставка второго плеча", "type": "", "max": "", "min": "", "access_list": [], "error": ""},
# # }

# # for key, val in prop_abr.items():
# #     print(key)
# #     print(check_type(1, val.get('type'), val.get('min'), val.get('max'), val.get('access_list')))