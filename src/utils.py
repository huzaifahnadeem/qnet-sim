import copy
import networkx as nx
import random

def latitude_longitude_distance(lat1, lat2, lon1, lon2):
    # from: https://www.geeksforgeeks.org/program-distance-two-points-earth/
    lat1 = float(lat1)
    lat2 = float(lat2)
    lon1 = float(lon1)
    lon2 = float(lon2)

    from math import radians, cos, sin, asin, sqrt

    # The math module contains a function named
    # radians which converts from degrees to radians.
    lon1 = radians(lon1)
    lon2 = radians(lon2)
    lat1 = radians(lat1)
    lat2 = radians(lat2)
      
    # Haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
 
    c = 2 * asin(sqrt(a)) 
    
    # Radius of earth in kilometers. Use 3956 for miles
    r = 6371
      
    # calculate the result
    return(c * r)

_slmpg_paths_found_already = {}

# This function is here and is not a property of entities (like it was previously) because of the fact that nx.shortest_path() returns any of the shortest paths and when this function was running seperately on each node entity, the results were inconsistent across nodes. So now the first time it is called, it caches the result and uses that later on.
def slmpg_find_paths(links_graph, sd_pairs): # TODO: i think this is quite inefficient.
        # use cached result if it exists
        if tuple(sd_pairs) in _slmpg_paths_found_already.keys():
            return _slmpg_paths_found_already[tuple(sd_pairs)]
        
        G = copy.deepcopy(links_graph)
        paths = []

        def edges_of_path(p):
            edge_path = []
            for i in range(1, len(p)):
                edge_path.append((p[i-1], p[i]))
            return edge_path
        
        for s, d in sd_pairs:
            try:
                p = nx.shortest_path(G, source=s, target=d, weight='length')
                paths.append(list(p))
                G.remove_edges_from(edges_of_path(p))
            except nx.NetworkXNoPath: # no path possible
                pass
            except nx.NodeNotFound: # if src/dst is not able to make link to any node
                pass
        
        _slmpg_paths_found_already[tuple(sd_pairs)] = paths # cache the result
        return paths

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