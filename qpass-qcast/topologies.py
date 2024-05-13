'''
This file contains the functions to import certain network topologies from saved data files on the disk as well as functions and hard-coded dictionaries that specify network topologies.
'''
import globals
import networkx as nx
# TODO: (line 12 fn) make a fn that joins same edges as increased width
data_directory_path = './networks-data'
# data_directory_path = './qpass-qcast/networks-data'
default_length = globals.args.length
default_width = globals.args.width

# TODO: Note that if there are parallel edges (same u-v nodes) then just add 1 to the width for each such edge. although if the lengths (or delay model etc) are different then cant consider that as a width increase its a separate edge

def convert_to_undirected(graph):
    '''
    converts the graph into an undirected graph. For undirected graphs, if a u-v edge exists then v-u edge also added. parallel edges in multi graph are removed and instead a single edge of the average length is added with the right width. TODO: this is not ideal. but to use a multigraph everywhere else would require significant changes.
    '''
    # if type(graph) is nx.Graph:         # if it is an undirected graph
    #     return graph
    # elif type(graph) is nx.DiGraph:     # if it is a directed graph
    #     return graph.to_undirected()
    # elif type(graph) is nx.MultiGraph:  # if it is a multigraph
    #     pass

    return graph.to_undirected()

def _slmp_grid_4x4(length=default_length, width=default_width):
    l = length
    w = width
    return nx.Graph({   
                    'n1': {'n2':{'length':l, 'width':w,}, 'n5':{'length':l, 'width':w,}},
                    'n2': {'n3':{'length':l, 'width':w,}, 'n6':{'length':l, 'width':w,}},
                    'n3': {'n7':{'length':l, 'width':w,}, 'n4':{'length':l, 'width':w,}},
                    'n4': {'n8':{'length':l, 'width':w,}},

                    'n5': {'n6':{'length':l, 'width':w,}, 'n9':{'length':l, 'width':w,}},
                    'n6': {'n7':{'length':l, 'width':w,}, 'n10':{'length':l, 'width':w,}},
                    'n7': {'n8':{'length':l, 'width':w,}, 'n11':{'length':l, 'width':w,}},
                    'n8': {'n12':{'length':l, 'width':w,}},

                    'n9': {'n10':{'length':l, 'width':w,}, 'n13':{'length':l, 'width':w,}},
                    'n10': {'n11':{'length':l, 'width':w,}, 'n14':{'length':l, 'width':w,}},
                    'n11': {'n12':{'length':l, 'width':w,}, 'n15':{'length':l, 'width':w,}},
                    'n12': {'n16':{'length':l, 'width':w,}},

                    'n13': {'n14':{'length':l, 'width':w,}},
                    'n14': {'n15':{'length':l, 'width':w,}},
                    'n15': {'n16':{'length':l, 'width':w,}},
                    'n16': {}, 
                }
        )

def _teaver_graph_common(data_directory=data_directory_path): # make_undirected is true by default. if this is true then the these teaver graphs (which are directed) are converted to undirected graphs. Directed graphs will definitely cause issues without significant changes
    # "topology.txt A list of rows containing edges with a source, destination, capacity, and probability of failure."
    
    nodes_file = data_directory + "/nodes.txt"
    topology_file = data_directory + "/topology.txt"
    with open(nodes_file) as file:
        nodes_data = [line.rstrip() for line in file]

    with open(topology_file) as file:
        edges_data = [line.rstrip() for line in file]
    edges_data = [line.split() for line in edges_data]
    edges_data = [x for x in edges_data if x != []]
    
    G = nx.DiGraph()

    for node in nodes_data[1:]:
        G.add_node(node)
    
    for edge in edges_data[1:]:
        to_node = 's' + edge[0]
        from_node = 's' + edge[1]
        G.add_edge(from_node, to_node, capacity=edge[2], prob_failure=edge[3], length=default_length, width=default_width) # added length and width for each edge. others are from the data file
    
    return convert_to_undirected(G)

def _att():
    att = _teaver_graph_common(f'{data_directory_path}/ATT/')
    return att

def _ibm():
    ibm = _teaver_graph_common(f'{data_directory_path}/IBM/')
    return ibm

def _abilene(): # make_undirected is true by default. if this is true then the this directed graph is converted to an undirected graph. Directed graphs will definitely cause issues without significant changes):
    ### Abilene
    from utils import latitude_longitude_distance

    with open(f'{data_directory_path}/Abilene/topo-2003-04-10.txt') as file:
            data = [line.rstrip() for line in file]
    data = [line.split('\t') for line in data]
    nodes_data = data[2:14]
    edges_data = data[18:]

    abilene = nx.DiGraph()

    # add nodes from nodes_data
    for name, city, latitude, longitude in nodes_data:
        abilene.add_node(name, city=city, latitude=latitude, longitude=longitude)

    # add edges
    for edge in edges_data:
        src_node = edge[0]
        dst_node = edge[1]
        capacity_kbps = edge[2].split()[0]
        ospf_weight = edge[2].split()[1]
        src_lat = abilene.nodes[src_node]['latitude']
        src_lon = abilene.nodes[src_node]['longitude']
        dst_lat = abilene.nodes[dst_node]['latitude']
        dst_lon = abilene.nodes[dst_node]['longitude']
        length = latitude_longitude_distance(src_lat, dst_lat, src_lon, dst_lon) # calculating length of edge using the nodes' latitute and longitude
        if length == 0:
            length = 0.1 # sometimes src and dst are at the same lat/long. in those cases still add a small length so its not 0 (TODO: does it make sense to have length 0? if so leave as 0)
        abilene.add_edge(src_node, dst_node, capacity=capacity_kbps, ospf_weight=ospf_weight, length=length, width=default_width) # added length and width for each edge. others are from the data file

    return convert_to_undirected(abilene) # seems like this graph is supposed to be a directed graph. but converting to undirected versions since that seems more reasonable for our purposes.

def _surfnet(): # make_undirected is true by default. if this is true then this multigraph is converted to an undirected graph. Directed graphs will definitely cause issues without significant changes):):
    ### SURFnet
    # SURFnet = nx.read_gml(f'{data_directory_path}/SURFnet/Surfnet.gml') # this is not working for some reason
    surfnet = nx.read_graphml(f'{data_directory_path}/SURFnet/Surfnet.graphml') # but the data also has this other file type and this works
    
    return convert_to_undirected(surfnet) # TODO: not working properly. check later

def _erdos_renyi_50_01():
    ### Erdos Renyi G(50, 0.1)
    g = nx.erdos_renyi_graph(50, 0.1)

    return g # TODO: check if it is directed or undirected. convert if directed

def _erdos_renyi_50_005():
    ### Erdos Renyi G(50, 0.05)
    g = nx.erdos_renyi_graph(50, 0.05)

    return g # TODO: check if it is directed or undirected. convert if directed

def network_choice():
    network_choice = globals.args.network
    top = globals.NET_TOPOLOGY
    nx_graph = None
    
    if network_choice is top.SLMP_GRID_4x4:
        nx_graph = _slmp_grid_4x4()
    elif network_choice is top.ATT:
        nx_graph = _att()
    elif network_choice is top.IBM:
        nx_graph = _ibm()
    elif network_choice is top.ABILENE:
        nx_graph = _abilene()
    elif network_choice is top.SURFNET:
        nx_graph = _surfnet()
    elif network_choice is top.ER_50_01:
        nx_graph = _erdos_renyi_50_01()
    elif network_choice is top.ER_50_005:
        nx_graph = _erdos_renyi_50_005
    elif network_choice is top.PA_50_2:
        raise NotImplementedError("The graph 'PA(50, 2)' not implemented yet") # TODO
    elif network_choice is top.PA_50_3:
        raise NotImplementedError("The graph 'PA(50, 3)' not implemented yet") # TODO
    else:
        raise NotImplementedError("Not implemented")
    
    return nx_graph