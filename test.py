from utils import get_sum_bets, get_new_sum_bets

k1 = 5.75
k2 = 1.22
total_bet = 400
bal1 = 5241
bal2 = 200


bet1, bet2 = get_sum_bets(k1, k2, total_bet, 5, True)
print(1,bet1, bet2)
if bet1 > bal1 or bet2 > bal2:
    if bal1 < bal2:
        bet1, bet2 = get_new_sum_bets(k1, k2, bal1, True)
        print(2,bet1, bet2)
    else:
        bet2, bet1 = get_new_sum_bets(k2, k1, bal2, True)
        print(3,bet1, bet2)

