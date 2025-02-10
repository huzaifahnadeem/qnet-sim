import json 
import networkx as nx

network_graph = {
    'n1':  {'n2':   {'length': 1, 'width': 1}, 'n5':  {'length': 1, 'width': 1}},
    'n2':  {'n1':   {'length': 1, 'width': 1}, 'n3':  {'length': 1, 'width': 1}, 'n6':  {'length': 1, 'width': 1}},
    'n3':  {'n2':   {'length': 1, 'width': 1}, 'n7':  {'length': 1, 'width': 1}, 'n4':  {'length': 1, 'width': 1}},
    'n4':  {'n3':   {'length': 1, 'width': 1}, 'n8':  {'length': 1, 'width': 1}},

    'n5':  {'n1':   {'length': 1, 'width': 1}, 'n6':  {'length': 1, 'width': 1}, 'n9':  {'length': 1, 'width': 1}},
    'n6':  {'n5':   {'length': 1, 'width': 1}, 'n2':  {'length': 1, 'width': 1}, 'n7':  {'length': 1, 'width': 1}, 'n10': {'length': 1, 'width': 1}},
    'n7':  {'n6':   {'length': 1, 'width': 1}, 'n3':  {'length': 1, 'width': 1}, 'n8':  {'length': 1, 'width': 1}, 'n11': {'length': 1, 'width': 1}},
    'n8':  {'n7':   {'length': 1, 'width': 1}, 'n4':  {'length': 1, 'width': 1}, 'n12': {'length': 1, 'width': 1}},

    'n9':  {'n5' :  {'length': 1, 'width': 1}, 'n10': {'length': 1, 'width': 1}, 'n13': {'length': 1, 'width': 1}},
    'n10': {'n9' :  {'length': 1, 'width': 1}, 'n6':  {'length': 1, 'width': 1}, 'n11': {'length': 1, 'width': 1}, 'n14': {'length': 1, 'width': 1}},
    'n11': {'n10' : {'length': 1, 'width': 1}, 'n7':  {'length': 1, 'width': 1}, 'n12': {'length': 1, 'width': 1}, 'n15': {'length': 1, 'width': 1}},
    'n12': {'n11' : {'length': 1, 'width': 1}, 'n8':  {'length': 1, 'width': 1}, 'n16': {'length': 1, 'width': 1}},

    'n13': {'n9' :  {'length': 1, 'width': 1}, 'n14': {'length': 1, 'width': 1}},
    'n14': {'n13' : {'length': 1, 'width': 1}, 'n10': {'length': 1, 'width': 1}, 'n15': {'length': 1, 'width': 1}},
    'n15': {'n14' : {'length': 1, 'width': 1}, 'n11': {'length': 1, 'width': 1}, 'n16': {'length': 1, 'width': 1}},
    'n16': {'n15' : {'length': 1, 'width': 1}, 'n12': {'length': 1, 'width': 1}},
}

G = nx.from_dict_of_dicts(network_graph)
for n in network_graph.keys():
    G.nodes[n]['qubit_capacity'] = 4

# dod = nx.to_dict_of_dicts(G)
# with open("./4x4.json", "w") as fp:
#     json.dump(dod , fp) 

nx.write_gml(G, "./4x4.gml")