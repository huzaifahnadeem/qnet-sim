import yaml

file_64 = '/home/hun13/qnet-sim/tmp-misc-random/64-degree-slmp-rep.yaml'
file_72 = '/home/hun13/qnet-sim/tmp-misc-random/72-degree-slmp-rep.yaml'


def _grid_dist(u, v, dir_ind):
    u = u[1:-1].split(',')
    v = v[1:-1].split(',')

    return abs(int(u[dir_ind]) - int(v[dir_ind]))

def _grid_x_dist(u, v):
    return _grid_dist(u, v, 0) # node name's tuple = (x, y). x = idx 0, y = idx 1

def _grid_y_dist(u, v):
    return _grid_dist(u, v, 1) # node name's tuple = (x, y). x = idx 0, y = idx 1

def grid_x_dist(pair):
    return _grid_x_dist(pair[0], pair[1])

def grid_y_dist(pair):
    return _grid_y_dist(pair[0], pair[1])


def tm_from_file(file_name):
    # sample file: ../tm-files/sample_tm_file.yaml

    num_of_ts = 11
    tm = [[] for _ in range(num_of_ts)]
    with open(file_name) as tm_file:
        tm_data = yaml.safe_load(tm_file)
        for ts in range(1, num_of_ts + 1):
            for sd_pair in tm_data[ts]:
                sd = (sd_pair[0], sd_pair[1])
                tm[ts-1].append(sd)
        
    return tm

def print_seps(degree, file):
    print(f"for {degree} degrees")
    tm = tm_from_file(file_name=file)
    for i, traffic in enumerate(tm):
        ts = i + 1
        print(f"ts = {ts}")
        for pair in traffic:
            print(f"{pair} => x-sep = {grid_x_dist(pair)} ; y-sep = {grid_y_dist(pair)}")
        print()

print_seps('64', file_64)
print(); print(); print()
print_seps('72', file_72)