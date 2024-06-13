import json

# dir = "/home/hun13/qnet-sim/src/experiments-results/varying-lengths-0.5-1"
# filename = '5b3b490a-3ec8-4609-8985-080269f27529.json'

# data = {}
# with open(f'{dir}/{filename}', 'r') as jsonfile:
#     data[filename] = json.load(jsonfile)

# paths = data[filename]['results']['path']
# # print(len(paths))
# # print(len(paths[-5:]))
# # print(paths[-5:])

# last5 = paths[-5:]
# # print(last5[0] == last5[1] == last5[2] == last5[3] == last5[4])
# # print(last5[0] == last5[1])
# # print(last5[-2] == last5[-1])

# combos = []
# for i, p1 in enumerate(last5):
#     for j, p2 in enumerate(last5):
#         if i == j:
#             continue
#         combos.append((p1, p2))

# print(len(combos))

# for p1, p2 in combos:
#     if p1 == p2:
#         print(last5.index(p1))
#         print(last5.index(p2))
#         print(p1)
#         print()


from numpy import power
def length_prob_loss(p_loss_init, p_loss_length, length_km):
    prob_loss = 1 - (1 - p_loss_init) * power(10, - length_km * p_loss_length / 10)

    return prob_loss

print(f"prob for len 0.5: {length_prob_loss(p_loss_init=0, p_loss_length=0.25, length_km=0.5)}")
print(f"prob for len 1.0: {length_prob_loss(p_loss_init=0, p_loss_length=0.25, length_km=1.0)}")
print(f"prob for len 1.5: {length_prob_loss(p_loss_init=0, p_loss_length=0.25, length_km=1.5)}")
print(f"prob for len 1.5: {length_prob_loss(p_loss_init=0, p_loss_length=0.25, length_km=1.5)}")