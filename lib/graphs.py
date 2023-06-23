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
            unif_random_value = self.common_random.uniform(rand_a, rand_b)
            capacities[e] = unif_random_value
        nx.set_edge_attributes(self._nx_graph, capacities, name='capacity')

    ### public methods:

    def __init__(self, config_filename) -> None:
        self.config = importlib.import_module(config_filename, package=None)
        self.common_random = CommonRandom(self.config.random_params.seed)
        self._nx_graph = self._import_graph()
        self._highlighted_nodes = [] # = ['NYCMng'] # test # TEMP TODO. do i need this?
        self._initialize_link_capacities()

    def save_graph(self, filename="graph.png"):
        self._draw_graph(action='save', filename=filename)

    def show_graph(self):
        self._draw_graph(action='show')
    
    def _draw_graph(self, action=None, filename="graph.png"):
        color_map = [self.config.graph.highlight_color if node_name in self._highlighted_nodes else self.config.graph.node_color for node_name in list(self._nx_graph.nodes)]
        
        # pos = nx.spring_layout(self._nx_graph, seed=7) # arbitrary seed value here
        # # nodes:
        # nx.draw_networkx_nodes(self._nx_graph, pos, node_size=700)
        # # edges:
        # nx.draw_networkx_edges(self._nx_graph, pos, width=6, alpha=0.5, edge_color="b", style="dashed")
        # # node labels:
        # nx.draw_networkx_labels(self._nx_graph, pos, font_size=20, font_family="sans-serif")
        # # edge labels:
        edge_labels = nx.get_edge_attributes(self._nx_graph, "capacity")
        # nx.draw_networkx_edge_labels(self._nx_graph, pos,  edge_labels)

        nx.draw_networkx(self._nx_graph, node_color=color_map, with_labels = True)

        if action == 'save':
            plt.savefig(filename, format="PNG")
        if action == 'show':
            plt.show()
    


