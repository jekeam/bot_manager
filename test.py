cur_val_bet = 3.75
old_val_bet = 6.7

bet1 = 250

x = round(bet1*old_val_bet/cur_val_bet/5)*5
print(x)

# print('l: ' + str(proc))
# print('l new: ' + str(proc2))

# print(sum_bet_all*proc)
# print(sum_bet_all*proc2)

# new_l = (k_opp * cur_val_bet) / (k_opp + cur_val_bet)
# old_l = (k_opp * old_val_bet) / (k_opp + old_val_bet)


# print('new_l: ' + str(new_l))
# print('old_l: ' + str(old_l))

# l = (1/cur_val_bet)+(1/k_opp)

# round_rang = 5
# #sum_bet = round(((sum_bet_all / new_l) / (cur_val_bet / new_l)) / round_rang) * round_rang
# sum_bet = round((cur_val_bet / l) / (cur_val_bet*(1 / l)) / round_rang) * round_rang
# print(sum_bet)

# #ROUND((K2/NEW%)/(K2*(1/NEW%));-1))
# #K2 - новый коф
# #Bet - сколько планировали ставить
# #NEW% - новый процент вилки
