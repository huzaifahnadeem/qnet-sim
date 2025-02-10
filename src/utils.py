import copy
import networkx as nx
import random


def parse_json_config(config, data):
    for var_str in data.keys():
        if f"{var_str[0]}{var_str[1]}" == '--':
            var = var_str[2:]
        else:
            var = var_str
            
        setattr(config, var, data[var_str])

def _grid_dist(u, v, dir_ind):
    u = u[1:-1].split(',')
    v = v[1:-1].split(',')

    return abs(int(u[dir_ind]) - int(v[dir_ind]))

def grid_x_dist(u, v):
    return _grid_dist(u, v, 0) # node name's tuple = (x, y). x = idx 0, y = idx 1

def grid_y_dist(u, v):
    return _grid_dist(u, v, 1) # node name's tuple = (x, y). x = idx 0, y = idx 1

def rand_success(p_of_fail):
    successful = True
    p = p_of_fail
    r = random.randint(1, 100)
    if r <= (p*100):
        successful = False

    return successful

def ceildiv(a, b):
    # https://stackoverflow.com/questions/14822184/is-there-a-ceiling-equivalent-of-operator-in-python
    # math.floor can apparently "quietly produce incorrect results, because it introduces floating-point error" according to the link above so just using this fn where needed
    return -(a // -b)