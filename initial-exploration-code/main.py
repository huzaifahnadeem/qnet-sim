#!/usr/bin/env python

# slmp global with components (using protocols approach) (for slmp global without components using simulation engine approach -- see ./examples/slmo_wo_channels.py)

import netsquid as ns
from netsquid.components import QuantumChannel
from netsquid.components import ClassicalChannel
from netsquid.components.models.delaymodels import FibreDelayModel
from netsquid.nodes import DirectConnection
from netsquid.protocols import NodeProtocol
from netsquid.components.qsource import QSource, SourceStatus
from netsquid.qubits.state_sampler import StateSampler
import netsquid.qubits.ketstates as ks
from netsquid.components.models.qerrormodels import FibreLossModel
from netsquid.qubits.qubitapi import create_qubits, assign_qstate
# from pydynaa import EventExpression
import networkx as nx
import matplotlib.pyplot as plt
import copy
import numpy as np
import random
import constants as consts
import lower_level_fns

seed = 4
ns.util.simtools.set_random_state(seed=seed)
random.seed(seed)
ns.qubits.qformalism.set_qstate_formalism(ns.qubits.qformalism.QFormalism.KET)

# tmp_qubit_teleported_info = []

class config:
    num_of_qubits_per_memory = 4
    # connections_length = 4e-3
    connections_length = 20
    channel_loss_p_loss_init = 1-0.95 #0.2 
    channel_loss_p_loss_length = 0 #0.2

class MyNode(ns.nodes.Node):
    def __init__(self, name) -> None:
        super().__init__(name=name)
        self.neighbours = []
        self.send_EPR_neighbours = [] # = all the neighbours with an id lower than self.node

class Network():
    def __init__(self, net_graph_dict) -> None:
        self._net_graph_dict = net_graph_dict
        self.nodes_names = self._net_graph_dict.keys()
        self.nodes = {}
        self.num_of_qubits_per_memory = config.num_of_qubits_per_memory
        self.connections = []
        self.internet = []
        self.num_neighbours = {}
        self.nx_graph = nx.Graph()

        self._setup_network()
        self._init_nx_graph()

    def _setup_network(self) -> None:
        self._set_up_nodes()
        self._set_up_connections()

    def _init_nx_graph(self) -> None:
        self.nx_graph.add_nodes_from(self.nodes_names)
        done = []
        for u in self._net_graph_dict:
            for v in self._net_graph_dict[u]:
                if ((u, v) not in done) and ((v, u) not in done):
                    self.nx_graph.add_edge(u, v, color='black')
                    self.nx_graph.add_edge(v, u, color='black')
                    done.append((u, v))
                    done.append((v, u))
    
    def _update_nx_graph(self) -> None:
        for this_node_name in self.nodes_names:
            this_node = self.nodes[this_node_name]
            neighbours_that_send_epr_qbit = [] # you wait to receive epr pair bit from these neighbours
            for neighbour in this_node.neighbours:
                if neighbour not in this_node.send_EPR_neighbours:
                    neighbours_that_send_epr_qbit.append(neighbour)
            for neighbour in neighbours_that_send_epr_qbit:
                neighbour_idx = this_node.neighbours.index(neighbour)
                received_epr_bit_from_this_neighbout = (this_node.qmemory.peek(positions=[neighbour_idx], skip_noise=True) != [None])
                if received_epr_bit_from_this_neighbout: # i.e. check if there is a qubit:
                    self.nx_graph.edges[this_node_name, neighbour]['color'] = "red"
                    self.nx_graph.edges[neighbour, this_node_name]['color'] = "red"

    def draw_nx_graph(self) -> None:
        self._update_nx_graph()
        edges = self.nx_graph.edges()
        colors = [self.nx_graph[u][v]['color'] for u,v in edges]
        pos = dict(zip(self.nx_graph.nodes(), [[0,3],[1,3],[2,3],[3,3],
                                               [0,2],[1,2],[2,2],[3,2],
                                               [0,1],[1,1],[2,1],[3,1],
                                               [0,0],[1,0],[2,0],[3,0]]))
        plt.clf()
        nx.draw_networkx(self.nx_graph, edge_color=colors, pos=pos)
        plt.savefig('./tmp-graph')

    def shortest_src_dst_paths(self, src, dst, net_graph):
        nx_graph = copy.deepcopy(net_graph)
        paths = []
        while True:
            try:
                p = nx.shortest_path(nx_graph, src, dst, weight=None, method='dijkstra')
            except nx.exception.NetworkXNoPath: # stop if not further paths
                break
            p_edges = []
            for i in range(1, len(p)):
                u = p[i-1]
                v = p[i]
                p_edges.append((u,v))
            nx_graph.remove_edges_from(p_edges)
            paths.append(p)
        return paths

    def ext_phase_subgraph(self):
        non_entangling_edges = []
        for (u, v) in self.nx_graph.edges:
            edge_not_entangling_link = self.nx_graph.edges[(u, v)]['color'] != 'red'
            if edge_not_entangling_link:
                non_entangling_edges.append((u, v))
        ext_phase_subgraph = copy.deepcopy(self.nx_graph)
        ext_phase_subgraph.remove_edges_from(non_entangling_edges)

        # tmp:
        pos = dict(zip(self.nx_graph.nodes(), [[0,3],[1,3],[2,3],[3,3],
                                               [0,2],[1,2],[2,2],[3,2],
                                               [0,1],[1,1],[2,1],[3,1],
                                               [0,0],[1,0],[2,0],[3,0]]))
        plt.clf()
        nx.draw_networkx(ext_phase_subgraph, pos=pos)
        plt.savefig('./tmp-graph-ext-ph')

        return ext_phase_subgraph

    def _set_up_nodes(self) -> None:
        for n_name in self.nodes_names:
            # create this node object:
            self.nodes[n_name] = MyNode(name=n_name)
            # these are useful pieces of data for protocols:
            self.nodes[n_name].neighbours = self._net_graph_dict[n_name]
            for neighbour in self.nodes[n_name].neighbours:
                if int(neighbour[1:]) < int(n_name[1:]):
                    self.nodes[n_name].send_EPR_neighbours.append(neighbour)

            # TODO: add noise model for qubit decoherence in memory
            # add the primary quantum memory to this node:
            this_memory = ns.components.QuantumMemory(
                name = f"{n_name}-memory", 
                num_positions = self.num_of_qubits_per_memory,
                )
            self.nodes[n_name].add_subcomponent(this_memory, name="memory")
            # add a quantum source so that it can generate entangled particles:
            # also adding a seconday memory of size 2 to temporarily hold ebits from qsource to form local entanglements
            ebit_mem = ns.components.QuantumMemory(
                name = f"{n_name}-ebit-mem", 
                num_positions = 2,
                )
            self.nodes[n_name].add_subcomponent(ebit_mem, name="ebit-mem")
            # TODO: there is some problem with this state sampler: should generate 2 bits with |0> with 1 prob. its not doing that.
            state_sampler = StateSampler([ks.b00], [1.0]) # for entangled qbits we want them to have |00> state initially
            this_qsource = QSource(
                    name = "qsource", 
                    state_sampler = state_sampler, 
                    num_ports = 2, # since we are generating 2 entangled particles at any time
                    status = SourceStatus.EXTERNAL # we use external clock to operate qsource. it will generate qbits when it receives a message on its trigger port.
                )
            self.nodes[n_name].add_subcomponent(this_qsource)
            # connect to the ebit-mem to temporarily hold any generated ebits from qsource
            this_qsource.ports["qout0"].connect(self.nodes[n_name].subcomponents['ebit-mem'].ports['qin0'])
            this_qsource.ports["qout1"].connect(self.nodes[n_name].subcomponents['ebit-mem'].ports['qin1'])
    
    def _set_up_connections(self) -> None:
        done = []
        for u_name in self.nodes_names: # set up quantum connections
            for v_name in self._net_graph_dict[u_name]:
                if ((u_name, v_name) not in done) and ((v_name, u_name) not in done):
                    # the objects for node u and node v:
                    u = self.nodes[u_name]
                    v = self.nodes[v_name]

                    # loss model for qubits during transmission:
                    loss_model = FibreLossModel(p_loss_init=config.channel_loss_p_loss_init, p_loss_length=config.channel_loss_p_loss_length)

                    channel_uv = QuantumChannel(
                            name = "{u_name}-->{v_name}", 
                            length = config.connections_length,
                            # models={"delay_model": FibreDelayModel()},
                            models = {'quantum_loss_model': loss_model},
                        )
                    channel_vu = QuantumChannel(
                            name = f"{u_name}<--{v_name}",
                            length = config.connections_length,
                            # models={"delay_model": FibreDelayModel()},
                            models = {'quantum_loss_model': loss_model},
                        )
                    
                    connection = DirectConnection(
                            name = f"{u_name}<==>{v_name}",
                            channel_AtoB = channel_uv,
                            channel_BtoA = channel_vu
                        )

                    u.connect_to(
                        remote_node=v, 
                        connection=connection,
                        local_port_name=f"{u_name}<->{v_name}", 
                        remote_port_name=f"{v_name}<->{u_name}",
                    ) # this should also connect v to u over the connection so no need to call v.connect_to(u)

                    u.ports[f"{u_name}<->{v_name}"].forward_input(u.qmemory.ports[f'qin{u.neighbours.index(v_name)}'])

                    self.connections.append(connection)
                    done.append((u_name, v_name))
                    done.append((v_name, u_name))
        
        # add classical connections:
        # for now adding connections between each pair of nodes (to simulate the internet). Makes things simple for now:
        done = []
        for u_name in self.nodes_names:
            for v_name in self.nodes_names:
                if u_name == v_name:
                    continue
                else:
                    if ((u_name, v_name) not in done) and ((v_name, u_name) not in done):
                        # the objects for node u and node v:
                        u = self.nodes[u_name]
                        v = self.nodes[v_name]

                        channel_uv = ClassicalChannel(
                                name = "{u_name}-->{v_name}",
                            )
                        channel_vu = ClassicalChannel(
                                name = f"{u_name}<--{v_name}",
                            )
                        
                        connection = DirectConnection(
                                name = f"{u_name}<==>{v_name}",
                                channel_AtoB = channel_uv,
                                channel_BtoA = channel_vu
                            )
                        
                        u.connect_to(
                            remote_node = v, 
                            connection = connection,
                            local_port_name = f"(internet) {u_name}<->{v_name}", 
                            remote_port_name = f"(internet) {v_name}<->{u_name}",
                        ) # this should also connect v to u over the connection so no need to call v.connect_to(u)

                        self.internet.append(connection)
                        done.append((u_name, v_name))
                        done.append((v_name, u_name))

# class MyProtocol(NodeProtocol):
#     def __init__(self, node, qubit=None) -> None:
#         super().__init__(node)
#         self.qubit = qubit
    
#     def run(self) -> None:
#         if self.qubit is not None:
#             # Send (TX) qubit to the other node via port's output:
#             if self.node.name == 'n10': # src
#                 self.node.ports['n10<->n11'].tx_output(self.qubit)
#                 print('src-end')
#             else: # for n11
#                 pass
#         if self.node.name != 'n10': # src
#             while True:
#                 # Wait (yield) until input has arrived on our port:
#                 yield self.await_port_input(self.node.ports["n11<->n10"])
#                 # Receive (RX) qubit on the port's input:
#                 message = self.node.ports["n11<->n10"].rx_input()
#                 qubit = message.items[0]
#                 meas, prob = ns.qubits.measure(qubit)
#                 print(f"{ns.sim_time():5.1f}: {self.node.name} measured "
#                     f"with probability {prob:.2f}")
#                 print('n11-end')

class ExternalPhase(NodeProtocol):
    def __init__(self, node) -> None:
        super().__init__(node)
    
    def run(self) -> None:
        # for now, the alg is such that each node with the higher node id is responsible for making an EPR pair and then sending it to its neighbour with lower id
        for n in self.node.send_EPR_neighbours: 
            # generate a pair of entangled bits:
            self.node.subcomponents['qsource'].trigger()
            
            # wait until the initial bits that will be entangled are generated:
            while True:
                expr1 = self.await_port_input(self.node.subcomponents['ebit-mem'].ports['qin0'])
                expr2 = self.await_port_input(self.node.subcomponents['ebit-mem'].ports['qin1'])
                epr_pair_initialized_expr = yield expr1 & expr2
                epr_pair_initialized = epr_pair_initialized_expr.first_term.value
                if epr_pair_initialized:
                    q1 = self.node.subcomponents['ebit-mem'].mem_positions[0].get_qubit(remove=True, skip_noise=True) # skip noise since this is just a temporary memory and using it for convenience.
                    q2 = self.node.subcomponents['ebit-mem'].mem_positions[1].get_qubit(remove=True, skip_noise=True)
                    q1, q2 = lower_level_fns.entangle_epr_bits(q1, q2)
                    # copy one of entangled bits from ebit-mem to qmemory and send the other one to one of the neighbours
                    neighbour_idx = self.node.neighbours.index(n)
                    self.node.qmemory.put(q1, neighbour_idx) # store one of the qbits in your actual memory.
                    neighbour_port = f"{self.node.name}<->{n}"
                    self.node.ports[neighbour_port].tx_output(q2) # send the other one to the neighbour
                    break

class SwapProtocol(NodeProtocol):
    def __init__(self, node, path):
        super().__init__(node)
        self.path = path
        self._src_node = path[0]
        self._dst_node = path[-1]
        self._src_side_neighbour = self.path[self.path.index(self.node.name) - 1]
        self._dst_side_neighbour = self.path[self.path.index(self.node.name) + 1]
        self._src_side_mem_pos = self.node.neighbours.index(self._src_side_neighbour)
        self._dst_side_mem_pos = self.node.neighbours.index(self._dst_side_neighbour)
        self.is_first_node_in_path = (self.path.index(self.node.name) == 1)
        self.cport_src_side_neighbor = f"(internet) {self.node.name}<->{self._src_side_neighbour}"
        self.cport_dst_side_neighbor = f"(internet) {self.node.name}<->{self._dst_side_neighbour}"

    def run(self):
        if not self.is_first_node_in_path: # if first in path then dont wait for measurements from you neighbour on src side (since there is no repeater neighbour that way (only source)).
            while True:
                src_side_port = self.node.ports[self.cport_src_side_neighbor]
                wait_for_src_side_msg = self.await_port_input(src_side_port)
                yield (wait_for_src_side_msg) # wait until you receive a classical message from src-side neightbour
                # epr pair swapping:
                msg = self.node.ports[self.cport_src_side_neighbor].rx_input()
                m1 = msg.items[0]
                m2 = msg.items[1]
                src_side_shared_eprbit = self.node.qmemory.mem_positions[self._src_side_mem_pos].get_qubit(remove=True, skip_noise=True)
                swapped_qbit = lower_level_fns.correction(m1, m2, src_side_shared_eprbit)
                # self.node.qmemory.put(qubits=[swapped_qbit], positions=self._src_side_mem_pos)
                
                # src_side_shared_eprbit = self.node.qmemory.mem_positions[self._src_side_mem_pos].get_qubit(remove=True, skip_noise=True)
                src_side_shared_eprbit = swapped_qbit
                dst_side_shared_eprbit = self.node.qmemory.mem_positions[self._dst_side_mem_pos].get_qubit(remove=True, skip_noise=True)
                m1, m2 = lower_level_fns.bell_state_measurement(src_side_shared_eprbit, dst_side_shared_eprbit)
                # send m1,m2 to dst-side neighbour:
                msg = ns.components.component.Message([m1, m2])
                self.node.ports[self.cport_dst_side_neighbor].tx_output(msg)
        else:
            # case for first-in-line repeater node:
            src_side_shared_eprbit = self.node.qmemory.mem_positions[self._src_side_mem_pos].get_qubit(remove=True, skip_noise=True)
            dst_side_shared_eprbit = self.node.qmemory.mem_positions[self._dst_side_mem_pos].get_qubit(remove=True, skip_noise=True)
            m1, m2 = lower_level_fns.bell_state_measurement(src_side_shared_eprbit, dst_side_shared_eprbit)
            # send m1,m2 to dst-side neighbour:
            msg = ns.components.component.Message([m1, m2])
            self.node.ports[self.cport_dst_side_neighbor].tx_output(msg)

class SrcProtocol(NodeProtocol):
    def __init__(self, node, dst_node_name, first_repeater_neighbor_name, qubit_to_send) -> None:
        super().__init__(node)
        self.qubit_to_send = qubit_to_send
        self.dst_cport_name = f"(internet) {self.node.name}<->{dst_node_name}"
        self.first_repeater_node_mem_pos = self.node.neighbours.index(first_repeater_neighbor_name)
    
    def run(self) -> None:
        qbit_to_send = self.qubit_to_send
        shared_eprbit = self.node.qmemory.mem_positions[self.first_repeater_node_mem_pos].get_qubit(remove=True, skip_noise=True)
        m1, m2 = lower_level_fns.bell_state_measurement(qbit_to_send, shared_eprbit)
        msg = ns.components.component.Message([m1, m2])
        self.node.ports[self.dst_cport_name].tx_output(msg)

class DstProtocol(NodeProtocol):
    def __init__(self, node, src_node_name, last_repeater_neighbor_name) -> None:
        super().__init__(node)
        self.src_cport_name = f"(internet) {self.node.name}<->{src_node_name}"
        self.last_repeater_node_mem_pos = self.node.neighbours.index(last_repeater_neighbor_name)
    
    def run(self) -> None:
        while True:
            src_port = self.node.ports[self.src_cport_name]
            wait_for_src_msg = self.await_port_input(src_port)
            yield (wait_for_src_msg) # wait until you receive a classical message from the source node

            msg = src_port.rx_input()
            m1 = msg.items[0]
            m2 = msg.items[1]            

            shared_eprbit = self.node.qmemory.mem_positions[self.last_repeater_node_mem_pos].get_qubit(remove=True, skip_noise=True)
            teleported_qubit = lower_level_fns.correction(m1, m2, shared_eprbit)

            # tmp_qubit_teleported_info = []
            # tmp_qubit_teleported_info.append("Destination node received the following qbit:")
            # # tmp_qubit_teleported_info.append(teleported_qubit.qstate.qrepr)
            # tmp_qubit_teleported_info.append(ns.qubits.reduced_dm([teleported_qubit]))
            # tmp_qubit_teleported_info.append(teleported_qubit)

            fidelity = ns.qubits.fidelity(teleported_qubit, ns.y0, squared=True)
            print('fidelity:', fidelity)

            break

def main() -> None:
    # creating a 4x4 grid like Non-oblivious local / SLMP paper:
    # network looks like: (including names) (connections are bidirectional and quantum)
    # all nodes can talk to any other classically through the internet
    # n1  ---  n2   ---  n3  ---  n4 (dst)
    #  |        |        |        |
    # n5  ---  n6   ---  n7  ---  n8
    #  |        |        |        |
    # n9  - n10 (src) - n11 ---  n12
    #  |        |        |        |
    # n13 ---  n14  ---  n15 ---  n16
    
    # manually defining the network for now:
    network_graph_grid = {
        'n1': ['n2', 'n5'],
        'n2': ['n1', 'n3', 'n6'],
        'n3': ['n2', 'n7', 'n4'],
        'n4': ['n3', 'n8'],

        'n5': ['n1', 'n6', 'n9'],
        'n6': ['n5', 'n2', 'n7', 'n10'],
        'n7': ['n6', 'n3', 'n8', 'n11'],
        'n8': ['n7', 'n4', 'n12'],

        'n9': ['n5', 'n10', 'n13'],
        'n10': ['n9', 'n6', 'n11', 'n14'],
        'n11': ['n10', 'n7', 'n12', 'n15'],
        'n12': ['n11', 'n8', 'n16'],

        'n13': ['n9', 'n14'],
        'n14': ['n13', 'n10', 'n15'],
        'n15': ['n14', 'n11', 'n16'],
        'n16': ['n15', 'n12'],
    }
    
    data_ebits_per_timeslot = []
    total_timeslots = 10
    q = 1
    # x = no. of hops
    # x = 2
    # x = 4
    x = 6

    if x == 2:
        src_node_name = 'n7'
        dst_node_name = 'n4'
    elif x == 4:
        src_node_name = 'n10'
        dst_node_name = 'n4'
    elif x == 6:
        src_node_name = 'n13'
        dst_node_name = 'n4'

    
    for timeslot in range(total_timeslots):
        print(f"timeslot {timeslot+1} out of {total_timeslots}")
        ns.sim_reset()
        
        network = Network(network_graph_grid)

        # qubits = ns.qubits.create_qubits(1)
        # alice_protocol = MyProtocol(network.nodes['n10'], qubit=qubits[0])
        # n11_protocol = MyProtocol(network.nodes['n11'], qubit=qubits[0])

        # alice_protocol.start()
        # n11_protocol.start()
        # run_stats = ns.sim_run(duration=300)
        # print(run_stats)

        print('Start of external phase protocols')
        external_phase = []
        for n in network.nodes_names:
            external_phase.append(ExternalPhase(network.nodes[n]))
        for ep in external_phase:
            ep.start()
        run_stats = ns.sim_run()
        # print(run_stats)
        print('End of external phase protocols')

        network.draw_nx_graph()
        # internal phase:
        # ns.sim_reset()
        print('Start of swapping protocols / internal phase (partial)')
        
        shortest_paths = network.shortest_src_dst_paths(src = src_node_name, dst = dst_node_name, net_graph=network.ext_phase_subgraph())
        if shortest_paths == []:
            print('no e2e paths possible in this timeslot. End of protocols for this timeslot')
            data_ebits_per_timeslot.append(0)
        else:
            swap_protocols = []
            p_count = -1
            for p in shortest_paths:
                p_count += 1
                nodes_on_path = p[1:-1] # excluding src and dst as they do not perform swapping
                swap_protocols.append([])
                for n in nodes_on_path:
                    swap_protocols[p_count].append(SwapProtocol(network.nodes[n], p))    
                for sp in swap_protocols[p_count]:
                    sp.start()
            run_stats = ns.sim_run()
            # print(run_stats)
            print('End of swapping protocols')
            
            data_ebits_per_timeslot.append(len(shortest_paths))

            print('Start of teleportation protocols')
            for p in range(len(shortest_paths)):
                print(f'teleporation on path # {p+1} out of {len(shortest_paths)}')
                rs = []
                swap_nodes = shortest_paths[p][1:-1]
                for _ in range(len(swap_nodes)):
                    rs.append(random.random())
                proceed = True
                for r in rs:
                    if r > q:
                        # internal link failure
                        proceed = False
                        data_ebits_per_timeslot[-1] = 0
                
                if proceed:
                    # qbit_to_send = create_qubits(1, no_state=True)[0]
                    # state_assigned = assign_qstate(qubits=[qbit_to_send], qrepr=np.array([0.5, 0.5]))
                    qbit_to_send = create_qubits(1)[0]
                    qbit_to_send = lower_level_fns.temp_assign_state(qbit_to_send)
                    src_protocol = SrcProtocol(network.nodes[src_node_name], dst_node_name, shortest_paths[p][1], qbit_to_send)
                    dst_protocol = DstProtocol(network.nodes[dst_node_name], src_node_name, shortest_paths[p][-2])
                    src_protocol.start()
                    dst_protocol.start()
                    run_stats = ns.sim_run()
                    # print(run_stats)

                    # print()
                    # print(tmp_qubit_teleported_info[0])
                    # print(tmp_qubit_teleported_info[1])
                    
                    # print('\nshould be:')
                    # # print(state_assigned.qrepr)
                    # print(ns.qubits.reduced_dm([qbit_to_send]))

                    # fidelity = ns.qubits.fidelity(tmp_qubit_teleported_info[2], ns.y0, squared=True)
                    # print('fidelity:', fidelity)
                else:
                    print('internal link failure')

            print('End of teleportation protocols')

    print()
    for i in range(total_timeslots):
        # print(f'ts = {i+1}, ebits = {data_ebits_per_timeslot[i]}')
        print(f'{data_ebits_per_timeslot[i]}')
    halt = '' # temporary line to use as a breakpoint during debugging.

if __name__ == '__main__':
    main()