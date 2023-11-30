# p = ['n1', 'n2', 'n3', 'n4']
# r = p[1:-1]

# print(r)

import random

class config:
    probability_ebit_lost_over_channel = 0


def ebit_arrives_across_channel():
    # TODO: test this function && use this function on receiver side.
    arrives = True
    r = random.randint(1, 100)
    if r <= config.probability_ebit_lost_over_channel:
        arrives = False
    return arrives


lost = 0
for _ in range(100):
    if ebit_arrives_across_channel() == False:
        lost += 1

print(lost)