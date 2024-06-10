import networkx as nx

dim = 20
l = [0.1, 0.25, 0.5, 0.75, 0.9]
w = 1

G = nx.grid_2d_graph(dim, dim)
temp = []
# set lengths and widths of the edges:
i = -1
for e in G.edges(data=True):
    # dicts are mutable to this will reflect in the graph object too:
    i = (i + 1) % len(l)
    temp.append(l[i])
    e[2]['length'] = l[i]
    e[2]['width'] = w

# change all node names to strings:
map = {}
for n in G.nodes:
    map[n] = str(n)
G = nx.relabel_nodes(G, map)

