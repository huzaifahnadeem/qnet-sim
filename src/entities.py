'''
This file is supposed to contain classes for the entities in the network which includes: the network nodes, and the network information server.
'''

import pydynaa
from src import globals
import random 
import networkx as nx
import netsquid as ns
import copy
# from functools import reduce
from src import quantum
from math import sqrt
from src import utils
from src import data_collector
from src import traffic_matrix
from .RoutingAlgorithms import slmp_global, slmp_local, qpass, qcast

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.network import Node, Network

# TODO Probably a good idea to use protocol class for the algorithms maybe

class K_Hop_Neighbour_Node:
    # this class, i think, should be in network.py but that causes some circular import issue. So, putting it here for now.
    def __init__(self, name, entity, path_to, k_hop) -> None:
        self.name = name
        self.entity = entity
        self.path_to = path_to
        self.k_hop = k_hop

class NodeEntity(pydynaa.Entity):
    p1_done_evtype = pydynaa.EventType("P1_DONE", "Phase 1 done.")
    p2_done_evtype = pydynaa.EventType("P2_DONE", "Phase 2 done.")
    p3_done_evtype = pydynaa.EventType("P3_DONE", "Phase 3 done.")
    p4_done_evtype = pydynaa.EventType("P4_DONE", "Phase 4 done.")
    e2e_ready_evtype = pydynaa.EventType("E2E EBIT READY", "E2E ebit is ready. can teleport now")
    
    def __init__(self, name, node):
        self.name: str = name
        self.node: 'Node' = node
        self.network: 'Network' = None
        self.nis: NIS = None
        self.curr_ts: int = None
        self.sd_pairs = []
        self.curr_role = None
        self.k_hop_neighbours = [] # nodes that are <= k hops away
        self.imm_neighbours = [] # immediate neighbours (share an edge)
        self.connections = {}
        self.events_msg_passing = {} # for passing parameters etc between a function and the handler function if needed (for the same entity not across)
        '''self.swapped_nodes = [] # to keep track in SLMP local'''
        '''self.e2e_paths_sofar = [] # for slmp local'''

    def start(self):
        self._setup()
        self._wait(
                event_type = NIS.new_ts_evtype,
                entity = self.nis,
                handler = pydynaa.EventHandler(self._new_ts),
            )

    def _setup(self):
        # this is to set up anything that could not be set up with the constructor (e.g. connections variable)
        self._set_connections()

    def _new_ts(self, _):
        self._cleanup()
        self.curr_ts = self.nis.curr_ts
        
        self._p1()

        # start P2 once P1 is done:
        self._wait_once(
            event_type = NodeEntity.p1_done_evtype,
            entity = self,
            handler = pydynaa.EventHandler(self._p2),
        )

        self._wait_once(
            event_type = NodeEntity.p2_done_evtype,
            entity = self,
            handler = pydynaa.EventHandler(self._p3),
        )

        self._wait_once(
            event_type = NodeEntity.p3_done_evtype,
            entity = self,
            handler = pydynaa.EventHandler(self._p4),
        )

    def _cleanup(self):
        # This is to clear up any variable states at the start of a new timeslot
        self.node.qmemory.discard(self.node.qmemory.used_positions, check_positions=False) # discard all qubits in memory from previous ts
        self.curr_qubit_channel_assignment = {} # reset qubit-channel assignments
        self.major_paths = None
        self.link_state = {}
        self.neighbours_link_state = {}
        self.events_msg_passing = {}
        self.swapped_nodes = []
        self.e2e_paths_sofar = []

    def set_nis_entity(self, nis):
        self.nis = nis

    def set_network(self, nw):
        self.network = nw
        
        if globals.args.alg is globals.ALGS.SLMPG:
            globals.args.p3_hop = float('inf')  # special case: the whole network knows the link state (aka global link state knowledge)

        self.k_hop_neighbours = self._find_k_hop_neighbours()
        self.imm_neighbours = [n for n in self.k_hop_neighbours if n.k_hop == 1]

        if globals.args.alg is globals.ALGS.SLMPL:
            # Doing this after k hop calculation because otherwise there would be no k hop or imm neighbours
            self.k_hop_neighbours = None        # not applicable to SLMPl since not going to be sharing link state with anyone

    def _find_k_hop_neighbours(self):
        k_hop_neighbours = []

        hop = globals.args.p3_hop
        ego_graph = nx.ego_graph(G=self.network.graph, n=self.name, radius=hop)
        k_neighbours = list(ego_graph.nodes())
        k_neighbours.remove(self.name) # as the above function works, the list would also include the node itself. So remove that.

        for k_name in k_neighbours:
            path = nx.shortest_path(ego_graph, source=self.name, target=k_name)
            this_k_neighbour = K_Hop_Neighbour_Node(name=k_name, entity=self.network.get_node(k_name).entity, path_to=path, k_hop=len(path)-1)
            k_hop_neighbours.append(this_k_neighbour)
            
        return k_hop_neighbours

    def _set_connections(self):
        self.connections = {}
        cconn_option = globals.CONN_CHANN_LABELS_FN_PARAM.CCONNECTION
        qconn_option = globals.CONN_CHANN_LABELS_FN_PARAM.QCONNECTION
        for n in self.imm_neighbours:
            self.connections[n.name] = []
            # one classical connection:
            clabel = self.network.gen_label(self.name, n.name, of=cconn_option)
            self.connections[n.name].append(self.network.get_connection(self.name, n.name, clabel))
            # 'w' quantum connections:
            for chan_num in range(self.network.graph[self.name][n.name]["width"]):
                qlabel = self.network.gen_label(self.name, n.name, of=qconn_option, num=chan_num)
                self.connections[n.name].append(self.network.get_connection(self.name, n.name, qlabel))

    def is_neighbour(self, node, imm_neighbour_only=True):
        neighbours = self.imm_neighbours
        if not imm_neighbour_only:
            neighbours = self.k_hop_neighbours
        
        is_a_neighbour = False if [n for n in neighbours if n.name == node] == [] else True
        return is_a_neighbour

    def send_message(self, v, message, send_directly=True):
        if send_directly:
            if self.is_neighbour(v):
                send_to = v
            else:
                raise ValueError(f"Node {v.name} is not an immediate neighbour of {self.name} so this message cannot be sent.")
        else:
            # find next hop on the shortest path and send it to that node.
            shortest_path = list(nx.shortest_path(self.network.graph, self.name, v))
            send_to = shortest_path[shortest_path.index(self.name) + 1]
        self.network.send_message(self.name, send_to, message)
        
    def send_qubit(self, v, qubit, channel_num=0):
        if self.is_neighbour(v):
            self.network.send_qubit(self.name, v, qubit, channel_num)
        else:
            raise ValueError(f"Node {v} is not an immediate neighbour of {self.name} so this qubit cannot be sent.")

    def _rcv_ebit(self, src_name, conn_num):
        this_event = pydynaa.EventType("EBIT_SENT", "...")
        # schedule an event after the interval of timeout. if qubit not present in the corresponding connection's qmem by then, then that means we did not receive that qubit.
        timeout = globals.args.link_establish_timeout
        self._schedule_after(timeout, this_event)
        # set up handler to receive this qubit.
        this_connection = self.connections[src_name][conn_num+1] # +1 since classical connectin is at index 0 then q conns in sequence
        def handler(_):
            # nonlocal this_connection
            nonlocal conn_num
            nonlocal self
            nonlocal src_name
            qmem_label = self.network.gen_label(src_name, self.name, of=globals.CONN_CHANN_LABELS_FN_PARAM.CONN_QMEM, num=conn_num)
            qmem = self.node.subcomponents[qmem_label]
            qubit_received = True if qmem.num_used_positions == 1 else False
            if (qubit_received) and (qmem._memory_positions[0]._qubit.qstate is None): # this check is required for when loss model = fixed is used for connections. (this is not a netsquid model, i overrode fibre model for this simpler loss model and probably didnt do a good job at it. but the way i have done it is that if the qubit is dropped then only its state is changed to None)
                qubit_received = False

            # update your link states
            self.add_to_link_state(src_name, self.name, conn_num, qubit_received)

            # let the neighbour know
            self.send_message(
                src_name, 
                message=self._gen_message_packet(
                    msg_type=globals.MSG_TYPE.ebit_received,
                    src_name=self.name,
                    dst_name=src_name, # dst is the source of qubit
                    conn_num=conn_num,
                    ebit_received_successfully=qubit_received
                    ),
                )
        
        self._wait_once(
            event_type = this_event,
            entity = self,
            handler = pydynaa.EventHandler(handler),
        )

    def _gen_message_packet(self, msg_type, src_name=None, dst_name=None, path=None, curr_ts=None, link_state=None, conn_num=None, ebit_received_successfully=None, corrections=None, data_qubit_state=None, serving_pair=None, corrections_via=None):
        # note that src_name, dst_name in the parameters is for the original sender and final receiver of the message packet. serving_pair param is to specify who the e2e src and dst nodes are for which this message is being sent (to anyone)
        KEYS = globals.MSG_KEYS
        MSG_TYPE = globals.MSG_TYPE
        msg_packet = {
            KEYS.TYPE: msg_type,
            KEYS.SRC: src_name,
            KEYS.DST: dst_name,
        }
        if msg_type is MSG_TYPE.ebit_sent:
            msg_packet[KEYS.CONN_NUM] = conn_num
        elif msg_type is MSG_TYPE.ebit_received:
            msg_packet[KEYS.CONN_NUM] = conn_num
            msg_packet[KEYS.EBIT_RECV_SUCCESS] = ebit_received_successfully
        elif msg_type is MSG_TYPE.link_state:
            msg_packet[KEYS.TS] = curr_ts
            msg_packet[KEYS.PATH] = path
            msg_packet[KEYS.LINK_STATE] = link_state
        elif msg_type is MSG_TYPE.corrections:
            if corrections_via is None:
                corrections_via = [self.name]
            msg_packet[KEYS.PATH] = path
            msg_packet[KEYS.SERVING_PAIR] = serving_pair
            msg_packet[KEYS.CORRECTIONS] = corrections
            msg_packet[KEYS.DATA_QUBIT_STATE] = data_qubit_state
            msg_packet[KEYS.CORRECTIONS_VIA] = corrections_via
        elif msg_type is MSG_TYPE.e2e_ready:
            msg_packet[KEYS.PATH] = path
            msg_packet[KEYS.SERVING_PAIR] = serving_pair
        
        return msg_packet

    def _gen_final_link_state(self):
        # go through link states. if both you and you neighbour successfully received each others ebit, then based on your algorithm figure out which one you are going to use and discard the other one.
        ls = self.link_state
        final_ls = []
        done = []
        for link in ls:
            if link in done:
                continue
            qb_src, qb_dst = link
            for chann_num in ls[link].keys():
                uv_status = ls[link][chann_num]
                if globals.args.two_sided_epr: # then check for the other side too
                    other_way = (qb_dst, qb_src)
                    vu_status = ls[other_way][chann_num]
                else:   # if single sided epr:
                    vu_status = False # since that node wasnt responsible for epr gen-share
                    
                if self.name == qb_src:
                    neighbour_received = uv_status
                    this_node_received = vu_status
                    neighbour_name = qb_dst
                else:
                    neighbour_received = vu_status
                    this_node_received = uv_status
                    neighbour_name = qb_src
                use_this_node_epr = self._use_this_node_epr(neighbour_name, neighbour_received, this_node_received)
                if use_this_node_epr == True:
                    final_ls.append((self.name, neighbour_name, chann_num))
                    # self.nis.epr_track_update(self.curr_ts, self.name, neighbour_name, 'used')
                elif use_this_node_epr == False:
                    final_ls.append((neighbour_name, self.name, chann_num))
                    # self.nis.epr_track_update(self.curr_ts, self.name, neighbour_name, 'unused (used other one)')
                done.append((qb_src, qb_dst))
                done.append((qb_dst, qb_src))
        self.link_state = {'final': final_ls}

    def add_to_link_state(self, ebit_from, ebit_to, on_channel_num, received_successfully):
        if (ebit_from, ebit_to) not in self.link_state.keys():
            self.link_state[(ebit_from, ebit_to)] = {}
        
        self.link_state[(ebit_from, ebit_to)][on_channel_num] = received_successfully

    def process_link_state_packet(self, recv_from, packet):
        # else forward it to the next node on path.
        KEYS = globals.MSG_KEYS
        if packet[KEYS.DST] == self.name: # if link state packet meant for you, save it:
            link_state = packet[KEYS.LINK_STATE]
            link_state_of = packet[KEYS.SRC]
            self.neighbours_link_state[link_state_of] = link_state
        else:
            # else forward it to the next node on path.
            next_on_path_idx = 1 + packet[KEYS.PATH].index(self.name) # 1 + (index of this node on the path)
            next_on_path_name =  packet[KEYS.PATH][next_on_path_idx]
            self.send_message(next_on_path_name, packet)

    def _establish_links(self):
        if globals.args.two_sided_epr not in [True, False]: # TODO: add a third option where the connection itself generates the epr pairs (like in netsquid tutorial/examples)
            raise NotImplementedError("connection-generated epr pairs not implemented yet")
        
        # TODO: implement nc functionality for QPASS
        # nc = globals.args.p2_nc
        for qubit_index in self.curr_qubit_channel_assignment.keys():
            to_node, channel_num = self.curr_qubit_channel_assignment[qubit_index]
            if not globals.args.two_sided_epr: # i.e. one sided epr generation (neighbour with the larger name responsible to generate the pair, in that case)
                if self._neighbour_responsible_for_ebit(neighbour_name=to_node):
                    pass # this node is responsible
                else:
                    continue # the other node is responsible
            q1, q2 = quantum.gen_epr_pair()
            self.nis.epr_track_add(self.curr_ts, self.name, to_node)
            self.node.qmemory.put(q1, positions=qubit_index)
            self.send_qubit(to_node, q2, channel_num)
            self.send_message(
                to_node, 
                message=self._gen_message_packet(
                        msg_type=globals.MSG_TYPE.ebit_sent,
                        src_name=self.name,
                        dst_name=to_node,
                        conn_num=channel_num,
                        ),
                )
               
    def _neighbour_responsible_for_ebit(self, neighbour_name):
        # bigger_id_node_name = neighbour_name if int(neighbour_name[1:]) > int(self.name[1:]) else self.name
        bigger_id_node_name = neighbour_name if neighbour_name > self.name else self.name
        if bigger_id_node_name == neighbour_name:
            return True
        return False

    def _use_this_node_epr(self, neighbour_name, neighbour_received, this_node_received):
        # returns: True if use this node's pair. False is neighbour's is to be used. Returns None for the case where neither node's ebit reached across the connection, or in the case of one-sided-epr-share, the one ebit didnt reach across the channel.
        use_this_nodes_pair = None
        
        neighbour_has_both_ebits = neighbour_received
        this_node_has_both_ebits = this_node_received
        
        if this_node_has_both_ebits and neighbour_has_both_ebits:
            # use bigger id's ebits
            if self._neighbour_responsible_for_ebit(neighbour_name):
                use_this_nodes_pair = False
            else:
                use_this_nodes_pair = True
        elif (not this_node_has_both_ebits) and neighbour_has_both_ebits:
            # use this node's ebit
            use_this_nodes_pair = True
        elif this_node_has_both_ebits and (not neighbour_has_both_ebits):
            # use neighbour's ebit
            use_this_nodes_pair = False
        else: # case: (not this_node_has_both_ebits) and (not neighbour_has_both_ebits):
            # attempt again if num_of_tries <= nc. otherwise, nothing can be done (larger id node to inform NIS for data collection purposes).
            pass
        
        return use_this_nodes_pair

    def _qpass_p2_alg(self):
        # TODO: could add a processing time delay here since the qpass p2 alg is supposed to run on each node. Im just running it on the NIS at the beginning of each ts so avoid running the exact same thing multiple times.
        assign_channels, major_paths = self.nis.qpass_p2_result
        return assign_channels, major_paths

    def _qcast_p2_alg(self):
        raise NotImplementedError("QCAST not implemented yet")

    def _p1(self):
        # print(f" sim_time = {ns.sim_time():.1f}: {self.name}: p1 start.")
        # Receive S-D pairs from the NIS
        # TODO: do this by sending messages through connections and listening for events
        # TODO: we dont have a direct connection to NIS right? so if we are getting this through the internet then there might be some delay (probably doesnt matter since its at the very start anyway)
        self.sd_pairs = self.nis.curr_sd_pairs

        p1_delay = globals.args.p1_delay
        self._schedule_after(p1_delay, NodeEntity.p1_done_evtype)

    def _p2(self, _):
        # Qubit Assignment / External Phase
        def start_p2(_):
            nonlocal self
            # print(f" sim_time = {ns.sim_time():.1f}: {self.name}: p2 start.")

            if globals.args.alg is globals.ALGS.SLMPG:
                self.major_paths = None # Not applicable # do i actually need this? not sure why i put it here in the first place TODO
                slmp_global.p2(self)

            if globals.args.alg is globals.ALGS.SLMPL:
                self.major_paths = None # Not applicable # do i actually need this? not sure why i put it here in the first place TODO
                slmp_local.p2(self)

            # QPASS ans QCAST has some preprocessing before p2 (or start of p2? confirm)
            # SLMP l/g dont have anything like this so we just called their p2 function
            '''
            if globals.args.alg is globals.ALGS.QPASS:
                # TODO: could add a processing time delay here since the qpass p2 alg is supposed to run on each node. Im just running it on the NIS at the beginning of each ts so avoid running the exact same thing multiple times.
                assign_channels, major_paths = self._qpass_p2_alg()
                recovery_paths = None # p2 also needs to return this. used in p4
            elif globals.args.alg is globals.ALGS.QCAST:
                assign_channels, major_paths, recovery_paths = self._qcast_p2_alg()
            '''
            
            '''
            if globals.args.alg in [globals.ALGS.QPASS, globals.ALGS.QCAST]: # TODO: this if statement doesnt have to be here. The following part should be common to all 4 algs. Right now the input/output to p2 algs needs to be adjusted slightly. fix this
                self.major_paths = major_paths
                self.curr_qubit_channel_assignment = {} # key = memory index for the qubit. value = num corresponding to channels (starts at 0)
                qubit_assignment = []
                for u, v in assign_channels:
                    num_channels = assign_channels[(u, v)]
                    if self.name in [u, v]: # checking if this node is connected to this edge.
                        send_to = u if self.name == v else v
                        for c in range(num_channels):
                            if qubit_assignment.count(send_to) < self.network.graph[u][v]["width"]:
                                # TODO: there may be a small issue with qpass p2 alg. it can assign more qubits on an edge than its width (i think this happens only for partial paths). Not sure what to do other than this if statement or spending time into that algorithm in detail.
                                qubit_assignment.append(send_to)
            
                # TODO: the following is not v efficient. write better code:
                qubit_mem_index = -1
                nodes_to_sent_to = list(set(qubit_assignment)) # list of unique nodes
                qubit_and_channel_assignmets = []
                for node in nodes_to_sent_to:
                    for channel_num in range(qubit_assignment.count(node)):
                        qubit_and_channel_assignmets.append((node, channel_num))
                for n, c in qubit_and_channel_assignmets:
                    qubit_mem_index += 1
                    self.curr_qubit_channel_assignment[qubit_mem_index] = (n, c)
            '''

            self._establish_links()
        
        start_p2(None)

        p2_delay_after_timeout = globals.args.p2_delay
        timeout = globals.args.link_establish_timeout
        self._schedule_after(timeout+p2_delay_after_timeout, NodeEntity.p2_done_evtype)

    def _p3(self, _):
        # Exchange Link State
        def start_p3(_):
            nonlocal self
            # print(f" sim_time = {ns.sim_time():.1f}: {self.name}: p3 start.")
            
            if (globals.args.alg is globals.ALGS.SLMPG):
                slmp_global.p3(self)

            if (globals.args.alg is globals.ALGS.QPASS): # this is basically the same code as SLMPG, might want to combine the code
                self._gen_final_link_state() # see which ebits to use. discard one of the ebits where both side were success

                # TODO: maybe. Add an option to send through the internet/NIS (larger delays, uncertain delays etc)
                # To send directly through neighbours, create a message and send it to next neighbour in the shortest path who forwards it further. All nodes know the topology. Also, might want to add that drop any message from an earlier ts.
                
                for k_neighbour in self.k_hop_neighbours:
                    send_through_node = self.network.get_node(k_neighbour.path_to[1]).entity
                    msg_packet = self._gen_message_packet(msg_type=globals.MSG_TYPE.link_state, src_name=self.name, dst_name=k_neighbour.name, path=k_neighbour.path_to, curr_ts=self.curr_ts, link_state=self.link_state)
                    
                    self.send_message(send_through_node.name, msg_packet)
                
                # TODO: Sending to next hop on path right now. maybe an option for sending via internet/NIS or whatever should be implemented
           
            elif globals.args.alg is globals.ALGS.SLMPL:
                # In SLMPl, only the two nodes across an edge know about the status of the local link. so nothing to do here (final link state already generated above)
                pass

            elif globals.args.alg is globals.ALGS.QCAST:
                pass # TODO: will probably be mostly the same as SLMPG. use that if statement or write new code if changes needed.
        
        start_p3(None)

        p3_delay = globals.args.p3_delay
        self._schedule_after(p3_delay, NodeEntity.p3_done_evtype)

    def _p4(self, _):
        # Place internal link / Internal Phase
        def start_p4(_):
            nonlocal self
            # print(f" sim_time = {ns.sim_time():.1f}: {self.name}: p4 start.")
            if globals.args.alg is globals.ALGS.SLMPG:
                slmp_global.p4(self)

            if globals.args.alg is globals.ALGS.SLMPL:
                slmp_local.p4(self)

            if globals.args.alg is globals.ALGS.QPASS:
                qpass.p4()
                
            if globals.args.alg is globals.ALGS.QCAST:
                qcast.p4()

        start_p4(None)

        p4_delay = globals.args.p4_delay
        self._schedule_after(p4_delay, NodeEntity.p4_done_evtype)
    
    def _store_corrections(self, msg_packet):
        KEYS = globals.MSG_KEYS
        path = msg_packet[KEYS.PATH]
        m0, m1 = msg_packet[KEYS.CORRECTIONS]
        data_qubit_state = msg_packet[KEYS.DATA_QUBIT_STATE]
        sender_name = msg_packet[KEYS.SRC]
        serving_pair = msg_packet[KEYS.SERVING_PAIR]
        src_name, dst_name = serving_pair

        if m0 is None and m1 is None: # is both m0 and m1 are None then the swap operation was a failure. so dont do anything
            return            

        if self.name == dst_name: # case when this is dest node
            if self.name != path[-1]:
                path.append(self.name)
            self.e2e_paths_sofar.append(path) # not used. remove TODO

        if data_qubit_state is None: # regular case
            if self._apply_corrections_and_swap_next(serving_pair, path, sender_name, m0, m1):
                return
            else:
                # if above function returns false then that means corrections couldnt be applied as the epr pair has already been swapped. so forward the message packet to the node that now holds this epr pair
                next_node_name = None
                for swapped_pair in self.swapped_nodes:
                    if swapped_pair[0] == sender_name:
                        next_node_name = swapped_pair[1]
                        break
                    if swapped_pair[1] == sender_name:
                        next_node_name = swapped_pair[0]
                        break
                
                if self.name != path[-1]:
                    path.append(self.name)
                self.send_message(
                    next_node_name, 
                    message=self._gen_message_packet(
                            msg_type=globals.MSG_TYPE.corrections,
                            src_name=self.name,
                            dst_name=next_node_name,
                            path=path,
                            serving_pair=serving_pair,
                            corrections=(m0, m1),
                            corrections_via=msg_packet[KEYS.CORRECTIONS_VIA].append(self.name)
                            ),
                    )
        else:
            # case when received corrections of the data qubit/teleported qubit
            self._receive_teleported_qubit(m0, m1, data_qubit_state, path, serving_pair)

    def _get_ebit_shared_with(self, node_name):
        # returns the ebit and also returns the ebit's index in main qmem or conn mem. also returns whether this self.node's ebit is used or not
        ebit = None

        using_my_ebit = None
        for link in self.link_state['final']:
            if link[0] == node_name:
                using_my_ebit = False
                channel_num = link[2]
                break
            elif link[1] == node_name:
                using_my_ebit = True
                channel_num = link[2]
                break
        
        qmem = None
        if using_my_ebit is not None:
            if using_my_ebit:
                qubit_mem_index = [n.name for n in self.imm_neighbours].index(node_name)
                qmem = self.node.qmemory
            else:
                conn_qmem_label = self.network.gen_label(node_name, self.name, of=globals.CONN_CHANN_LABELS_FN_PARAM.CONN_QMEM, num=channel_num)
                conn_qmem = self.node.subcomponents[conn_qmem_label]
                qmem = conn_qmem
                qubit_mem_index = 0 # only 1 position for connection memory on each node
            
            ebit = qmem.mem_positions[qubit_mem_index].get_qubit(remove=True)
        else:
            ebit, qubit_mem_index, using_my_ebit = None, None, None
        
        return ebit, qubit_mem_index, using_my_ebit

    def _role(self, paths):
        # returns the enum for source, destination, or repeater as per the role in this ts. Note that source and destination also perform the same repeating operations but they just do not have anything after p4.
        ROLES = globals.ROLES
        pathwise_roles = [] # will store this nodes' role for each path
        for path in paths:
            if self.name not in path:
                pathwise_roles.append(ROLES.NO_TASK)
            else:
                if path[0] == self.name:
                    # is source
                    pathwise_roles.append(ROLES.SOURCE)
                elif path[-1] == self.name:
                    pathwise_roles.append(ROLES.DESTINATION)
                else:
                    pathwise_roles.append(ROLES.REPEATER)
        
        return pathwise_roles

    def _swap(self, serving, path):
        prev_node_name = path[path.index(self.name) - 1]
        next_node_name = path[path.index(self.name) + 1]
        src_side_ebit, _, _ = self._get_ebit_shared_with(prev_node_name)
        dst_side_ebit, _, _ = self._get_ebit_shared_with(next_node_name)
        
        if src_side_ebit is None:
            return
        if dst_side_ebit is None:
            return
        
        m0, m1 = quantum.prepare_corrections(src_side_ebit, dst_side_ebit)
        
        if not self._swap_successful(): # q parameter
            m0, m1 = None, None
        
        self.send_message(
            next_node_name, 
            message=self._gen_message_packet(
                    msg_type=globals.MSG_TYPE.corrections,
                    src_name=self.name,
                    dst_name=next_node_name,
                    path=path,
                    serving_pair=serving,
                    corrections=(m0, m1)
                    ),
            ) # the node receiving this message will run self._store_corrections()
        self.swapped_nodes.append((prev_node_name, next_node_name))
    
    def _teleport_qubit(self, serving_pair, path):
        src_name, dst_name = serving_pair
        if src_name != self.name:
            # if i am not the source then dont do anything
            return
        
        data_qubit, ref_idx = quantum.get_data_qubit_for((src_name, dst_name))

        if data_qubit is None and ref_idx is None: # this can happen with slmpl since you are trying to find as many paths as possible.
            # then you have the e2e path ready but no qubit to send
            return

        e2e_ebit, _, _ = self._get_ebit_shared_with(path[1])
        m0, m1 = quantum.prepare_corrections(data_qubit, e2e_ebit)
        self.send_message(
            dst_name, 
            message=self._gen_message_packet(
                    msg_type=globals.MSG_TYPE.corrections,
                    src_name=self.name,
                    dst_name=dst_name,
                    corrections=(m0, m1),
                    data_qubit_state=ref_idx,
                    path=path,
                    serving_pair=serving_pair
                    ),
            send_directly=False, # src and dest may or may not be neighbours. so letting the send_message figure out the next hop itself
            )
    
    def _apply_corrections_and_swap_next(self, serving_pair, path, sender_name, m0, m1):
        src_name, dst_name = serving_pair
        is_dest = True if self.name == dst_name else False
        ebit, index, using_mine = self._get_ebit_shared_with(sender_name)
        if ebit is None:
            # this can happen in SLMP local if this swap has already been done
            # upon return, the node will forward corrections to the node that now share the epr pair with the sender
            return False
        teleported_qubit, _ = quantum.apply_corrections(ebit, (m0, m1))
        
        # put the teleported qubit back into memory:
        if using_mine: # then put into main qmem
            qmem = self.node.qmemory
        else:   # put in conn qmem
            conn_qmem_label = self.network.gen_label(sender_name, self.name, of=globals.CONN_CHANN_LABELS_FN_PARAM.CONN_QMEM, num=0) # TODO: channel num is hardcodded
            qmem = self.node.subcomponents[conn_qmem_label]
        qmem.put(teleported_qubit, positions=index)

        if not is_dest:
            # print(f" sim_time = {ns.sim_time():.1f}: {self.name}: swapped ebit after receiving corrections from {sender_name}")
            if globals.args.alg is globals.ALGS.SLMPG:
                self._swap(serving_pair, path)

        if is_dest: # destination node has the extra step to let source node know that they share an e2e ebit. so schedule a e2e_ready_evtype event
            if path[0] == src_name and path[-1] == dst_name: # send e2e ready message if e2e path ready (useful check for slmpl)
                self._send_e2e_ready_message(serving_pair, path)

        return True

    def _receive_teleported_qubit(self, m0, m1, data_qubit_state, path, serving_pair):
        e2e_ebit, _, _ = self._get_ebit_shared_with(path[-2])
        teleported_qubit, fidelity = quantum.apply_corrections(e2e_ebit, (m0, m1), original_state_idx=data_qubit_state)
        # print(f" sim_time = {ns.sim_time():.1f}: {self.name}: received the data qubit with fidelity {fidelity:.3f} over path {path}")
        self.nis.data_collector.add_data(
            ts=self.curr_ts,
            src_name=serving_pair[0],
            dst_name=serving_pair[1],
            path=path,
            fidelity=float(f"{fidelity:.3f}"),
            num_eprs_used=len(path)-1,
            num_eprs_created=self.nis.epr_total_created(self.curr_ts),
            x_dist=utils.grid_x_dist(serving_pair[0], serving_pair[1]),
            y_dist=utils.grid_y_dist(serving_pair[0], serving_pair[1]),
        )

    def _gen_links_graph(self, og_graph, neighbours_link_states: list):
        # generates an nx graph comprising of successful links (edges over which epr pairs have been shared successfully)
        link_states = neighbours_link_states
        link_states[self.name] = self.link_state
        links_graph = nx.Graph()
        already_added = []
        for n in link_states.keys():
            edges_list = link_states[n]['final']
            for e in edges_list:
                if e not in already_added:
                    already_added.append(e)
                    links_graph.add_edge(e[0], e[1], channel_num=e[2], length=og_graph[e[0]][e[1]]['length'])
        return links_graph

    def _set_event_handler_params(self, ev_type, ev_src, params):
        entity = ev_src
        key = (ev_type, entity)
        val = params
        self.events_msg_passing.setdefault(key,[]).append(val)
    
    def _get_event_handler_params(self, ev_type, ev_src):
        return self.events_msg_passing.pop((ev_type, ev_src), None)

    def _send_e2e_ready_message(self, serving_pair, path):
        # this is sent to whoever is at the start of the path. this lets that node know that it shares an e2e ebit with dst. if that node is src, it will teleport the data qubit. otherwise do nothing.
        send_to = path[0]
        self.send_message(
            send_to, 
            message=self._gen_message_packet(
                    msg_type=globals.MSG_TYPE.e2e_ready,
                    src_name=self.name,
                    dst_name=send_to,
                    path=path,
                    serving_pair=serving_pair,
                    ),
            send_directly=False
            ) # the node receiving this message will run self._teleport_qubit()

    def _swap_successful(self):
        q = globals.args.prob_swap_loss
        op_successful = utils.rand_success(p_of_fail=q)
        
        return op_successful

class NIS(pydynaa.Entity): # The Network Information Server
    new_ts_evtype = pydynaa.EventType("NEW_TIMESLOT", "A new timeslot has begun.")
    _init_new_ts_evtype = pydynaa.EventType("INIT_NEW_TIMESLOT", "Prepare for the next timeslot.")

    def __init__(self, nw):
        self.network = nw
        self.traffic_matrix: list = None
        self.curr_ts: int = 0
        self.curr_sd_pairs: list = None
        self.total_num_ts = globals.args.num_ts
        '''self.offline_paths = {} # candidate paths for QPASS -- generated by yen's alg at the very start before ts=1'''
        self._epr_track = {}
        self.data_collector = data_collector.DataCollector()

        tm: list = None
        if globals.args.traffic_matrix is globals.TRAFFIC_MATRIX_CHOICES.random:
            tm = traffic_matrix.random_traffic_matrix(self.network)
        elif globals.args.traffic_matrix is globals.TRAFFIC_MATRIX_CHOICES.file:
            tm = traffic_matrix.tm_from_file(globals.args.tm_file)
        else:
            raise NotImplementedError("Other traffic matrix options to be implemented")
        self.set_traffic_matrix(tm)

        # run any pre ts=1 tasks that the algorithms may need to run
        if globals.args.alg is globals.ALGS.SLMPG:
            slmp_global.pre_ts_1_tasks()
        elif globals.args.alg is globals.ALGS.SLMPL:
            slmp_local.pre_ts_1_tasks()
            '''
            elif globals.args.alg is globals.ALGS.QPASS:
                qpass.pre_ts_1_tasks(self)
            elif globals.args.alg is globals.ALGS.QCAST:
                qcast.pre_ts_1_tasks()
                raise NotImplementedError("QCAST not implemented yet.")
            '''
        else:
            raise NotImplementedError("Unknown algorithm selected.")

        # set up the event to trigger self._new_ts fn
        self._wait(
                event_type = NIS._init_new_ts_evtype, # Only events of the given event_type will match the filter.
                entity = self, # Only events from this entity will match the filter
                handler = pydynaa.EventHandler(self._new_ts), # The event or expression handler to be invoked when a triggered event matches the given filter.
            )

    def set_traffic_matrix(self, tm):
        for sds_in_ts in tm:
            for sdpair in sds_in_ts:
                quantum.new_sd_pair(sdpair)
        
        self.traffic_matrix = tm

    def start(self):
        self._schedule_now(NIS._init_new_ts_evtype)

    def _new_ts(self, _):
        self.curr_ts += 1
        # print(f"time slot {self.curr_ts}")
        self.curr_sd_pairs = self._this_ts_sd_pairs()
        
        if globals.args.alg is globals.ALGS.SLMPG:
            slmp_global.paths_found_already = {}
        
        if globals.args.alg is globals.ALGS.QPASS:
            qpass._run_qpass_p2_alg(self)
        
        self._schedule_now(NIS.new_ts_evtype)  # node entities start their time slots with this event

        # schedule the event for start of the next timeslot (unless currently in the last ts):
        if self.curr_ts < globals.args.num_ts:
            self._schedule_after(globals.args.ts_length, NIS._init_new_ts_evtype)

    def _this_ts_sd_pairs(self):
        return self.traffic_matrix[self.curr_ts - 1] # -1 because index 0 stores sd pairs for ts=1 and so on.
  
    def save_exp_results(self):
        self.data_collector.save_results()

    # < epr tracking>

    def epr_track_add(self, ts, gen_by, gen_for):
        self._epr_track.setdefault(ts, []).append([gen_by, gen_for, 'unused'])
        
    def epr_track_update(self, ts, gen_by, gen_for, update):
        i = self._epr_track[ts].index([gen_by, gen_for, 'unused'])
        self._epr_track[ts][i] = [gen_by, gen_for, update]

    def epr_track_print(self):
        # for ts in self._epr_track.keys():
        #     print(f"ts = {ts}")
        #     for x in self._epr_track[ts]:
        #         print(f"\t{x}")
        count_used = 0
        count_unused = 0
        for ts in self._epr_track.keys():
            this_ts_count_used = 0
            this_ts_count_unused = 0
            print(f"ts = {ts}")
            for x in self._epr_track[ts]:
                if x[-1] == 'used':
                    count_used += 1
                    this_ts_count_used += 1
                else:
                    count_unused += 1
                    this_ts_count_unused += 1
            total = this_ts_count_used+this_ts_count_unused
            print(f"Out of total {total}\n used = {this_ts_count_used}\n unused = {this_ts_count_unused} \n percentage used = {100*this_ts_count_used/total}%\n percentage unused = {100*this_ts_count_unused/total}%")
        
        total = count_used+count_unused
        print(f"Overall: Out of total {total}\n used = {count_used}\n unused = {count_unused} \n percentage used = {100*count_used/total}%\n percentage unused = {100*count_unused/total}%")

    def epr_total_created(self, ts):
        count_used = 0
        count_unused = 0
        for x in self._epr_track[ts]:
            if x[-1] == 'used':
                count_used += 1
                continue
            count_unused += 1
        return count_used+count_unused
    
    # </ epr tracking>