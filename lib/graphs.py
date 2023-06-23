import networkx as nx
import matplotlib.pyplot as plt
import importlib
from lib.common_random import CommonRandom

class QONgraph:
    ### private methods:

    def _teaver_graph(self, data_directory):
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
            G.add_edge(from_node, to_node)
        
        return G

    def _graph_obj_for_ATT(self):
        ### ATT
        ATT = self._teaver_graph(f'{self.config.data_directory.path}/ATT/')

        return ATT
    
    def _graph_obj_for_Abilene(self):
        ### Abilene
        with open(f'{self.config.data_directory.path}/Abilene/topo-2003-04-10.txt') as file:
                data = [line.rstrip() for line in file]
        data = [line.split('\t') for line in data]
        topology = data[18:]

        nodes = set()

        for edge in topology:
            src_node = edge[0]
            dst_node = edge[1]
            nodes.add(src_node)
            nodes.add(dst_node)

        Abilene = nx.DiGraph()

        for node in nodes:
            Abilene.add_node(node)

        for edge in topology:
            src_node = edge[0]
            dst_node = edge[1]
            Abilene.add_edge(src_node, dst_node)

        return Abilene
    
    def _graph_obj_for_IBM(self):
        ### IBM
        IBM = self._teaver_graph(f'{self.data_directory.path}/IBM/')

        return IBM
    
    def _graph_obj_for_SURFnet(self):
        ### SURFnet
        # SURFnet = nx.read_gml(f'{config.data_directory.path}/SURFnet/Surfnet.gml')
        SURFnet = nx.read_graphml(f'{config.data_directory.path}/SURFnet/Surfnet.graphml')
        
        return SURFnet
    
    def _graph_obj_for_G50_01(self):
        ### Erdos Renyi G(50, 0.1)
        G_50_01 = nx.erdos_renyi_graph(50, 0.1)

        return G_50_01
    
    def _graph_obj_for_G50_005(self):
        ### Erdos Renyi G(50, 0.05)
        G_50_005 = nx.erdos_renyi_graph(50, 0.05)

        return G_50_005
    
    def _import_graph(self):
        graph_name = self.config.graph.name   
        if graph_name == 'ATT':
            nx_graph = self._graph_obj_for_ATT()
        elif graph_name == 'Abilene':
            nx_graph = self._graph_obj_for_Abilene()
        elif graph_name == 'IBM':
            nx_graph = self._graph_obj_for_IBM()
        elif graph_name == 'SURFnet':
            nx_graph = self._graph_obj_for_SURFnet()
        elif graph_name == 'G(50,0.1)':
            nx_graph = self._graph_obj_for_G50_01()
        elif graph_name == 'G(50,0.05)':
            nx_graph = self._graph_obj_for_G50_005()
        else:
            raise NameError("Invalid graph name specified in the configuration file")

        return nx_graph

    def _initialize_link_capacities(self):
        # link capacities are represented by the internal nx_graph's weights
        capacities = {}
        rand_a = self.config.fixed_params.c_u_v.random_start
        rand_b = self.config.fixed_params.c_u_v.random_stop
        for e in nx.edges(self._nx_graph):
            unif_random_value = int(self.common_random.uniform(rand_a, rand_b))
            capacities[e] = unif_random_value
        nx.set_edge_attributes(self._nx_graph, capacities, name='capacity')

    # def _initialize_node_colors(self):
    #     # set all node colors to the color specified in config:
    #     default_color = self.config.graph.node_color
    #     storage_node_color = self.config.graph.storage_node_color
    #     colors = {}
    #     node_types = nx.get_node_attributes(self._nx_graph, 'type')
    #     for node in self._nx_graph:
    #         if node_types[node] == 'storage':
    #             colors[node] = storage_node_color
    #         else:
    #             colors[node] = default_color
    #     nx.set_node_attributes(self._nx_graph, colors, name='color')

    def _initialize_node_types(self):
        node_type = {}
        storage_nodes_list = self._get_storage_nodes()
        user_pairs_list = self._get_user_pairs()
        all_users = list(map(list, zip(*user_pairs_list)))
        for node in self._nx_graph:
            if node in storage_nodes_list and node in all_users:
                pass # TODO
            elif node in storage_nodes_list:
                node_type[node] = 'storage' # mark as a storage node
            elif node in all_users[0] + all_users[1]:
                node_type[node] = 'up'
            else: 
                node_type[node] = None # just a regular node; nothing special about it
        nx.set_node_attributes(self._nx_graph, node_type, name='type')
        self._set_user_pair_ids(all_users[0], all_users[1])

    def _initialize_graph(self):
        self._initialize_node_types() # sets 'type' attribute of nodes to None or 'storage'
        # self._initialize_node_colors() # colors represent user pairs. user pairs also marked by a number in parenthesis next to node name #TODO
        self._initialize_link_capacities()
    
    def _get_storage_nodes(self):
        return ['NYCMng'] # placeholder. TODO: fix
    
    def _get_user_pairs(self):
        return [('ATLA-M5', 'WASHng'), ('LOSAng', 'KSCYng'), ('STTLng', 'CHINng')] # placeholder. TODO: fix

    def _set_user_pair_ids(self, user_pairs_list_a, user_pairs_list_b):
        ids = {}
        all_users = user_pairs_list_a + user_pairs_list_b
        non_users_list = list(set(list(self._nx_graph.nodes)) - set(all_users))
        for non_user in non_users_list:
            ids[non_user] = None
        for user in all_users:
            try:
                ind = user_pairs_list_a.index(user)
            except ValueError:
                ind = user_pairs_list_b.index(user)
            this_id = ind + 1
            ids[user] = this_id
        nx.set_node_attributes(self._nx_graph, ids, name='up_id')

    ### public methods:

    def __init__(self, config_filename) -> None:
        self.config = importlib.import_module(config_filename, package=None)
        self.common_random = CommonRandom(self.config.random_params.seed)
        self._nx_graph = self._import_graph()
        self._initialize_graph()

    def save_graph(self, filename="graph.png"):
        self._draw_graph(action='save', filename=filename)

    def show_graph(self):
        self._draw_graph(action='show')
    
    def _draw_graph(self, action=None, filename="graph.png"):
        pos = nx.spring_layout(self._nx_graph, seed=0) 
        
        # # node colors:
        # colors = nx.get_node_attributes(self._nx_graph, "color")
        # temp: colors for user pair ids
        colors = ['', 'cyan', 'green', 'yellow', 'pink', 'red']
        
        # edge labels:
        edge_capacities = nx.get_edge_attributes(self._nx_graph, "capacity")

        # draw graph:
        # draw storage nodes:
        nx.draw_networkx_nodes(
            self._nx_graph, 
            pos, 
            nodelist=[n for (n, ddict) in self._nx_graph.nodes(data=True) if ddict["type"] == 'storage'], 
            node_color = 'gray', 
            node_size = 700,
            node_shape='^'
            ).set_edgecolor('red')
        # draw user pair nodes: 
        nx.draw_networkx_nodes(
            self._nx_graph, 
            pos, 
            nodelist=[n for (n, ddict) in self._nx_graph.nodes(data=True) if ddict["type"] == 'up'], 
            node_color = [colors[ddict['up_id']] for (n, ddict) in self._nx_graph.nodes(data=True) if ddict["type"] == 'up'], 
            node_size = 700,
            node_shape='s'
            ).set_edgecolor('red')
        # draw rest of the nodes:
        nx.draw_networkx_nodes(
            self._nx_graph, 
            pos, 
            nodelist=[n for (n, ddict) in self._nx_graph.nodes(data=True) if ddict["type"] not in ['storage', 'up']], 
            node_color = 'white', 
            node_size = 600,
            node_shape = 'o'
            ).set_edgecolor('black')
        # all nodes' labels
        nx.draw_networkx_labels(self._nx_graph, pos)
        # draw all edges:
        nx.draw_networkx_edges(self._nx_graph, pos, arrowsize = 20)
        # edge labels (capacities):
        # nx.draw_networkx_edge_labels(self._nx_graph, pos, edge_labels = edge_capacities)

        if action == 'save':
            plt.savefig(filename, format = "PNG")
        if action == 'show':
            plt.show()
    


