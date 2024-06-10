'''
This file contains objects, classes, functions, etc associated with the network
'''
from netsquid.nodes import Network as ns_Network
from netsquid.nodes.node import Node as ns_Node
from netsquid.nodes.connections import DirectConnection
from netsquid.components import QuantumChannel, ClassicalChannel, QuantumMemory
import networkx as nx
# from netsquid.components import QuantumMemory
import netsquid as ns


import globals
from topologies import network_choice
from entities import NodeEntity
import quantum

class Node(ns_Node):
    def __init__(self, name, ID=None, qmemory=None, port_names=None, node_entity=None) -> None:
        super().__init__(name=name, ID=ID, qmemory=qmemory, port_names=port_names)
        self.entity = node_entity

class Network(ns_Network):
    def __init__(self, name=globals.args.network.value) -> None:
        # network_choice returns a full multigraph and a simplified graph (also of type multigraph)
        self.graph, self.graph_full = network_choice() # used for yen's algorithm and for visualizing the network situation (<- TODO this second part)
        self.nx_graph = self.graph # TODO: this is here temporarily so avoid any issues with references to the old var name "self.nx_graph". remove this when all references are changed to either self.graph_full or self.graph
        
        super().__init__(name=name)
        super().add_nodes(self._create_nodes())
        
        # Note the difference: 
        # paper vs here: channels (paper) = DirectConnection (here) (each of which has 2 channels internally). Edges (paper) = A collection of connections here.
        self._create_and_add_connections()
        
        # TODO: log at the end of init that network has been initialized? or maybe in main somewhere

    def node_names(self):
        return nx.nodes(self.graph)

    def _create_nodes(self):
        for node_name in self.node_names():
            # Assuming unique name. might require an ID field if that is not the case.
            degree = self.graph.degree[node_name]
            qubit_capacity = degree # By default go with qubit_capacity = degree of node just like SLMP paper. TODO: one should be able to define this in topology for QPASS and probably others
            this_node = Node(
                name = node_name,
                # ID = int(node_name[1:]), # not using ID. but might be good to have? currently assume unique names so dont need IDs.
                qmemory = QuantumMemory(name=f"{node_name}-qmem", num_positions=qubit_capacity, memory_noise_models=self._gen_q_mem_model()),
            )
            this_node.entity = NodeEntity(node_name, this_node)
            yield this_node
    
    def _create_and_add_connections(self) -> None:
        already_done = []
        for u in self.node_names():
            for _, v, edge_data in self.graph.edges(u, data=True):
                if ((u, v) not in already_done) and ((v, u) not in already_done):
                    self._gen_connection(u, v, edge_data['length'], edge_data['width'])
                already_done.append((u, v))
                already_done.append((v, u))
        
    def gen_label(self, u, v, of, num=0):
        # assume: u to v for channels. bidirectional for connection
        label = ''
        num = f'[{str(num)}]'
        
        # fixed naming order
        a = u
        b = v
        u = a if a > b else b
        v = b if u == a else a

        of_options = globals.CONN_CHANN_LABELS_FN_PARAM
        if of is of_options.CCHANNEL:
            label = f"{u}-->{v} | classical"
        elif of is of_options.CCONNECTION:
            label = f"{u}<==>{v} | classical"
        elif of is of_options.QCHANNEL:
            label = f"{u}-->{v} | quantum"
        elif of is of_options.QCONNECTION:
            label = f"{u}<={num}=>{v} | quantum"
        elif of is of_options.CONN_QMEM:
            q_conn_label = f"{u}<={num}=>{v} | quantum"
            label = f'{q_conn_label} | qmem'
        
        return label
    
    def _gen_connection(self, u_name, v_name, length, width):
        label_options = globals.CONN_CHANN_LABELS_FN_PARAM
        network = super()
        u = network.get_node(u_name)
        v = network.get_node(v_name)
        
        c_channel_model = self._gen_c_channel_model()
        c_conn_label = self.gen_label(u_name, v_name, of=label_options.CCONNECTION)
        c_conn = DirectConnection(
                name = c_conn_label,
                channel_AtoB = ClassicalChannel(
                                name = self.gen_label(u_name, v_name, of=label_options.CCHANNEL),
                                length=length,
                                models=c_channel_model,
                            ),
                channel_BtoA = ClassicalChannel(
                                name = self.gen_label(v_name, u_name, of=label_options.CCHANNEL),
                                length=length,
                                models=c_channel_model,
                            ),
            )
        local_port_name, remote_port_name = network.add_connection(u, v, c_conn, label=c_conn_label)

        u.ports[local_port_name].bind_input_handler(
                            # lambda m: print(f"{u_name} received message: {m}!")
                            self._message_recv_handler
                        )
        v.ports[remote_port_name].bind_input_handler(
                            # lambda m: print(f"{v_name} received message: {m}!")
                            self._message_recv_handler
                        )
        
        for channel_num in range(width):
            q_conn_label = self.gen_label(u_name, v_name, of=label_options.QCONNECTION, num=channel_num)
            qmem_name = self.gen_label(u_name, v_name, of=label_options.CONN_QMEM, num=channel_num)
            u.add_subcomponent(QuantumMemory(qmem_name, num_positions=1, memory_noise_models=self._gen_q_mem_model()))
            v.add_subcomponent(QuantumMemory(qmem_name, num_positions=1, memory_noise_models=self._gen_q_mem_model()))
            
            q_channel_model = self._gen_q_channel_model()
            
            q_conn = DirectConnection(
                    name = q_conn_label,
                    channel_AtoB = QuantumChannel(
                                    name = self.gen_label(u_name, v_name, of=label_options.QCHANNEL),
                                    length=length, # in km
                                    models=q_channel_model, 
                                ),
                    channel_BtoA = QuantumChannel(
                                    name = self.gen_label(v_name, u_name, of=label_options.QCHANNEL),
                                    length=length, # in km
                                    models=q_channel_model,
                                ),
                )
            local_port_name, remote_port_name = network.add_connection(u, v, q_conn, label=q_conn_label)
            
            u.ports[local_port_name].bind_input_handler(
                                # lambda m: print(f"{u_name} received a qubit: {m}!")
                                self._qubit_recv_handler
                            )
            v.ports[remote_port_name].bind_input_handler(
                                # lambda m: print(f"{v_name} received a qubit: {m}!")
                                self._qubit_recv_handler
                            )
    
    def _send(self, u_name, v_name, packet, is_qubit=False, channel_num=0) -> None:
        label_options = globals.CONN_CHANN_LABELS_FN_PARAM
        network = super()
        u = network.get_node(u_name)
        v = network.get_node(v_name)
        of = label_options.QCONNECTION if is_qubit else label_options.CCONNECTION
        conn_label = self.gen_label(u_name, v_name, of, num=channel_num)
        conn = network.get_connection(u, v, label=conn_label)
        channel = conn.channel_AtoB
        header = (u_name, v_name, channel_num) # tuple: (source, dst, channelnum)
        channel.send(packet, header=header)
    
    def send_message(self, u_name, v_name, message) -> None:
        self._send(u_name, v_name, packet=message)
    
    def send_qubit(self, u_name, v_name, qubit, channel_num=0) -> None:
        self._send(u_name, v_name, packet=qubit, is_qubit=True, channel_num=channel_num)

    def _message_recv_handler(self, m):
        # print(f'rcv msg:{m}')
        for i in range(len(m.items)): # there can be more than 1 message packet in queue (if received >1 before reading and clearing message queue (happens internally -- i dont touch that part))
            msg_packet = m.items[i]
            if msg_packet == {}:
                # then it means the packet was lost over the channel
                continue
            header = {}

            header['src'] = m.meta['header'][0]
            header['dst'] = m.meta['header'][1]
            header['channel_num'] = m.meta['header'][2]
            network = super()
            this_node_name = header['dst']
            KEYS = globals.MSG_KEYS
            this_entity: NodeEntity = network.get_node(this_node_name).entity
            if msg_packet[KEYS.DST] == this_node_name: # if the message packet is meant for me, process
                MSG_TYPE = globals.MSG_TYPE
                if msg_packet[KEYS.TYPE] is MSG_TYPE.ebit_sent:
                    this_entity._rcv_ebit(msg_packet[KEYS.SRC], msg_packet[KEYS.CONN_NUM])
                elif msg_packet[KEYS.TYPE] is MSG_TYPE.ebit_received:
                    this_entity.add_to_link_state(ebit_from=msg_packet[KEYS.DST], ebit_to=msg_packet[KEYS.SRC], on_channel_num=msg_packet[KEYS.CONN_NUM], received_successfully=msg_packet[KEYS.EBIT_RECV_SUCCESS])
                elif msg_packet[KEYS.TYPE] is MSG_TYPE.link_state:
                    this_entity.process_link_state_packet(header['src'], msg_packet)
                elif msg_packet[KEYS.TYPE] is MSG_TYPE.corrections:
                    this_entity._store_corrections(msg_packet)
                elif msg_packet[KEYS.TYPE] is MSG_TYPE.e2e_ready:
                    this_entity._teleport_qubit(msg_packet[KEYS.SERVING_PAIR], msg_packet[KEYS.PATH])
            else: # if message not meant for you. send to next neighbour onward to the destination
                this_entity.send_message(msg_packet[KEYS.DST], msg_packet, send_directly=False)

    def _qubit_recv_handler(self, q):
        # print(f'rcv qbit:{q}')
        qubit = q.items[0]
        header = {}
        header['src'] = q.meta['header'][0]
        header['dst'] = q.meta['header'][1]
        header['channel_num'] = q.meta['header'][2]
        
        qmem_label = self.gen_label(header['src'], header['dst'], of=globals.CONN_CHANN_LABELS_FN_PARAM.CONN_QMEM, num=header['channel_num'])
        network = super()
        this_node = network.get_node(header['dst'])
        this_conn_qmem = this_node.subcomponents[qmem_label]
        this_conn_qmem.put(qubit)
    
    def _gen_q_channel_model(self):
        q_channel_model = {}

        key_quantum_noise_model = globals.QCHANNEL_MODEL_TYPES.quantum_noise_model.name
        key_quantum_loss_model = globals.QCHANNEL_MODEL_TYPES.quantum_loss_model.name
        key_delay_model = globals.QCHANNEL_MODEL_TYPES.delay_model.name
        
        LOSS_MODELS = globals.QCHANNEL_LOSS_MODEL
        NOISE_MODELS = globals.QCHANNEL_NOISE_MODEL
        DELAY_MODELS = globals.CHANNEL_DELAY_MODEL

        if (globals.args.qc_noise_model is NOISE_MODELS.none) and (globals.args.qc_loss_model is LOSS_MODELS.none) and (globals.args.qc_delay_model is DELAY_MODELS.none):
            q_channel_model = None
        else:
            # setting the noise model first:
            if globals.args.qc_noise_model is NOISE_MODELS.none:
                q_channel_model[key_quantum_noise_model] = None
            elif globals.args.qc_noise_model is NOISE_MODELS.dephase:
                q_channel_model[key_quantum_noise_model] = ns.components.models.qerrormodels.DephaseNoiseModel(dephase_rate=globals.args.qc_noise_rate, time_independent=globals.args.qc_noise_time_independent)
            elif globals.args.qc_noise_model is NOISE_MODELS.depolar:
                q_channel_model[key_quantum_noise_model] = ns.components.models.qerrormodels.DepolarNoiseModel(depolar_rate=globals.args.qc_noise_rate, time_independent=globals.args.qc_noise_time_independent)
            elif globals.args.qc_noise_model is NOISE_MODELS.t1t2:
                q_channel_model[key_quantum_noise_model] = ns.components.models.qerrormodels.T1T2NoiseModel(T1=globals.args.qc_noise_t1, T2=globals.args.qc_noise_t2)
            
            # setting the loss model:
            if globals.args.qc_loss_model is LOSS_MODELS.none:
                q_channel_model[key_quantum_loss_model] = None
            elif globals.args.qc_loss_model is LOSS_MODELS.fibre:
                q_channel_model[key_quantum_loss_model] = ns.components.models.qerrormodels.FibreLossModel(p_loss_init=globals.args.qc_p_loss_init, p_loss_length=globals.args.qc_p_loss_length)
            elif globals.args.qc_loss_model is LOSS_MODELS.fixed:
                q_channel_model[key_quantum_loss_model] = quantum.FixedProbabilityLoss(p_prob=globals.args.qc_p_loss_init, p_loss_length=globals.args.qc_p_loss_length)

            # setting the delay model:
            if globals.args.qc_delay_model is DELAY_MODELS.none:
                q_channel_model[key_delay_model] = None
            elif globals.args.qc_delay_model is DELAY_MODELS.fibre:
                q_channel_model[key_delay_model] = ns.components.models.delaymodels.FibreDelayModel(c=globals.args.qc_delay_photon_speed)
            elif globals.args.qc_delay_model is DELAY_MODELS.fixed:
                q_channel_model[key_delay_model] = ns.components.models.delaymodels.FixedDelayModel(delay=globals.args.qc_delay_fixed)
            elif globals.args.qc_delay_model is DELAY_MODELS.gaussian:
                q_channel_model[key_delay_model] = ns.components.models.delaymodels.GaussianDelayModel(delay_mean=globals.args.qc_delay_mean, delay_std=globals.args.qc_delay_std)

        return q_channel_model
    
    def _gen_c_channel_model(self):
        # Note: Netsquid only provides delay models for classical channels. It provides a base class for loss models but no ready-made loss model.
        # Note 2: I figured that values in microsec would be more convenient so arg values are converted into ns since netsquid model params assume nano sec.
        
        ms_to_ns_factor = 1000 # to convert ms to ns, multiple the ms value by 1000.
        c_channel_model = {}
        key_delay_model = globals.QCHANNEL_MODEL_TYPES.delay_model.name
        key_classical_loss_model = globals.CCHANNEL_MODEL_TYPES.classical_loss_model.name
        DELAY_MODELS = globals.CHANNEL_DELAY_MODEL
        LOSS_MODELS = globals.CCHANNEL_LOSS_MODEL

        if (globals.args.cc_loss_model is LOSS_MODELS.none) and (globals.args.cc_delay_model is DELAY_MODELS.none):
            c_channel_model = None
        else:
            # setting the delay model:
            if globals.args.cc_delay_model is DELAY_MODELS.none:
                c_channel_model[key_delay_model] = None
            elif globals.args.cc_delay_model is DELAY_MODELS.fibre:
                c_channel_model[key_delay_model] = ns.components.models.delaymodels.FibreDelayModel(c=globals.args.cc_delay_photon_speed)
            elif globals.args.cc_delay_model is DELAY_MODELS.fixed:
                c_channel_model[key_delay_model] = ns.components.models.delaymodels.FixedDelayModel(delay = globals.args.cc_delay_fixed * ms_to_ns_factor)
            elif globals.args.cc_delay_model is DELAY_MODELS.gaussian:
                c_channel_model[key_delay_model] = ns.components.models.delaymodels.GaussianDelayModel(delay_mean = globals.args.cc_delay_mean * ms_to_ns_factor, delay_std = globals.args.cc_delay_std * ms_to_ns_factor)

            # setting the loss model:
            if globals.args.cc_loss_model is LOSS_MODELS.none:
                c_channel_model[key_classical_loss_model] = None
            elif globals.args.cc_loss_model is LOSS_MODELS.prob:
                c_channel_model[key_classical_loss_model] = quantum.CChannelProbLoss(prob=globals.args.cc_loss_prob)

        return c_channel_model
    
    def _gen_q_mem_model(self):
        q_mem_model = None

        NOISE_MODELS = globals.QMEM_NOISE_MODEL

        if globals.args.qm_noise_model is NOISE_MODELS.none:
            q_mem_model = None
        elif globals.args.qm_noise_model is NOISE_MODELS.dephase:
            q_mem_model = ns.components.models.qerrormodels.DephaseNoiseModel(dephase_rate=globals.args.qm_noise_rate, time_independent=globals.args.qm_noise_time_independent)
        elif globals.args.qm_noise_model is NOISE_MODELS.depolar:
            q_mem_model = ns.components.models.qerrormodels.DepolarNoiseModel(depolar_rate=globals.args.qm_noise_rate, time_independent=globals.args.qm_noise_time_independent)

        return q_mem_model