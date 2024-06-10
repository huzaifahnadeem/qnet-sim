import networkx as nx
import yaml
# import random

# seed = 0
# random.seed(seed)

dim = 19
# l = [0.1, 0.25, 0.5, 0.75, 0.9]
l = [0.5, 1.0]
w = 1

G = nx.grid_2d_graph(dim, dim)
# set lengths and widths of the edges:
i = -1
for e in G.edges(data=True):
    # dicts are mutable to this will reflect in the graph object too:
    i = (i + 1) % len(l)
    e[2]['length'] = l[i]
    e[2]['width'] = w

# change all node names to strings:
map = {}
for n in G.nodes:
    map[n] = str(n)
G = nx.relabel_nodes(G, map)

graph_dict = nx.to_dict_of_dicts(G)
yaml_filename = "/home/hun13/qnet-sim/src/networks-data/grid_2d_19x19_varlen_0.5_1.0.yaml"

with open(yaml_filename, 'w') as outfile:
    yaml.dump(graph_dict, outfile)
