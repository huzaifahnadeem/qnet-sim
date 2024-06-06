'''
This file contains the functions to import certain network topologies from saved data files on the disk as well as functions and hard-coded dictionaries that specify network topologies.
'''
import globals
import networkx as nx
import os 

data_directory_path = f'{os.path.dirname(os.path.realpath(__file__))}/networks-data'
default_length = globals.args.length
default_width = globals.args.width

# TODO: https://networkx.org/documentation/stable/reference/generators.html has a lot of possible topologies. might be nice to add some of them.

def _from_file():
    raise NotImplementedError("TODO")

    file = globals.args.network_file
    if file is None or file == '':
        raise ValueError("No network file selected. Need to specify the file to use if --network=file is used.")
    


def _grid_2d(dim=globals.args.grid_dim):
    l = default_length
    w = default_width if default_width > 0 else 1
    
    G = nx.grid_2d_graph(dim, dim)

    # set lengths and widths of the edges:
    for e in G.edges(data=True):
        # dicts are mutable to this will reflect in the graph object too:
        e[2]['length'] = l
        e[2]['width'] = w

    # nx.grid_2d_graph creates node labels as tuples which causes type issues later on. so convert the label (tuple) into a string:
    map = {}
    for n in G.nodes:
        map[n] = str(n)
    G = nx.relabel_nodes(G, map)

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
    
    G = nx.DiGraph() # both ATT and IBM topologies seem to be digraphs but edges from both directions seem to be the identical for every pair of nodes.

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
    from utils import latitude_longitude_distance

    with open(f'{data_directory_path}/Abilene/topo-2003-04-10.txt') as file:
            data = [line.rstrip() for line in file]
    data = [line.split('\t') for line in data]
    nodes_data = data[2:14]
    edges_data = data[18:]

    abilene = nx.DiGraph() # seems like this graph is supposed to be a directed graph.

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
        w = default_width if default_width > 0 else 1
        abilene.add_edge(src_node, dst_node, capacity=capacity_kbps, ospf_weight=ospf_weight, length=length, width=w) # added length and width for each edge. others are from the data file

    return abilene

def _surfnet(): # make_undirected is true by default. if this is true then this multigraph is converted to an undirected graph. Directed graphs will definitely cause issues without significant changes):):
    ### SURFnet
    from utils import latitude_longitude_distance

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
            length = 0.1 # sometimes src and dst are at the same lat/long. in those cases still add a small length so its not 0 (TODO: does it make sense to have length 0? if so leave as 0)

        e[2]['length'] = length # dicts are mutable to this will reflect in the graph object too
        w = default_width if default_width > 0 else 1
        e[2]['width'] = w

    return surfnet

def _erdos_renyi_50_01():
    ### Erdos Renyi G(50, 0.1)
    g = nx.erdos_renyi_graph(50, 0.1)

    return g # TODO: check if it is directed or undirected. convert if directed

def _erdos_renyi_50_005():
    ### Erdos Renyi G(50, 0.05)
    g = nx.erdos_renyi_graph(50, 0.05)

    return g # TODO: check if it is directed or undirected. convert if directed

def standardize_graph(graph):
    '''
    This function is supposed to convert the different network topologies into a standard kind of /a graph/s to be used later. 
    This function will return two graphs. 1) a multigraph which is the full graph to run networkx's algorithms on. 2) a simpler multigraph which follows the QPASS paper's network model. This will condense parallel edges of equal length into a single edge of equivalent width. Parallel edges of different lengths remain separate and are not counted as another channel but rather a completely separate connection.
    Note that we are going with a MultiGraph and not a MultiDiGraph. The latter is a directed graph while the former is not.
    '''
    # the full multigraph, and the simplified multigraph:
    graph_f = nx.MultiGraph()
    graph_s = nx.MultiGraph()
    graph_f.add_nodes_from(graph)
    graph_s.add_nodes_from(graph)

    if (type(graph) is nx.Graph) or (type(graph) is nx.DiGraph):
        if type(graph) is nx.DiGraph:
            undir_graph = graph.to_undirected()
            edges = [e for e in undir_graph.edges.data()]
        else:
            edges = [e for e in graph.edges.data()]
        graph_s.add_edges_from(edges)
        for e in edges:
            w = e[2]['width']
            for _ in range(w):
                graph_f.add_edges_from([e])
    elif type(graph) is nx.MultiGraph:  # if it is a multigraph
        edges = sorted(graph.edges(data=True), key=lambda edge: edge[2].get('length', None)) # doing this so that edges (of diff lengths) between the same u-v nodes are grouped together. might be useful to have this later.
        graph_f.add_edges_from(edges)
        added_already = []
        for e in edges:
            if [e[0], e[1], e[2]['length']] not in added_already: # only add as a new edge if there is a new edge between u-v or is of a different length than previous ones.
                graph_s.add_edges_from([e])
                graph_s.edges[e[0]][e[1]]['width'] = 1
                added_already.append([e[0], e[1], e[2]['length']])
            else:
                graph_s.edges[e[0]][e[1]]['width'] += 1

    return graph_s, graph_f

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
        nx_graph = _erdos_renyi_50_005
    elif network_choice is top.PA_50_2:
        raise NotImplementedError("The graph 'PA(50, 2)' not implemented yet") # TODO
    elif network_choice is top.PA_50_3:
        raise NotImplementedError("The graph 'PA(50, 3)' not implemented yet") # TODO
    else:
        raise NotImplementedError("Not implemented")
    
    return standardize_graph(nx_graph)