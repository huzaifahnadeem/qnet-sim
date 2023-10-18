#!/usr/bin/env python


import netsquid as ns

ns.util.simtools.set_random_state(seed=0)

class Network():
    def __init__(self, nodes, connections) -> None:
        self.nodes = nodes
        self.connections = connections

def setup_network(network_graph, node_distance=4e-3, depolar_rate=1e7, source_frequency=2e7):
    nodes_names = network_graph.keys()

    # create nodes:
    nodes = {}
    num_of_qubits_per_memory = 4 # like slmp, 4 qubits per node.
    for node_name in nodes_names:
        nodes[node_name] = ns.nodes.Node(name=node_name)
        
        # choosing values below (and in params) such as source frequency and delay model from the 'Nodes and Connections' tutorial on netsquid's website
        
        # add a quantum memory to the node:
        noise_model = ns.components.models.DepolarNoiseModel(depolar_rate=depolar_rate) # a noise model dictates how the stored qubit decohere in the memory over
        this_memory = ns.components.QuantumMemory(f"{node_name}-memory", num_positions=num_of_qubits_per_memory, memory_noise_models=[noise_model] * num_of_qubits_per_memory)
        nodes[node_name].add_subcomponent(this_memory, name="memory")

        # adding to each node a quantum source so that it can act as a repeater node:
        timing_model = ns.components.models.FixedDelayModel(delay=(1e9 / source_frequency))
        # TODO for now, creating two qsources because i cant figure out how to make one with four ports instead of two. So for now, qsource_h will server horizontal edges and qsource_v will server verticle edges for this node.
        this_qsource_h = ns.components.qsource.QSource(
                        "qsource_h", 
                        ns.qubits.StateSampler([ns.qubits.ketstates.b00], [1.0]), 
                        num_ports=2,
                        timing_model=timing_model,
                        status=ns.components.qsource.SourceStatus.INTERNAL
                    )
        this_qsource_v = ns.components.qsource.QSource(
                        "qsource_v", 
                        ns.qubits.StateSampler([ns.qubits.ketstates.b00], [1.0]), 
                        num_ports=2,
                        timing_model=timing_model,
                        status=ns.components.qsource.SourceStatus.INTERNAL
                    )
        nodes[node_name].add_subcomponent(this_qsource_h)
        nodes[node_name].add_subcomponent(this_qsource_v)

    # connections:
    # a connection is an edge in the graph. a connection is a collection of channels.
    # for this network, a connection includes two classical channels (one for each way) and two quantum channels (one for each way)
    # using built-in optic fibre classical delay and quantum loss models for the connection/channels

    connections = []
    done = [] # storing (u, v) pairs here for which i have created a two way connection including both classical and qchannel
    for u_name in network_graph.keys():
        for v_name in network_graph[u_name]:
            if ((u_name, v_name) not in done) and ((v_name, u_name) not in done):
                # the objects for node u and node v:
                u = nodes[u_name]
                v = nodes[v_name]

                # using mostly default values:
                # params_length = 10
                params_length = node_distance / 2
                params_p_loss_init = 0.83
                params_p_loss_length = 0.2

                # need add a port to both u and v for each of their edges. so for this edge:
                u.add_ports([f"<-{v_name}", f"->{v_name}"]) # [from_v, to_v]
                v.add_ports([f"<-{u_name}", f"->{u_name}"]) # [from_u, to_u]

                # make the connection:
                connection = ns.nodes.connections.Connection(f"{u_name}<==>{v_name} (connection)")
                
                # a connection has two ports by default 'A' and 'B', but we need four ports:
                connection.add_ports(['A-in', 'A-out', 'B-in', 'B-out'])

                # connect node u and v's ports to the connection:
                # connect the port with one of of the channel's ends. e.g:
                u.ports[f"<-{v_name}"].connect(connection.ports['A-out'])
                u.ports[f"->{v_name}"].connect(connection.ports['A-in'])
                v.ports[f"<-{u_name}"].connect(connection.ports['B-out'])
                v.ports[f"->{u_name}"].connect(connection.ports['B-in'])

                c_delay_model = ns.components.models.delaymodels.FibreDelayModel()
                cchannel_uv = ns.components.cchannel.ClassicalChannel(f"{u_name}-->{v_name} (c)", length=params_length, models={'delay_model': c_delay_model})
                cchannel_vu = ns.components.cchannel.ClassicalChannel(f"{u_name}<--{v_name} (c)", length=params_length, models={'delay_model': c_delay_model})

                q_loss_model = ns.components.models.qerrormodels.FibreLossModel(p_loss_init=params_p_loss_init, p_loss_length=params_p_loss_length)
                qchannel_uv = ns.components.qchannel.QuantumChannel(f"{u_name}-->{v_name} (q)", length=params_length, models={'quantum_loss_model': q_loss_model})
                qchannel_vu = ns.components.qchannel.QuantumChannel(f"{u_name}<--{v_name} (q)", length=params_length, models={'quantum_loss_model': q_loss_model})

                connection.add_subcomponent(cchannel_uv,
                                            forward_input=[('A-in', "send")],  # u's port 'to_v'   / ->v
                                            forward_output=[('B-out', "recv")]) # v's port 'from_u' / <-u
                connection.add_subcomponent(cchannel_vu,
                                            forward_input=[('B-in', "send")],  # v's port 'to_u'   / ->u
                                            forward_output=[('A-out', "recv")]) # u's port 'from_v' / <-v

                connection.add_subcomponent(qchannel_uv,
                                            forward_input=[('A-in', "send")],  # u's port 'to_v'   / ->v
                                            forward_output=[('B-out', "recv")]) # v's port 'from_u' / <-u
                connection.add_subcomponent(qchannel_vu,
                                            forward_input=[('B-in', "send")],  # v's port 'to_u'   / ->u
                                            forward_output=[('A-out', "recv")]) # u's port 'from_v' / <-v

                connections.append(connection)
                done.append((u_name, v_name))
                done.append((v_name, u_name))
    
    # connect qsources' ports to their respective nodes' channels:
    for node_name in nodes.keys():
        node = nodes[node_name]
        # since for now we have two qsource per node (one for horiztal edges, one for verticle). TODO change this once you figure out how to make a qsource with 4 ports
        qsource_h = node.subcomponents['qsource_h']
        qsource_v = node.subcomponents['qsource_v']

        v_edges = []
        h_edges = []

        for port_name in list(node.ports):
            if port_name[:2] != '->':
                continue
            else:
                # ideally, here i would know which edges are horizontal and which ones are verticle and forward input accordingly, but for now, just connecting the first two edges to qsource_h and the other two (or one) to qsource_h
                edge_num = 0
                total_edges = len(list(node.ports))//2
                for _ in range(total_edges):
                    edge_num += 1
                    if edge_num in [1,2]:
                        node.ports[port_name].forward_input(qsource_h.ports["qout0"])
                        node.ports[port_name].forward_input(qsource_h.ports["qout1"])
                    else:
                        node.ports[port_name].forward_input(qsource_v.ports["qout0"])
                        node.ports[port_name].forward_input(qsource_v.ports["qout1"])
        
    t2= 0

    return nodes, connections

def external_phase(this_node):
    for i in range(this_node.qmemory.unused_positions): # should run for all memory positions since this is at the start of a time slot
        qubit, = ns.qubits.qubitapi.create_qubits(num_qubits=1) # create a qubit
        mem_pos = this_node.qmemory.unused_positions[i]
        this_node.qmemory.put(qubit, mem_pos)

class AliceProtocol(ns.protocols.NodeProtocol): # qubit's source node
    def run(self):
        print("Starting Alice's protocol (src) ...")
        # External Phase:
        # TODO
        # Internal Phase:
        # port = self.node.ports["port_to_channel"] # TODO. port name correction
        # qubit, = ns.qubits.qubitapi.create_qubits(num_qubits=1) # create a random qubit
        # port.tx_output(qubit)  # Send qubit to a neighbour. TODO: which neighbour

class BobProtocol(ns.protocols.NodeProtocol): # qubit's destination node
    def run(self):
        print("Starting Bobs's protocol (dst) ...")
        # External Phase:
        # TODO
        # Internal Phase:

class RepeaterNodeProtocol(ns.protocols.NodeProtocol): # all other nodes
    def run(self):
        print(f"Starting {self.node.name}'s protocol ...")
        # External Phase:
        # TODO
        # Internal Phase:

def main():
    # creating a 4x4 grid like Non-oblivious local / SLMP paper:
    # network looks like: (including names):
    # n1  ---  n2   ---  n3  ---  bob
    #  |        |        |        |
    # n5  ---  n6   ---  n7  ---  n8
    #  |        |        |        |
    # n9  --- alice ---  n11 ---  n12
    #  |        |        |        |
    # n13 ---  n14  ---  n15 ---  n16
    
    # manually defining the network for now:
    network_graph = {
        'n1': ['n2', 'n5'],
        'n2': ['n1', 'n3', 'n6'],
        'n3': ['n2', 'n7', 'bob'],
        'bob': ['n3', 'n8'],

        'n5': ['n1', 'n6', 'n9'],
        'n6': ['n5', 'n2', 'n7', 'alice'],
        'n7': ['n6', 'n3', 'n8', 'n11'],
        'n8': ['n7', 'bob', 'n12'],

        'n9': ['n5', 'alice', 'n13'],
        'alice': ['n9', 'n6', 'n11', 'n14'],
        'n11': ['alice', 'n7', 'n12', 'n15'],
        'n12': ['n11', 'n8', 'n16'],

        'n13': ['n9', 'n14'],
        'n14': ['n13', 'alice', 'n15'],
        'n15': ['n14', 'n11', 'n16'],
        'n16': ['n15', 'n12'],
    }
    _nodes, _connections = setup_network(network_graph)
    network = Network(_nodes, _connections)
    alice_protocol = AliceProtocol(network.nodes['alice'])
    bob_protocol = BobProtocol(network.nodes['bob'])

    halt = True # temporary line to use as a breakpoint during debugging.

if __name__ == '__main__':
    main()