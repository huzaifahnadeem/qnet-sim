'''
This file contains objects, classes, functions, etc associated with the network
'''
from netsquid.nodes import Network as ns_Network
from netsquid.nodes.node import Node as ns_Node
from netsquid.nodes.connections import DirectConnection
from netsquid.components import QuantumChannel
# from netsquid.components.models.delaymodels import FibreDelayModel # TODO: need to add this later
import networkx as nx

import globals
from network_topologies import network_choice
from entities import NodeEntity

class Node(ns_Node):
    def __init__(self, name, ID=None, qmemory=None, port_names=None, node_entity=None) -> None:
        super().__init__(name=name, ID=ID, qmemory=qmemory, port_names=port_names)
        self.entity = node_entity

class Network(ns_Network):
    def __init__(self, name=globals.args.net_top.value) -> None:
        self.net_dict = network_choice()
        self.nx_graph = nx.Graph() # used for yen's algorithm and for visualzing the network situation (<- TODO this second part)
        self.offline_paths = {} # generated by yen's alg in QPASS
        # TODO: assumed input network is SLMP_GRID_4x4. so num of quantum memories hardcoded below. change later when you implement other networks
        super().__init__(name=name)
        super().add_nodes(self._create_nodes())
        
        # TODO: add nodes and connections (as per the paper (incl. edge width etc. use the same terms as the paper))
        
        # Note the difference: 
        # paper vs here: channels (paper) = DirectConnection (here) (each of which has 2 channels internally). Edges (paper) = A collection of connections here
        self._create_and_add_connections()

        if globals.args.alg is globals.ALGS.QPASS:
            self._run_yens_alg()
        else:
            raise NotImplementedError("QCAST not implemented yet")
        
        # TODO: log at the end of init that network has been initialized? or maybe in main somewhere

    def _create_nodes(self):
        for node_name in self.net_dict.keys():
            self.nx_graph.add_node(node_name) # TODO: Assuming unique name. might require an ID field if that is not the case. for SLMP_GRID_4x4 this is fine.
            yield Node(
                name = node_name,
                ID = int(node_name[1:]), # TODO: this is assuming SLMP_GRID_4x4. make dynamic
                qmemory = None,     # TODO: update
                port_names = None,  # TODO: update
                node_entity = NodeEntity(), # TODO: update
            )
    
    def _create_and_add_connections(self) -> None:
        already_done = []
        for u in self.net_dict.keys():
            for (v, width) in self.net_dict[u]:
                if ((u, v) not in already_done) and ((v, u) not in already_done):
                    # loss_model = FibreLossModel(p_loss_init=config.channel_loss_p_loss_init, p_loss_length=config.channel_loss_p_loss_length) # TODO: need to add this later
                    for channel_num in range(width): # TODO: bugfix . check this thoroughly later, but it seems like this width thing is not working. The network only keeps the last direct channel made and overwrites the previous ones. so if width 3, it only makes 1 connection with #3 in its name. this is fine for slmp grid ig but needs work
                        self.nx_graph.add_edge(u, v)
                        channel_uv = QuantumChannel(
                                name = f"channel | {u}-->{v} #{channel_num+1} | quantum",
                                # length = config.connections_length,
                                # models={"delay_model": FibreDelayModel()},
                                # models = {'quantum_loss_model': loss_model},
                            )
                        channel_vu = QuantumChannel(
                                name = f"channel | {u}<--{v} #{channel_num+1} | quantum",
                                # length = config.connections_length,
                                # models={"delay_model": FibreDelayModel()},
                                # models = {'quantum_loss_model': loss_model},
                            )
                        
                        connection = DirectConnection(
                                name = f"dirConn. | {u}<->{v} #{channel_num+1} | quantum",
                                channel_AtoB = channel_uv,
                                channel_BtoA = channel_vu
                            ) # Note that each connection here has a property uid which is a a unique identifier for this entity in the simulation. So the part in the paper where they ask for globally unique ID is covered.
                        
                        # TODO: may need to call node.connect_to and forwarding ports to quantum memories

                        super().add_connection(
                            node1 = u,
                            node2 = v,
                            connection = connection,
                        )
                    
                    already_done.append((u, v))
                    already_done.append((v, u))

    def _run_yens_alg(self):
        # nx.shortest_simple_paths function uses yen's algorithm as per the the reference on networkx' website: https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.simple_paths.shortest_simple_paths.html
        # This sub function is also adapted from the same source:
        
        from itertools import islice
        def k_shortest_paths(G, source, target, k, weight=None):
            return list(islice(nx.shortest_simple_paths(G, source, target, weight=weight), k))

        # need three positional params for these fns (to be used as 'weight' param when calling the fn above). params = start node, end node, dict containing properties of the edge
        def sum_dist(u, v, _):
            raise NotImplementedError("SumDist metric not implemented yet") # TODO

        def creation_rate(u, v, _):
            raise NotImplementedError("CR metric not implemented yet") # TODO

        def bottleneck_cap(u, v, _):
            raise NotImplementedError("BotCap metric not implemented yet") # TODO

        k = globals.args.yen_n

        if globals.args.yen_metric is globals.YEN_METRICS.SUMDIST:
            weight_fn = sum_dist
        elif globals.args.yen_metric is globals.YEN_METRICS.CR:
            weight_fn = creation_rate
        elif globals.args.yen_metric is globals.YEN_METRICS.BOTCAP:
            weight_fn = bottleneck_cap
        elif globals.args.yen_metric is globals.YEN_METRICS.HOPCOUNT:
            weight_fn = None

        for n1 in self.net_dict.keys():
            for n2 in self.net_dict.keys():
                if n1 == n2:
                    continue
                self.offline_paths[(n1, n2)] = k_shortest_paths(self.nx_graph, source=n1, target=n2, k=k, weight=weight_fn)
