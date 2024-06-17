import networkx as nx
import yaml

# choice = '0.55+half'
# choice = '0.55+twice'
# choice = '0.4+half'
choice = '0.4+twice'


len_55 = 17.34
len_40 = 11.09

dim = 19

if choice == '0.55+half':
    yaml_filename = "/home/hun13/qnet-sim/tmp-misc-random/grid_2d_19x19_varlen_p0.55_with_half.yaml"
    length_factor = len_55
    l = [0.5*length_factor, 1.0*length_factor]

if choice == '0.55+twice':
    yaml_filename = "/home/hun13/qnet-sim/tmp-misc-random/grid_2d_19x19_varlen_p0.55_with_twice.yaml"
    length_factor = len_55
    l = [2*length_factor, 1.0*length_factor]

if choice == '0.4+half':
    yaml_filename = "/home/hun13/qnet-sim/tmp-misc-random/grid_2d_19x19_varlen_p0.4_with_half.yaml"
    length_factor = len_40
    l = [0.5*length_factor, 1.0*length_factor]

if choice == '0.4+twice':
    yaml_filename = "/home/hun13/qnet-sim/tmp-misc-random/grid_2d_19x19_varlen_p0.4_with_twice.yaml"
    length_factor = len_40
    l = [2*length_factor, 1.0*length_factor]


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

with open(yaml_filename, 'w') as outfile:
    yaml.dump(graph_dict, outfile)
