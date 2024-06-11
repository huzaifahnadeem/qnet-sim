import networkx as nx

data_directory_path = "/home/hun13/qnet-sim/src/networks-data"

default_width = 1

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

def _surfnet(): # make_undirected is true by default. if this is true then this multigraph is converted to an undirected graph. Directed graphs will definitely cause issues without significant changes):):
    ### SURFnet

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

def _abilene(): # make_undirected is true by default. if this is true then the this directed graph is converted to an undirected graph. Directed graphs will definitely cause issues without significant changes):
    ### Abilene

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


# abilene = standardize_graph(_abilene())
# surfnet = standardize_graph(_surfnet())

abilene = _abilene()
surfnet = _surfnet()

abilene_lengths = {}
for edge in abilene.edges():
    this_len = abilene.edges[edge]['length']
    if this_len not in abilene_lengths:
        abilene_lengths[this_len] = None

# surfnet_lengths = {}
# for edge in surfnet.edges():
#     this_len = surfnet.edges[edge]['length']
#     if this_len not in surfnet_lengths:
        # surfnet_lengths[this_len] = None

print(list(abilene_lengths.keys()))
print()
# print(list(surfnet_lengths.keys()))

temp = 1