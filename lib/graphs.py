import networkx as nx
import matplotlib.pyplot as plt
import importlib
from lib.common_random import CommonRandom

class QONgraph:
    ### private methods: # TODO most of the functions are unneccessary for each object. maybe move these to a separate file

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
        IBM = self._teaver_graph(f'{self.config.data_directory.path}/IBM/')

        return IBM
    
    def _graph_obj_for_SURFnet(self):
        ### SURFnet
        # SURFnet = nx.read_gml(f'{self.config.data_directory.path}/SURFnet/Surfnet.gml')
        SURFnet = nx.read_graphml(f'{self.config.data_directory.path}/SURFnet/Surfnet.graphml')
        
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
        graph_name = self.workload.graph.name   
        if graph_name == 'ATT':
            nx_graph = self._graph_obj_for_ATT()
        elif graph_name == 'Abilene':
            nx_graph = self._graph_obj_for_Abilene()
        elif graph_name == 'IBM':
            nx_graph = self._graph_obj_for_IBM()
        elif graph_name == 'SURFnet':
            nx_graph = self._graph_obj_for_SURFnet()
        elif graph_name == 'G(50, 0.1)':
            nx_graph = self._graph_obj_for_G50_01()
        elif graph_name == 'G(50, 0.05)':
            nx_graph = self._graph_obj_for_G50_005()
        elif graph_name == 'PA(50, 2)':
            raise NameError("The graph 'PA(50, 2)' not implemented yet") # TODO
        elif graph_name == 'PA(50, 3)':
            raise NameError("The graph 'PA(50, 3)' not implemented yet") # TODO
        else:
            raise NameError("Invalid graph name specified in the workload file")

        return nx_graph

    def _link_capacity_fidelity_common(self, attribute_name):
        # link capacities and fidelities are saved by the internal nx_graph's nodes' 'capacity' and 'fidelity' attributes, respectively

        from_workload = {
            'capacity': {
                'start': self.workload.fixed_params.c_u_v.random_start,
                'stop': self.workload.fixed_params.c_u_v.random_stop,
            },
            'fidelity': {
                'start': self.workload.fixed_params.link_fidelity.random_start,
                'stop': self.workload.fixed_params.link_fidelity.random_stop,
            },
        }

        values = {}
        rand_a = from_workload[attribute_name]['start']
        rand_b = from_workload[attribute_name]['stop']
        
        if type(self._nx_graph) is nx.MultiGraph: # for SURFnet
            edges_iterator = self._nx_graph.edges(keys=True) # edge 'keys' are needed to add attributes for multigraphs
        else: # only SURFnet is multigraph
            edges_iterator = nx.edges(self._nx_graph)

        for e in edges_iterator:
            unif_random_value = self.common_random.uniform(rand_a, rand_b)
            values[e] = unif_random_value
        nx.set_edge_attributes(self._nx_graph, values, name=attribute_name)

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
        self._initialize_link_fidelities()
    
    def _random_storage_nodes_selection(self):
        # TODO: no_of_storage_nodes is randomly selected for now. Should this be changed?
        no_of_storage_nodes = self.common_random.randint(0, self._nx_graph.number_of_nodes())
        selected_nodes = []
        for _ in range(no_of_storage_nodes):
            while True:
                random_node = self.common_random.choice(list(self._nx_graph.nodes()))
                if random_node not in selected_nodes:
                    selected_nodes.append(random_node)
                    break # break the while loop. Continues to randomly pick another node if picked an already-picked node again
        return selected_nodes

    def _degree_storage_nodes_selection(self):
        # TODO: no_of_storage_nodes is randomly selected for now. Should this be changed?
        no_of_storage_nodes = self.common_random.randint(0, self._nx_graph.number_of_nodes())
        selected_nodes = []
        nodes_list = list(self._nx_graph.degree) # TODO is this correct?
        nodes_list = sorted(nodes_list, key=lambda x: x[1], reverse=True)
        for _ in range(no_of_storage_nodes):
            selected_nodes.append(nodes_list[0][0])
            del nodes_list[0]
        
        return selected_nodes

    def _get_storage_nodes(self):
        selection_scheme = self.workload.storage_servers.selection_scheme
        storage_nodes = []
        if selection_scheme == 'random':
            storage_nodes = self._random_storage_nodes_selection()
        elif selection_scheme == 'degree':
            storage_nodes = self._degree_storage_nodes_selection()
        elif selection_scheme == 'manual':
            storage_nodes = self.workload.storage_servers.manual_storage_servers
        else:
            raise NameError("Invalid storage selection scheme in the given workload file.")

        return storage_nodes
    
    def _random_user_pairs_selection(self):
        # note that currently each node can be part of only one pair
        no_of_user_pairs = self.workload.user_pairs.number
        nodes_list = list(self._nx_graph.nodes())
        selected_pairs = [] # list of tuples
        for _ in range(no_of_user_pairs):
            user1 = self.common_random.choice(nodes_list)
            nodes_list.remove(user1)
            user2 = self.common_random.choice(nodes_list)
            nodes_list.remove(user2)
            selected_pairs.append((user1, user2))
        
        return selected_pairs

    def _get_user_pairs(self):
        selection_scheme = self.workload.user_pairs.selection_scheme
        user_pairs = []
        if selection_scheme == 'random':
            user_pairs = self._random_user_pairs_selection()
        elif selection_scheme == 'manual':
            user_pairs = self.workload.user_pairs.manual_user_pairs
        else:
            raise NameError("Invalid user pairs selection scheme in the given workload file.")

        return user_pairs

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

    def _initialize_link_capacities(self):
        self._link_capacity_fidelity_common('capacity')

    def _initialize_link_fidelities(self):
        self._link_capacity_fidelity_common('fidelity')

    def _kk_into_fr(self, G):
        # kamada kawai layout for initial pos feed into fruchterman reingold. 
        # ref: https://en.wikipedia.org/wiki/Force-directed_graph_drawing#:~:text=A%20combined%20application%20of%20different%20algorithms%20is%20helpful%20to%20solve%20this%20problem.%5B10%5D%20For%20example%2C%20using%20the%20Kamada%E2%80%93Kawai%20algorithm%5B11%5D%20to%20quickly%20generate%20a%20reasonable%20initial%20layout%20and%20then%20the%20Fruchterman%E2%80%93Reingold%20algorithm%5B12%5D%20to%20improve%20the%20placement%20of%20neighbouring%20nodes.
        inital_pos = nx.kamada_kawai_layout(G)
        final_pos = nx.fruchterman_reingold_layout(G, pos = inital_pos)
        return final_pos

    ### public methods:

    def __init__(self, config_filename) -> None:
        self.config = importlib.import_module(config_filename, package=None)
        self.workload = importlib.import_module('.workload', package='workloads') # TODO: pass workload file name as param
        self.common_random = CommonRandom(self.config.random_params.seed)
        self._nx_graph = self._import_graph()
        self._initialize_graph()

    def save_graph(self, filename="graph.png"):
        self._draw_graph(action='save', filename=filename)

    def show_graph(self):
        self._draw_graph(action='show')
    
    def _draw_graph(self, action=None, filename="graph.png"):
        class config: # shorter aliases for longer variable names containing config info from the config file
            class layout:
                _function_for = {
                'fruchterman reingold': nx.fruchterman_reingold_layout,
                'circular': nx.circular_layout,
                'spectral': nx.random_layout,
                'random': nx.spectral_layout,
                'spring': nx.spring_layout, # internally in networkx is equal to 'fruchterman reingold'
                'kamada kawai': nx.kamada_kawai_layout,
                'planar': nx.planar_layout,
                'spiral': nx.spiral_layout,
                'kk --> fr': self._kk_into_fr,
                }
                
                function = _function_for[self.config.graph.layout.name]
            
            class plot:
                width = self.config.graph.plot.width
                height = self.config.graph.plot.height
                dpi = self.config.graph.plot.dpi


            class edges:
                arrow_size = self.config.graph.edges.arrow_size
            
            class nodes:
                class up:
                    colors = [None, *self.config.graph.nodes.user_pair.colors] # later on using up_ids as index for colors so adding a None at index 0
                    size = self.config.graph.nodes.user_pair.size
                    shape = self.config.graph.nodes.user_pair.shape
                    edge_color = self.config.graph.nodes.user_pair.edge_color

                class storage:
                    color = self.config.graph.nodes.storage.color
                    size = self.config.graph.nodes.storage.size
                    shape = self.config.graph.nodes.storage.shape
                    edge_color = self.config.graph.nodes.storage.edge_color
                
                class other:
                    color = self.config.graph.nodes.other.color
                    size = self.config.graph.nodes.other.size
                    shape = self.config.graph.nodes.other.shape
                    edge_color = self.config.graph.nodes.other.edge_color

        # set up node positions in the graph:
        pos = config.layout.function(self._nx_graph)

        # plt figure size:
        plt.figure(
            figsize = (
                config.plot.width, 
                config.plot.height
                ), 
                dpi = config.plot.dpi
                ) # 'width' x 'height' in inches s.t. each 1 inch is equal to 'dpi' pixels

        # draw graph:
        # draw storage nodes:
        nx.draw_networkx_nodes(
            self._nx_graph, 
            pos, 
            nodelist = [n for (n, ddict) in self._nx_graph.nodes(data = True) if 'storage' in ddict["type"]], 
            node_color = config.nodes.storage.color, 
            node_size = config.nodes.storage.size,
            node_shape = config.nodes.storage.shape
            ).set_edgecolor(config.nodes.storage.edge_color)
        
        # draw user pair nodes: (note: type 'up' = 'user pair') 
        nx.draw_networkx_nodes(
            self._nx_graph, 
            pos, 
            nodelist = [n for (n, ddict) in self._nx_graph.nodes(data = True) if 'up' in ddict["type"]], 
            node_color = [config.nodes.up.colors[ddict['up_id']] for (n, ddict) in self._nx_graph.nodes(data = True) if 'up' in ddict["type"]], 
            node_size = config.nodes.up.size,
            node_shape = config.nodes.up.shape
            ).set_edgecolor(config.nodes.up.edge_color)

        # draw rest of the nodes that have no special type:
        nx.draw_networkx_nodes(
            self._nx_graph, 
            pos, 
            nodelist = [n for (n, ddict) in self._nx_graph.nodes(data = True) if ddict["type"] == []], 
            node_color = config.nodes.other.color, 
            node_size = config.nodes.other.size,
            node_shape = config.nodes.other.shape
            ).set_edgecolor(config.nodes.other.edge_color)
        
        # all nodes' labels
        # TODO: display capacity of the storage servers maybe in title or legend from 'self.workload.fixed_params.B_s'
        node_labels = {}
        for (n, ddict) in self._nx_graph.nodes(data = True):
            node_labels[n] = str(n) if ddict["up_id"] is None else str(n) + ' (' + str(ddict["up_id"]) + ')'
        nx.draw_networkx_labels(
            self._nx_graph, 
            pos,
            labels = node_labels
            )
        
        # draw all edges:
        nx.draw_networkx_edges(self._nx_graph, pos, arrowsize = config.edges.arrow_size)
        
        # edge labels: # TODO: the following code works fine but graph is too messy. fix that and then print edge labels with both capacity and fidelity neatly
        # edge_capacities = nx.get_edge_attributes(self._nx_graph, "capacity")
        # nx.draw_networkx_edge_labels(self._nx_graph, pos, edge_labels = edge_capacities)
        # edge_fidelities = nx.get_edge_attributes(self._nx_graph, "fidelity")
        # for k in edge_fidelities:
        #     edge_fidelities[k] = round(edge_fidelities[k], 2)
        # nx.draw_networkx_edge_labels(self._nx_graph, pos, edge_labels = edge_fidelities)

        # for now, legend is added as title:
        plot_title = 'squares = storage servers; colors & (#) = user pairs'

        if action == 'save':
            plt.savefig(filename, format = "PNG")
        if action == 'show':
            plt.title(plot_title)
            plt.show()
    
