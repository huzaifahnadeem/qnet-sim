'''
This file is supposed to contain classes for the entities in the network which includes: the network nodes, and the network information server.
'''

import pydynaa
import globals
import random 
import networkx as nx
from queue import PriorityQueue
import netsquid as ns
import copy
from functools import reduce

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
    
    def __init__(self, name, node):
        self.name = name
        self.node = node
        self.network = None
        self.nis = None
        self.curr_ts = None
        self.sd_pairs = []
        self.curr_role = None
        self.k_hop_neighbours = [] # nodes that are <= k hops away
        self.imm_neighbours = [] # immediate neighbours (share an edge)
        self.connections = {}

    def set_nis_entity(self, nis):
        self.nis = nis

    def set_network(self, nw):
        self.network = nw
        self.k_hop_neighbours = self._find_k_hop_neighbours()
        self.imm_neighbours = [n for n in self.k_hop_neighbours if n.k_hop == 1]

    def _find_k_hop_neighbours(self):
        k_hop_neighbours = []

        hop = globals.args.p3_hop
        ego_graph = nx.ego_graph(G=self.network.nx_graph, n=self.name, radius=hop)
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
            # w quantum connections:
            for chan_num in range(self.network.nx_graph[self.name][n.name]["width"]):
                qlabel = self.network.gen_label(self.name, n.name, of=qconn_option, num=chan_num)
                self.connections[n.name].append(self.network.get_connection(self.name, n.name, qlabel))
        
        t = 1

    def is_neighbour(self, node, imm_neighbour_only=True):
        neighbours = self.imm_neighbours
        if not imm_neighbour_only:
            neighbours = self.k_hop_neighbours
        
        is_a_neighbour = False if [n for n in neighbours if n.name == node] == [] else True
        return is_a_neighbour

    def send_message(self, v, message):
        if self.is_neighbour(v):
            self.network.send_message(self.name, v, message)
        else:
            raise ValueError(f"Node {v.name} is not an immediate neighbour of {self.name} so this message cannot be sent.")
        
    def send_qubit(self, v, qubit, channel_num=0):
        if self.is_neighbour(v):
            self.network.send_qubit(self.name, v, qubit, channel_num)
        else:
            raise ValueError(f"Node {v} is not an immediate neighbour of {self.name} so this qubit cannot be sent.")

    def _setup(self):
        # this is to set up anything that could not be set up with the constructor (e.g. connections variable)
        self._set_connections()

    def start(self):
        self._setup()
        self._wait(
                event_type = NIS.new_ts_evtype,
                entity = self.nis,
                handler = pydynaa.EventHandler(self._new_ts),
            )

    def _cleanup(self):
        # This is to clear up any variable states at the start of a new timeslot
        self.node.qmemory.discard(self.node.qmemory.used_positions, check_positions=False) # discard all qubits in memory from previous ts
        self.curr_qubit_channel_assignment = {} # reset qubit-channel assignments
        self.major_paths = None
        self.link_state = {}
        self.neighbours_link_state = {}
        # TODO: discard connection qmem qubits from prev ts if any

    def _new_ts(self, _):
        self._cleanup()
        self.curr_ts = self.nis.curr_ts
        # TODO: add "flow of time" (call p1, p2 fns using events)
        self._p1()
        self._p2()
        self._p3()
        self._p4()
        self._send_data_qubit()
        self._receive_data_qubit()
    
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
            
            # update your link states
            self.add_to_link_state(src_name, self.name, conn_num, qubit_received)

            # let the neighbour know
            self.send_message(
                src_name, 
                message=self._gen_message_packet(
                    msg_type='ebit-received',
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

    def _gen_message_packet(self, msg_type, src_name=None, dst_name=None, dst_path=None, curr_ts=None, link_state=None, conn_num=None, ebit_received_successfully=None):
        KEYS = globals.MSG_KEYS
        msg_packet = {}
        if msg_type == 'ebit-sent':
            msg_packet = {
                KEYS.TYPE: msg_type,
                KEYS.SRC: src_name,
                KEYS.DST: dst_name,
                KEYS.CONN_NUM: conn_num,
            }
        elif msg_type == 'ebit-received':
            msg_packet = {
                KEYS.TYPE: msg_type,
                KEYS.SRC: src_name,
                KEYS.DST: dst_name,
                KEYS.CONN_NUM: conn_num,
                KEYS.EBIT_RECV_SUCCESS: ebit_received_successfully,
            }
        elif msg_type == 'link-state':
            msg_packet = {
                KEYS.TYPE: msg_type,
                KEYS.SRC: src_name,
                KEYS.DST: dst_name,
                KEYS.TS: curr_ts,
                KEYS.PATH: dst_path, # not really needed but makes coding slightly easier.
                KEYS.LINK_STATE: link_state,
            }
        
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
                other_way = (qb_dst, qb_src)
                vu_status = ls[other_way][chann_num]
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
                elif use_this_node_epr == False:
                    final_ls.append((neighbour_name, self.name, chann_num))
                done.append((qb_src, qb_dst))
                done.append((qb_dst, qb_src))
        self.link_state = final_ls

    def add_to_link_state(self, ebit_from, ebit_to, on_channel_num, received_successfully):
        if (ebit_from, ebit_to) not in self.link_state.keys():
            self.link_state[(ebit_from, ebit_to)] = {}
        
        self.link_state[(ebit_from, ebit_to)][on_channel_num] = received_successfully

    def save_neighbours_link_state(self, neighbour_name, link_state):
        self.neighbours_link_state[neighbour_name] = link_state

    def _establish_links(self):
        if globals.args.two_sided_epr == False:
            raise NotImplementedError("one sided epr share not implemented yet")
        
        # TODO: implement nc functionality
        # nc = globals.args.p2_nc
        for qubit_index in self.curr_qubit_channel_assignment.keys():
            to_node, channel_num = self.curr_qubit_channel_assignment[qubit_index]
            q1, q2 = self._gen_epr_pair()
            self.node.qmemory.put(q1, positions=qubit_index)
            self.send_qubit(to_node, q2, channel_num)
            self.send_message(
                to_node, 
                message=self._gen_message_packet(
                    msg_type='ebit-sent',
                    src_name=self.name,
                    dst_name=to_node,
                    conn_num=channel_num,
                    ),
                )
               
    def _neighbour_responsible_for_ebit(self, neighbour_name):
        bigger_id_node_name = neighbour_name if int(neighbour_name[1:]) > int(self.name[1:]) else self.name
        if bigger_id_node_name == neighbour_name:
            return True
        return False

    def _use_this_node_epr(self, neighbour_name, neighbour_received, this_node_received):
        # returns: True if use this node's pair. False is neighbour's is to be used. Returns None for the case where neither node's ebit reached across the connection, or in the case of one-sided-epr-share, the one ebit didnt reach across the channel.
        use_this_nodes_pair = None
        if globals.args.two_sided_epr == True:
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
        else: # case for one sided epr share
            if self._neighbour_responsible_for_ebit(neighbour_name):
                use_this_nodes_pair = False
                if this_node_received == False:
                    use_this_nodes_pair = None
            else:
                use_this_nodes_pair = True
                if neighbour_received == False:
                    use_this_nodes_pair = None
        
        return use_this_nodes_pair

    def _gen_epr_pair(self):
        q1, q2 = ns.qubits.create_qubits(2)
        ns.qubits.operate(q1, ns.H)
        ns.qubits.operate([q1, q2], ns.CNOT)
        
        return q1, q2

    def _qpass_p2_alg(self):
        # TODO: could add a processing time delay here since the qpass p2 alg is supposed to run on each node. Im just running it on the NIS at the beginning of each ts so avoid running the exact same thing multiple times.
        assign_channels, major_paths = self.nis.qpass_p2_result
        return assign_channels, major_paths

    def _qcast_p2_alg(self):
        raise NotImplementedError("QCAST not implemented yet")

    def _p1(self):
        print(f" sim_time = {ns.sim_time():.1f}: {self.name}: p1 start.")
        # Receive S-D pairs from the NIS
        # TODO: do this by sending messages through connections and listening for events
        # TODO: we dont have a direct connection to NIS right? so if we are getting this through the internet then there might be some delay (probably doesnt matter since its at the very start anyway)
        self.sd_pairs = self.nis.curr_sd_pairs
        self.curr_role = self._role()

        p1_delay = 1 # TODO: input param?
        self._schedule_after(p1_delay, NodeEntity.p1_done_evtype)

    def _p2(self):
        # Qubit Assignment / External Phase
        def start_p2(_):
            nonlocal self
            print(f" sim_time = {ns.sim_time():.1f}: {self.name}: p2 start.")
            # # Test: # TODO: remove this code
            # # <>
            # if self.name == 'n1' and self.curr_ts==3:
            #     self.network.send_message(self.name, 'n5', message='hello')
            #     q = ns.qubits.create_qubits(1, no_state=True)
            #     print(f'n1: {q}')
            #     self.network.send_qubit(self.name, 'n5', qubit=q)
            #     q2 = ns.qubits.create_qubits(1, no_state=True)
            #     print(f'n1: {q2}')
            #     self.send_qubit('n2', q2, 2)
            
            # if self.name == 'n4' and self.curr_ts==4:
            #     self.send_message('n8', 'hey')
            #     q = ns.qubits.create_qubits(1, no_state=True)
            #     print(f'n4: {q}')
            #     self.send_qubit('n8', q)
            # # </>

            if globals.args.alg is globals.ALGS.QPASS:
                # TODO: could add a processing time delay here since the qpass p2 alg is supposed to run on each node. Im just running it on the NIS at the beginning of each ts so avoid running the exact same thing multiple times.
                assign_channels, major_paths = self._qpass_p2_alg()
                recovery_paths = None # p2 also needs to return this. used in p4
            else:
                assign_channels, major_paths, recovery_paths = self._qcast_p2_alg()
            
            self.major_paths = major_paths
            self.curr_qubit_channel_assignment = {} # key = memory index for the qubit. value = num corresponding to channels (starts at 0)
            qubit_assignment = []
            for u, v in assign_channels:
                num_channels = assign_channels[(u, v)]
                if self.name in [u, v]: # checking if this node is connected to this edge.
                    send_to = u if self.name == v else v
                    for c in range(num_channels):
                        if qubit_assignment.count(send_to) < self.network.nx_graph[u][v]["width"]:
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
            self._establish_links()
        
        self._wait_once(
            event_type = NodeEntity.p1_done_evtype,
            entity = self,
            handler = pydynaa.EventHandler(start_p2),
        )

        p2_delay_after_timeout = 10 # TODO: input param?
        timeout = globals.args.link_establish_timeout
        self._schedule_after(timeout+p2_delay_after_timeout, NodeEntity.p2_done_evtype)

    def _p3(self):
        # Exchange Link State
        def start_p3(_):
            nonlocal self
            print(f" sim_time = {ns.sim_time():.1f}: {self.name}: p3 start.")
            self._gen_final_link_state() # see which ebits to use. discard one of the ebits where both side were success
            
            # TODO: maybe. Add an option to send through the internet/NIS (larger delays, uncertain delays etc)
            # To send directly through neighbours, create a message and send it to next neighbour in the shortest path who forwards it further. All nodes know the topology. Also, might want to add that drop any message from an earlier ts.
            # Assuming no message drops? # TODO: would be pretty neat to add that too (more realistic)
            
            for k_neighbour in self.k_hop_neighbours:
                send_through_node = self.network.get_node(k_neighbour.path_to[1]).entity
                msg_packet = self._gen_message_packet(msg_type='link-state', src_name=self.name, dst_name=k_neighbour.name, dst_path=k_neighbour.path_to, curr_ts=self.curr_ts, link_state=self.link_state)
                
                self.send_message(send_through_node.name, msg_packet)
            
            # TODO: working with k=1 initially. so need to implement forwarding/direct sending via internet/NIS or whatever
            # receive other's packets -- we are assuming no packet loss so we can just move on to phase 4 where we can look at message queue and save other's link states.
        
        self._wait_once(
            event_type = NodeEntity.p2_done_evtype,
            entity = self,
            handler = pydynaa.EventHandler(start_p3),
        )

        p3_delay = 30 # TODO: input param? # this delay includes the delay for p1, and p2
        self._schedule_after(p3_delay, NodeEntity.p3_done_evtype)

    def _p4(self):
        # Place internal link / Internal Phase
        def start_p4(_):
            nonlocal self
            print(f" sim_time = {ns.sim_time():.1f}: {self.name}: p4 start.")

        self._wait_once(
            event_type = NodeEntity.p3_done_evtype,
            entity = self,
            handler = pydynaa.EventHandler(start_p4),
        )

        p4_delay = 1 # TODO: input param?
        self._schedule_after(p4_delay, NodeEntity.p4_done_evtype)
    
    def _role(self):
        # returns the enum for source, destination, or repeater as per the role in this ts. Note that source and destination also perform the same repeating operations but they just do not have anything after p4.
        ROLES = globals.ROLES
        for s,d in self.sd_pairs:
            if self.name == s:
                return ROLES.SOURCE
            if self.name == d:
                return ROLES.DESTINATION
        return ROLES.REPEATER

    def _send_data_qubit(self):
        if self.curr_role is not globals.ROLES.SOURCE:
            return
        
        pass # TODO
    
    def _receive_data_qubit(self):
        if self.curr_role is not globals.ROLES.DESTINATION:
            return
        
        pass # TODO

class NIS(pydynaa.Entity): # The Network Information Server
    new_ts_evtype = pydynaa.EventType("NEW_TIMESLOT", "A new timeslot has begun.")
    _init_new_ts_evtype = pydynaa.EventType("INIT_NEW_TIMESLOT", "Prepare for the next timeslot.")

    def __init__(self, nw):
        self.network = nw
        self.traffic_matrix = None
        self.curr_ts = 0
        self.curr_sd_pairs = None
        self.total_num_ts = globals.args.num_ts
        self.offline_paths = {} # candidate paths for QPASS -- generated by yen's alg at the very start before ts=1

        if globals.args.alg is globals.ALGS.QPASS:
            self._run_yens_alg()
        else:
            raise NotImplementedError("QCAST not implemented yet")

        self._wait(
                event_type = NIS._init_new_ts_evtype, # Only events of the given event_type will match the filter.
                entity = self, # Only events from this entity will match the filter
                handler = pydynaa.EventHandler(self._new_ts), # The event or expression handler to be invoked when a triggered event matches the given filter.
            )
    
    def set_traffic_matrix(self, tm):
        self.traffic_matrix = tm

    def init_random_traffic_matrix(self, node_names):
        # TODO: might want to look into quantum overlay paper's traffic matrix generation process and use that.
        num_of_ts = globals.args.num_ts
        max_num_sds = globals.args.max_sd
        min_num_sds = globals.args.min_sd

        tm = []
        for _ in range(num_of_ts):
            this_ts_sds = []
            num_sds = random.randint(min_num_sds, max_num_sds)
            
            sources = random.choices(node_names, k = num_sds)
            for s in sources:
                while True:
                    d = random.choice(node_names)
                    if s != d:
                        this_ts_sds.append((s, d))
                        break

            tm.append(this_ts_sds)
        
        self.set_traffic_matrix(tm)

    def start(self):
        self._schedule_now(NIS._init_new_ts_evtype)

    def _new_ts(self, _):
        self.curr_ts += 1
        self.curr_sd_pairs = self._this_ts_sd_pairs()
        if globals.args.alg is globals.ALGS.QPASS:
            self._run_qpass_p2_alg()
        self._schedule_now(NIS.new_ts_evtype)

        # schedule the event for start of the next timeslot (unless currently in the last ts):
        if self.curr_ts < globals.args.num_ts:
            # TODO: first param of the following (== time slot length)
            self._schedule_after(100, NIS._init_new_ts_evtype)

    def _this_ts_sd_pairs(self):
        return self.traffic_matrix[self.curr_ts - 1] # -1 because index 0 stores sd pairs for ts=1 and so on.
    
    def _run_yens_alg(self):
        # nx.shortest_simple_paths function uses yen's algorithm as per the the reference on networkx' website: https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.simple_paths.shortest_simple_paths.html
        # This sub function is also adapted from the same source:
        
        from itertools import islice
        def k_shortest_paths(G, source, target, k, weight=None):
            return list(islice(nx.shortest_simple_paths(G, source, target, weight=weight), k))

        # need three positional params for these fns (to be used as 'weight' param when calling the fn above). params = start node, end node, dict containing properties of the edge
        def ext(u, v, _): # This one is the best in theory but would take too long to run in practice
            # use equation in paper's section 4.1
            raise NotImplementedError("EXT metric not implemented yet") # TODO
        
        def sum_dist(): # this is a little different than the other routing metric functions. we wont be passing this function, we only need the string it returns
            return 'length'

        def creation_rate(u, v, _): # best one after EXT. the paper uses this since its better than sumdist and bottleneckcap and has a decent performance
            # computed as sum(1/p_i) where p_i is the success rate of any channel on the i-th hop of the path. Presumably, all channels of an edge have same probability of success value.
            # Note that the paper says that CR takes into account the path width. p_i is the success on ANY channel for that edge.
            raise NotImplementedError("CR metric not implemented yet") # TODO

        def bottleneck_cap(u, v, _):
            # bottleneck_cap metric is just "-W" i.e. -1*W. use CR to break ties for paths with the same width.
            raise NotImplementedError("BotCap metric not implemented yet") # TODO
        
        # TODO: the paper also have a "multimetric" option. look into that.

        k = globals.args.yen_n # TODO: in the paper it is mentioned "N will grow by 50% percent in the next offline phase if the paths happen happen to be not enough for a pair."

        if globals.args.yen_metric is globals.YEN_METRICS.EXT:
            weight_fn = ext
        elif globals.args.yen_metric is globals.YEN_METRICS.SUMDIST:
            weight_fn = sum_dist() # note the parenthesis. for this one we are calling the function and using the returned string and not the function itself.
        elif globals.args.yen_metric is globals.YEN_METRICS.CR:
            weight_fn = creation_rate
        elif globals.args.yen_metric is globals.YEN_METRICS.BOTCAP:
            weight_fn = bottleneck_cap
        elif globals.args.yen_metric is globals.YEN_METRICS.HOPCOUNT: # the paper doesnt consider this but added this for the sake of completion. SLMP implicitly chooses to use this.
            weight_fn = None

        for n1 in self.network.node_names():
            for n2 in self.network.node_names():
                if n1 == n2:
                    continue
                self.offline_paths[(n1, n2)] = k_shortest_paths(self.network.nx_graph, source=n1, target=n2, k=k, weight=weight_fn)

    def _run_qpass_p2_alg(self):
        # writing the following function to match the alg1 in the paper as closely as possible
        def qpass_p2_alg(G, O, P):
            # inputs: G = <V, E, C> (graph: V vertices, E edges, C capacity), O = list of S-D pairs, P = mapping from any S-D pair to its offline paths
            # outputs: <L_C, L_P>; L_C = list of channels to assigned qubits, L_P = ordered list of selected paths
            def construct_node_capacity_map(G):
                T_Q = {}
                for n_name in G.node_names():
                    node = G.get_node(G.get_node(n_name))
                    T_Q[n_name] = copy.deepcopy(node.qmemory.num_positions)
                return T_Q
            
            def edges_of_path(p):
                edge_path = []
                for i in range(1, len(p)):
                    edge_path.append((p[i-1], p[i]))
                return edge_path
            
            # note that the width of a path is defined as being equal to the width of the edge with the smallest width.
            def Width(p, T_Q, L_P=None): # capital W in name to match the fn name in the paper
                nonlocal G
                def w_after_LP(L_P, u, v, width_original):
                    edge_width_used = 0
                    for path_w, p in L_P:
                        for lu, lv in edges_of_path(p):
                            if (u == lu) and (v == lv):
                                edge_width_used += path_w
                    return width_original - edge_width_used


                w = float("inf")
                for u, v in edges_of_path(p):
                    width_original = G.nx_graph[u][v]["width"]
                    width_after_removing_LP = float("inf") if L_P is None else w_after_LP(L_P, u, v, width_original)
                    width_effective = min([width_original, T_Q[u], T_Q[v], width_after_removing_LP])
                    if width_effective < w:
                        w = width_effective

                return w

            def get_routing_metric_val(p, w):
                # w will be used by some of the metrics
                m = None
                nonlocal G
                # TODO: these functions are defined in yen's alg as well. make and use a single copy of these functions
                if globals.args.yen_metric is globals.YEN_METRICS.EXT:
                    raise NotImplementedError("EXT metric not implemented yet") # TODO
                elif globals.args.yen_metric is globals.YEN_METRICS.SUMDIST:
                    m = 0
                    for u, v in edges_of_path(p):
                        m += G.nx_graph[u][v]["length"]
                elif globals.args.yen_metric is globals.YEN_METRICS.CR:
                    raise NotImplementedError("CR metric not implemented yet") # TODO
                elif globals.args.yen_metric is globals.YEN_METRICS.BOTCAP:
                    raise NotImplementedError("BOTCAP metric not implemented yet") # TODO
                elif globals.args.yen_metric is globals.YEN_METRICS.HOPCOUNT:
                    m = 0
                    for _ in edges_of_path(p):
                        m += 1
                
                return m
            
            def priority_queue_as_list(q):
                q_list = []
                while q.empty() == False:
                    q_list.append(q.get())
                return q_list

            L_C = []                                                                    # line 1 of alg1 in paper
            L_P = []
            T_Q = {}
            T_Q = construct_node_capacity_map(G)
            W = {}                                                                      # line 5
            q = PriorityQueue()
            for o in O:
                for p in P[o]:
                    W[tuple(p)] = Width(p, T_Q)
                    m = get_routing_metric_val(p, W[tuple(p)])                                 # line 10
                    q.put((m, p))
            while not q.empty():
                _, p = q.get()
                if Width(p, T_Q, L_P) < W[tuple(p)]: # The width of p has changed
                    W[tuple(p)] = Width(p, T_Q, L_P); q.put((get_routing_metric_val(p, W[tuple(p)]), p))   # line 15
                    continue
                if Width(p, T_Q, L_P) == 0: # Even the best path is unsatisfiable
                    q.put((get_routing_metric_val(p, W[tuple(p)]), p)); break
                L_P.append((W[tuple(p)], p))
                for n1, n2 in edges_of_path(p):                                         # line 20
                    T_Q[n1] = T_Q[n1] - W[tuple(p)]
                    T_Q[n2] = T_Q[n2] - W[tuple(p)]
                    L_C.append((n1, n2, W[tuple(p)])) # need to bind "W[p]" many channels between n1 and n2
            # partial = L_P + priority_queue_as_list(q)
            partial = priority_queue_as_list(q)
            for _, p in partial:                                                           # line 25
                for n1, n2 in edges_of_path(p):
                    if Width([n1, n2], T_Q, L_P) > 0: # only on available edges
                        T_Q[n1] = T_Q[n1] - 1
                        T_Q[n2] = T_Q[n2] - 1
                        L_C.append((n1, n2, 1))
            return L_C, L_P
        
        nw = self.network
        sd_pairs_list = self.curr_sd_pairs # = list of (s, d)
        sd_pair_to_offline_path_map = self.offline_paths # dict keyed by (s, d). val = list of lists with each list being a path (path is list of nodes in the path includes src and dest)
        
        L_C, L_P = qpass_p2_alg(
            G = nw,
            O = sd_pairs_list,
            P = sd_pair_to_offline_path_map,
        )

        major_paths = L_P # ordered list of selected paths
        assign_channels = {} # list of channels to assign qubits
        for n1, n2, num_c in L_C:
            if (n1, n2) not in assign_channels.keys():
                assign_channels[(n1, n2)] = 0
            assign_channels[(n1, n2)] += num_c

        self.qpass_p2_result = assign_channels, major_paths