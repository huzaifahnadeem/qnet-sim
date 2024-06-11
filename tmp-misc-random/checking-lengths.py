import yaml
import networkx as nx
from numpy import power

nw_file = "/home/hun13/qnet-sim/src/networks-data/grid_2d_19x19_varlen_0.5_1.0.yaml"
tm_file = "/home/hun13/qnet-sim/src/sample_tm_file.yaml"

def length_prob_loss(p_loss_init, p_loss_length, length_km):
    prob_loss = 1 - (1 - p_loss_init) * power(10, - length_km * p_loss_length / 10)

    return prob_loss

G = None
with open(nw_file) as stream:
    nw_data = yaml.safe_load(stream)
    G = nx.from_dict_of_dicts(nw_data)

    with open(tm_file) as stream2:
        tm_data = yaml.safe_load(stream2)
        pair_data = {}
        for ts in tm_data:
            if ts == 1:
                continue # ts 1 is empty
            this_xsep = ts-1 # NOTE: this specific tm file is arranged like this -- hacky
            this_pair = tuple(tm_data[ts][0])
            src, dst = this_pair
            min_dist = nx.shortest_path_length(G, source=src, target=dst, weight='length')
            pair_data[this_pair] = {}
            pair_data[this_pair]['x_sep'] = this_xsep
            pair_data[this_pair]['shortest_path_len'] = min_dist
            # pair_data[this_pair]['avg_shortest_path_len'] = nx.average_shortest_path_length(G, weight='length')

print(f"pair\t\t\t\tx-sep\t\tmin_dist")
for pair in pair_data:
    print(f"{pair}:\t\t{pair_data[pair]['x_sep']}\t\t{pair_data[pair]['shortest_path_len']}")
