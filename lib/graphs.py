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

    def _initialize_node_types(self):
        node_type = {}
        storage_nodes_list = self._get_storage_nodes()
        user_pairs_list = self._get_user_pairs()
        all_users = list(map(list, zip(*user_pairs_list)))
        for node in self._nx_graph:
            node_type[node] = []
            if node in storage_nodes_list:
                node_type[node].append('storage') # mark as a storage node
            if node in all_users[0] + all_users[1]:
                node_type[node].append('up')
        nx.set_node_attributes(self._nx_graph, node_type, name='type')
        self._set_user_pair_ids(all_users[0], all_users[1])

    def _initialize_graph(self):
        self._initialize_node_types()
        self._initialize_link_capacities()
    
    def _get_storage_nodes(self):
        return ['NYCMng'] # placeholder. TODO: fix
    
    def _get_user_pairs(self):
        return [('ATLA-M5', 'WASHng'), ('LOSAng', 'KSCYng'), ('STTLng', 'CHINng'), ('NYCMng', 'ATLAng')] # placeholder. TODO: fix

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
        class config:
            class layout:
                _func_map = {
                'fruchterman reingold': nx.fruchterman_reingold_layout,
                'circular': nx.circular_layout,
                'spectral': nx.random_layout,
                'random': nx.spectral_layout,
                'spring': nx.spring_layout, # internally in networkx is equal to 'fruchterman reingold'
                'kamada kawai': nx.kamada_kawai_layout,
                'planar': nx.planar_layout,
                'spiral': nx.spiral_layout,
                }
                
                function = _func_map['kamada kawai']
                # function = _func_map['fruchterman reingold'] 
                # kamada kawai seems best for our use. fruchterman reingold also seems good

            class edges:
                arrow_size = 20
            
            class nodes:
            
                class up:
                    colors = [None, 'cyan', 'green', 'yellow', 'pink', 'red', 'purple', 'blue', 'indigo'] # later on using up_ids as index for colors so adding a None at index 0
                    size = 700
                    shape = 's' # square
                    edge_color = 'green'

                class storage:
                    color = 'gray'
                    size = 1000
                    shape = '^' # triangle
                    edge_color = 'red'
                
                class other:
                    color = 'white'
                    size = 600
                    shape = 'o' # circle
                    edge_color = 'black'
    
        pos = config.layout.function(self._nx_graph)

        # edge labels:
        edge_capacities = nx.get_edge_attributes(self._nx_graph, "capacity")

        # draw graph:
        # draw user pair nodes: (note: type 'up' = 'user pair') 
        nx.draw_networkx_nodes(
            self._nx_graph, 
            pos, 
            nodelist = [n for (n, ddict) in self._nx_graph.nodes(data = True) if 'up' in ddict["type"]], 
            node_color = [config.nodes.up.colors[ddict['up_id']] for (n, ddict) in self._nx_graph.nodes(data = True) if 'up' in ddict["type"]], 
            node_size = config.nodes.up.size,
            node_shape = config.nodes.up.shape
            ).set_edgecolor(config.nodes.up.edge_color)
        
        # draw storage nodes:
        nx.draw_networkx_nodes(
            self._nx_graph, 
            pos, 
            nodelist = [n for (n, ddict) in self._nx_graph.nodes(data = True) if 'storage' in ddict["type"]], 
            node_color = config.nodes.storage.color, 
            node_size = config.nodes.storage.size,
            node_shape = config.nodes.storage.shape
            ).set_edgecolor(config.nodes.storage.edge_color)

        # draw rest of the nodes that have no special type:
        nx.draw_networkx_nodes(
            self._nx_graph, 
            pos, 
            nodelist = [n for (n, ddict) in self._nx_graph.nodes(data = True)], 
            node_color = config.nodes.other.color, 
            node_size = config.nodes.other.size,
            node_shape = config.nodes.other.shape
            ).set_edgecolor(config.nodes.other.edge_color)
        
        # all nodes' labels
        node_labels = {}
        for (n, ddict) in self._nx_graph.nodes(data = True):
            node_labels[n] = n if ddict["up_id"] is None else n + ' (' + str(ddict["up_id"]) + ')'
        nx.draw_networkx_labels(
            self._nx_graph, 
            pos,
            labels = node_labels
            )
        
        # draw all edges:
        nx.draw_networkx_edges(self._nx_graph, pos, arrowsize = config.edges.arrow_size)
        
        # edge labels (capacities):
        # nx.draw_networkx_edge_labels(self._nx_graph, pos, edge_labels = edge_capacities)

        if action == 'save':
            plt.savefig(filename, format = "PNG")
        if action == 'show':
            plt.show()
    


