import random
import utils
import globals

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


def old_init_random_traffic_matrix(network):
    # TODO: might want to look into quantum overlay paper's traffic matrix generation process and use that.
    node_names = [n for n in network.node_names()]
    num_of_ts = globals.args.num_ts
    max_num_sds = globals.args.max_sd
    min_num_sds = globals.args.min_sd
    
    if not globals.args.single_entanglement_flow_mode:
        if globals.args.src_set == []:
            src_set = node_names
        else:
            src_set = globals.args.src_set
        if globals.args.dst_set == []:
            dst_set = node_names
        else:
            dst_set = globals.args.dst_set

    tm = []
    i = -1
    j = -1
    for _ in range(num_of_ts):
        if globals.args.single_entanglement_flow_mode:
            if globals.args.src_set == []:
                src_set = [random.choice(node_names)]
            if globals.args.dst_set == []:
                dst_set = [random.choice(list(set(node_names) - set(src_set)))]

            if (globals.args.src_set != []) and (globals.args.dst_set != []):
                while True:
                    i = (i+1) % len(globals.args.src_set)
                    j = (j+1) % len(globals.args.dst_set)
                    src_set = [globals.args.src_set[i]]
                    dst_set = [globals.args.dst_set[j]]
                    if src_set != dst_set:
                        break
                    else:
                        i -= 1

        this_ts_sds = []
        num_sds = random.randint(min_num_sds, max_num_sds)
        
        sources = random.choices(src_set, k = num_sds)
        for s in sources:
            while True:
                d = random.choice(dst_set)
                if s != d:
                    sd_pair = (s, d)
                    # quantum.new_sd_pair(sd_pair) # returns an index of the state. quantum file will keep track of the actual state in random_states list.
                    this_ts_sds.append(sd_pair)
                    break

        tm.append(this_ts_sds)
    
    return tm