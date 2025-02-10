'''
This file contains the functions to import certain network topologies from saved data files on the disk as well as functions and hard-coded dictionaries that specify network topologies.
'''
from src import globals
import networkx as nx
import os 

data_directory_path = f'{os.path.dirname(os.path.realpath(__file__))}/../networks-data'
default_length = globals.args.length
default_width = globals.args.width

# TODO: https://networkx.org/documentation/stable/reference/generators.html has a lot of possible topologies. might be nice to add some of them.

def _from_file():
    file = globals.args.network_file
    if file is None or file == '':
        raise ValueError("No network file selected. Need to specify the file to use if --network=file is used.")

    G = nx.read_gml(file)
    
    return G

def _grid_2d(dim: int = globals.args.grid_dim):
    l: int = default_length
    w: int = default_width if default_width > 0 else 1
    
    G = nx.grid_2d_graph(dim, dim)

    # nx.grid_2d_graph creates node labels as tuples which causes type issues later on. so convert the label (tuple) into a string:
    map = {}
    for n in G.nodes:
        map[n] = str(n)
    G = nx.relabel_nodes(G, map)

    # set lengths and widths of the edges:
    edges = G.edges(data=True)
    for u, v, data in edges:
        # dicts are mutable to this will reflect in the graph object too:
        data['length'] = l
        data['width'] = w

    return G

def _teaver_graph_common(data_directory=data_directory_path):
    # "topology.txt A list of rows containing edges with a source, destination, capacity, and probability of failure."
    
    nodes_file = data_directory + "/nodes.txt"
    topology_file = data_directory + "/topology.txt"
    with open(nodes_file) as file:
        nodes_data = [line.rstrip() for line in file]

    with open(topology_file) as file:
        edges_data = [line.rstrip() for line in file]
    edges_data = [line.split() for line in edges_data]
    edges_data = [x for x in edges_data if x != []]
    
    # both ATT and IBM topologies seem to be digraphs but edges from both directions seem to be the identical for every pair of nodes.
    # so for that reason and also because we assume that the graphs are undirected, we dont make it into a digraph
    G = nx.Graph() 

    for node in nodes_data[1:]:
        G.add_node(node)
    
    w = default_width if default_width > 0 else 1

    for edge in edges_data[1:]:
        to_node = 's' + edge[0]
        from_node = 's' + edge[1]
        G.add_edge(from_node, to_node, capacity=edge[2], prob_failure=edge[3], length=default_length, width=w) # added length and width for each edge. others are from the data file
    
    return G

def _att():
    att = _teaver_graph_common(f'{data_directory_path}/ATT/')
    return att

def _ibm():
    ibm = _teaver_graph_common(f'{data_directory_path}/IBM/')
    return ibm

def _abilene(): # make_undirected is true by default. if this is true then the this directed graph is converted to an undirected graph. Directed graphs will definitely cause issues without significant changes):
    ### Abilene
    from src.utils import latitude_longitude_distance

    with open(f'{data_directory_path}/Abilene/topo-2003-04-10.txt') as file:
            data = [line.rstrip() for line in file]
    data = [line.split('\t') for line in data]
    nodes_data = data[2:14]
    edges_data = data[18:]

    # seems like this graph is supposed to be a directed graph.
    # but we assume that graphs are not directed graphs to make it an undirected graph
    abilene = nx.Graph() 

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
            length = default_length # sometimes src and dst are at the same lat/long. in those cases still use default length (TODO: does it make sense to have length 0? if so leave as 0)
            # default length is 1. So for lat-lon distance, it would be 1km which seems fair for 2 nodes in the same city
        length = round(length, 2) # round to 2 decimal places because otherwise there are a lot of decimal places
        w = default_width if default_width > 0 else 1
        abilene.add_edge(src_node, dst_node, capacity=capacity_kbps, ospf_weight=ospf_weight, length=length, width=w) # added length and width for each edge. others are from the data file

    return abilene

def _surfnet(): # make_undirected is true by default. if this is true then this multigraph is converted to an undirected graph. Directed graphs will definitely cause issues without significant changes):):
    ### SURFnet
    from src.utils import latitude_longitude_distance

    # both gml and graphml are working but graphml seems to provide a slightly easier to read graph (e.g. it has both labels and ids for nodes but in gml only labels are used as ids, etc)
    # surfnet = nx.read_gml(f'{data_directory_path}/SURFnet/Surfnet.gml')
    surfnet = nx.read_graphml(f'{data_directory_path}/SURFnet/Surfnet.graphml')

    # calculate and add lengths of edges based on the latitudes and the longitudes of the nodes
    for e in surfnet.edges(data=True):
        u = e[0]
        v = e[1]
        u_lat = surfnet.nodes[u]['Latitude']
        u_lon = surfnet.nodes[u]['Longitude']
        v_lat = surfnet.nodes[v]['Latitude']
        v_lon = surfnet.nodes[v]['Longitude']
        length = latitude_longitude_distance(u_lat, v_lat, u_lon, v_lon) # calculating length of edge using the nodes' latitute and longitude
        if length == 0:
            length = default_length # sometimes src and dst are at the same lat/long. in those cases still use default length (TODO: does it make sense to have length 0? if so leave as 0)
            # default length is 1. So for lat-lon distance, it would be 1km which seems fair for 2 nodes in the same city
        length = round(length, 2) # round to 2 decimal places because otherwise there are a lot of decimal places
        e[2]['length'] = length # dicts are mutable to this will reflect in the graph object too
        w = default_width if default_width > 0 else 1
        e[2]['width'] = w

    # we assume that graphs are not directed graphs so make it an undirected graph
    surfnet_undirected_graph = nx.Graph(surfnet)
    return surfnet_undirected_graph

def _erdos_renyi_50_01():
    ### Erdos Renyi G(50, 0.1)
    ### Erdős–Rényi model

    g = nx.erdos_renyi_graph(50, 0.1, seed=globals.args.er_seed)

    return g

def _erdos_renyi_50_005():
    ### Erdos Renyi G(50, 0.05)
    ### ### Erdős–Rényi model

    g = nx.erdos_renyi_graph(50, 0.05, seed=globals.args.er_seed)

    return g

def standardize_graph(graph: nx.Graph):
    '''
    This function is supposed to convert the different network topologies into a standard kind of /a graph/s to be used later. 
    This function will return an undirected graph with 'width' and 'length' properties for edges and any other property that may already exist for the edge are removed. 
    If there is no property for 'width' and/or 'length'. The default value is set.
    For nodes, all properties, except 'qubit_capacity', are deleted. It also relabels nodes if a property 'ID' exists already then that is used for this, otherwise 'name' is used. If neighther are there then it doesnt relabel it. Note that labels are unique and can be used as IDs
    '''
    
    nodes = graph.nodes(data=True)
    edges = graph.edges(data=True)
    # any changes to the objects above should reflect in the original graph object
    
    # update nodes:
    label_mapping = {}
    for n, data in nodes:
        if 'ID' in nodes[n].keys():
            label_mapping[n] = data['ID']
        elif 'name' in nodes[n].keys():
            label_mapping[n] = data['name']
        else:
            label_mapping[n] = n
        
        for k in list(nodes[n].keys()):
            if k == 'qubit_capacity': # dont remove this because we use this if specified in the topology
                continue
            del data[k]
        
        if 'qubit_capacity' not in list(nodes[n].keys()):
            data['qubit_capacity'] = globals.args.qubit_capacity
    nx.relabel_nodes(graph, label_mapping, copy=False)

    # update edges:
    for u, v, data in edges:
        for k in list(data.keys()):
            if k in ['length', 'width']:
                continue
            del data[k]

        # set lengths and widths of the edges, if they dont exist:
        if 'length' not in data.keys():
            data['length'] = default_length
        if 'width' not in data.keys():
            w: int = default_width if default_width > 0 else 1
            data['width'] = w

def apply_scale_factor(graph: nx.Graph, scale_factor: float):
    if scale_factor == 1:
        return
    
    edges = graph.edges(data=True)
    for u, v, data in edges:
        data['length'] *= scale_factor

def network_choice():
    network_choice = globals.args.network
    top = globals.NET_TOPOLOGY
    nx_graph = None
    
    if network_choice is top.FILE:
        nx_graph = _from_file()
    elif network_choice is top.GRID_2D:
        nx_graph = _grid_2d()
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
        nx_graph = _erdos_renyi_50_005()
    elif network_choice is top.PA_50_2:
        # it is unclear what 'preferential attachment model' abd 'power graphs' in the quantim overlay paper means. Quantum Overlay people might have used 'nx.barabasi_albert_graph'. At least its somewhere in their code but commented out
        # look at https://networkx.org/documentation/stable/reference/generators.html
        # the link has a few graphs generated from some kind of preferential attachment models
        raise NotImplementedError("The graph 'PA(50, 2)' not implemented yet") # TODO
    elif network_choice is top.PA_50_3:
        raise NotImplementedError("The graph 'PA(50, 3)' not implemented yet") # TODO
    else:
        raise NotImplementedError("Not implemented")
    
    assert (graph_type := type(nx_graph)) is nx.Graph, f"We assume the network topology will be an undirected graph without self loops. The graph generated from the topology is of type '{graph_type}'."
    assert (num_self_loops := nx.number_of_selfloops(nx_graph)) == 0, f"We assume the network topology will be an undirected graph without self loops. The graph generated from the topology has {num_self_loops} self-loops."

    apply_scale_factor(nx_graph, globals.args.scale_length)
    standardize_graph(nx_graph)
    return nx_graph