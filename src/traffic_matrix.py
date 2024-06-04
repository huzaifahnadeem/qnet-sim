import random
import utils
import globals
import json

def random_traffic_matrix(network):
    def calc_dist_range(dist_is_specified, grid_dim, dist_lte=None, dist_gte=None):
        if not dist_is_specified:
            return range(0, grid_dim)
        else:
            # < 0 implies dont force a specific distance.
            low = dist_gte if dist_gte >= 0 else 0
            high = 1 + dist_lte if dist_lte >= 0 else grid_dim
            return range(low, high)


    node_names = [n for n in network.node_names()]
    num_of_ts = globals.args.num_ts
    max_num_sds = globals.args.max_sd   # per ts
    min_num_sds = globals.args.min_sd   # per ts
    is_single_entanglement_flow_mode = globals.args.single_entanglement_flow_mode
    is_grid_topology = globals.args.network is globals.NET_TOPOLOGY.GRID_2D
    xdist_is_specified = is_grid_topology and ((globals.args.x_dist_gte >= 0) or (globals.args.x_dist_lte >= 0))
    ydist_is_specified = is_grid_topology and ((globals.args.y_dist_gte >= 0) or (globals.args.y_dist_lte >= 0))
    xdist_range = calc_dist_range(xdist_is_specified, globals.args.grid_dim, globals.args.x_dist_lte, globals.args.x_dist_gte)
    ydist_range = calc_dist_range(ydist_is_specified, globals.args.grid_dim, globals.args.y_dist_lte, globals.args.y_dist_gte)
    src_set_is_specified = globals.args.src_set != []
    dst_set_is_specified = globals.args.dst_set != []

    tm = [[] for _ in range(num_of_ts)]

    for this_ts_sds in tm:
        src_set = globals.args.src_set if src_set_is_specified else node_names
        dst_set = globals.args.dst_set if dst_set_is_specified else node_names
        sd_combos = [(x, y) for x in src_set for y in dst_set]
        if not is_grid_topology:
            combo_weights = [1 for _ in sd_combos]
        else:
            combo_weights = [int((utils.grid_x_dist(u, v) in xdist_range) and (utils.grid_y_dist(u, v) in ydist_range)) for u, v in sd_combos] # 1 if in xdist_range and in ydist_range. 0 otherwise
        num_sds_this_ts = random.randint(min_num_sds, max_num_sds)
        
        if is_single_entanglement_flow_mode:
            sd = random.choices(sd_combos, weights=combo_weights, k=1)[0]
            src_i = random.choices([0, 1], k=1)[0] 
            dst_i = 1 if src_i == 0 else 0
            sd = (sd[src_i], sd[dst_i])
            for _ in range(num_sds_this_ts):
                this_ts_sds.append(sd) 
        else:
            k = num_sds_this_ts
            sds = random.choices(sd_combos, weights=combo_weights, k=k)
            for sd_pair in sds:
                src_i = random.choices([0, 1], k=1)[0] # assuming idx 0 as src, idx 1 as dst so doing this for randomization
                dst_i = 1 if src_i == 0 else 0
                sd = (sd_pair[src_i], sd_pair[dst_i])
                this_ts_sds.append(sd)
    return tm

def tm_from_file(file_name):
    # assumptions: in json file, key denotes ts. val is a list of 2-element lists [src, dst]. The val list is processed in order i.e. first s-d pair attempted first then second and so on. If more keys than timeslots then arg --num_ts is the cut off. Keys assumed to start from 1 and in consecutive order.

    num_of_ts = globals.args.num_ts
    tm = [[] for _ in range(num_of_ts)]
    with open(file_name) as tm_file:
        json_data = json.load(tm_file)
        for ts in range(1, num_of_ts + 1):
            for sd_pair in json_data[str(ts)]:
                sd = (sd_pair[0], sd_pair[1])
                tm[ts-1].append(sd)
        
    return tm
