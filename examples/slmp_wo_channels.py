import netsquid as ns
import pydynaa
import logging
from functools import reduce
import random
import networkx as nx
import copy
import argparse

import data_logger as dl

data_logger = dl.DataLogger(labels=['ts', 'data_qubit_transmitted', 'x-hop', 'y-hop'])

class config:
    seed = 0
    num_of_timeslots = 5
    time_slot_length = 100

    ebits_ready_delay = 10 # how long it takes for the ebits to be ready after you initiate the generation process
    ebits_across_channel_delay = 10
    ext_phase_end_delay = 5

    internal_phase_delay = 10
    corrections_delay = 5

    prob_ebit_arrives_successfully_over_channel = 50 # p probability parameter
    prob_swap_op_successful = 10 # q probability parameter
    p = prob_ebit_arrives_successfully_over_channel
    q = prob_swap_op_successful

# ns.set_random_state(seed=config.seed)
# random.seed(config.seed)

def calc_x_sep(n1, n2):
    num1 = int(n1[1:])
    num2 = int(n2[1:])

    counter = 1
    for n in [num1, num2]:
        if n not in [1, 2, 3, 4]:
            if n in [13, 14, 15, 16]:
                n -= 4
            if n in [9, 10, 11, 12]:
                n -= 4
            if n in [5, 6, 7, 8]:
                n -= 4
        if counter == 1:
            num1 = n 
        else:
            num2 = n 
        counter += 1
    return abs(num1 - num2)


def calc_y_sep(n1, n2):
    num1 = int(n1[1:])
    num2 = int(n2[1:])

    counter = 1
    for n in [num1, num2]:
        if n not in [1, 5, 9, 13]:
            if n in [4, 8, 12, 16]:
                n -= 1
            if n in [3, 7, 11, 15]:
                n -= 1
            if n in [2, 6, 10, 14]:
                n -= 1
        if counter == 1:
            num1 = n 
        else:
            num2 = n 
        counter += 1
    return int(abs((num1 - num2)/4))

def ebit_arrives_across_channel():
    arrives = True
    prob_ebit_lost_over_channel = 1 - config.prob_ebit_arrives_successfully_over_channel
    r = random.randint(1, 100)
    if r <= prob_ebit_lost_over_channel:
        arrives = False
    
    return arrives

def swap_op_successful():
    op_successful = False
    q = config.prob_swap_op_successful
    r = random.randint(1, 100)
    if r <= q:
        op_successful = True
    
    return op_successful

class NodeEntity(pydynaa.Entity):
    external_phase_done_evtype = pydynaa.EventType("EXT_PHASE_DONE", "External Phase complete (epr pair generation + sending to neighbour)")
    ebits_ready_evtype = pydynaa.EventType("EPR_PAIR_READY", "Entangled qubits are ready.")
    # swap_operation_done_evtype = pydynaa.EventType("SWAP_DONE", "This repeater node has performed the swap operation.")
    # swap_operation_fail_evtype = pydynaa.EventType("SWAP_FAIL", "This repeater node's swap operation failed.")
    corrections_ready_evtype = pydynaa.EventType("CORRECTION_READY", "Corrections are ready.")
    done_talking_to_neighbour_end_of_ext_phase_evtype = pydynaa.EventType("TALKED TO NEIGHBOUR", "Talked to one of the neighbours right before the end of external phase")

    swap_operation_update_evtype = pydynaa.EventType("SWAP_UPDATE", "This repeater node's swap operation is complete (either succeeded or failed -- check messages for details).")

    def __init__(self, name, traffic_mat, net_graph):
        self.name = name
        self.traffic_matrix = traffic_mat
        self.net_graph = net_graph
        self.controller_entity = None
        self.node_entities = {}
        self.curr_ts = 0
        self.role = None
        self.neighbours = self.net_graph[self.name]
        self.smaller_id_neighbours = [n for n in self.neighbours if int(n[1:]) < int(self.name[1:])]
        self.bigger_id_neighbours = [n for n in self.neighbours if int(n[1:]) > int(self.name[1:])]
        self.ebits_memory = {}
        self.ebits_to_send = {}
        self.ebits_received = {}
        self.data_qbit = None
        self.swap_data = {}
        self.corrections = None
        # self.neighbours_comm_events = {}
        # for n in self.neighbours:
        #     self.neighbours_comm_events[n] = {
        #         'received_ebit': pydynaa.EventType("RECEIVED EBIT", "Received the epr originating from this neighbour"),
        #         'not_received_ebit': pydynaa.EventType("NOT RECEIVED EBIT", "Did not received the epr originating from this neighbour"),
        #         }

        self.neighbours_comm_events = {}
        for n in self.neighbours:
            self.neighbours_comm_events[n] = {
                'ebit_receival': {
                    'event': pydynaa.EventType("EBIT_RECEIVAL_UPDATE", "There is an update regarding whether or not this node received ebit sent by this neighbour"), # the event object
                    'message': '', # optional message field that may be required for this particular event. 
                    }
                }
        self.event_msgs = {
            'swap': '',
            'neighbouring-src-dst-case': False,
        }


    def set_controller_entity(self, controller_entity):
        self.controller_entity = controller_entity
    
    def set_node_entitities(self, node_entities):
        self.node_entities = node_entities

    def start(self):
        logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: starts.")
        self._wait(
                event_type = ControllerEntity.new_ts_evtype,
                entity = self.controller_entity,
                handler = pydynaa.EventHandler(self._new_ts),
            )
    
    def reset(self):
        # reset the following fields:
        self.event_msgs = {
            'swap': '',
            'neighbouring-src-dst-case': False,
        }
        for n in self.neighbours:
            self.neighbours_comm_events[n] = {
                'ebit_receival': {
                    'event': pydynaa.EventType("EBIT_RECEIVAL_UPDATE", "There is an update regarding whether or not this node received ebit sent by this neighbour"), # the event object
                    'message': '', # optional message field that may be required for this particular event. 
                    }
                }

    def _new_ts(self, _):
        self.reset()
        self.curr_ts += 1
        self.role = self._role_in_this_ts()

        logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: starting external phase procedure.")
        self._external_phase()
        # external phase done, wait for the signal to start the internal phase:
        self._wait_once(
            event_type = ControllerEntity.start_internal_phase_evtype,
            entity = self.controller_entity,
            handler = pydynaa.EventHandler(self._internal_phase),
        )
    
    def _role_in_this_ts(self):
        if self.traffic_matrix[self.curr_ts]['src'] == self.name:
            role = 'src'
        elif self.traffic_matrix[self.curr_ts]['dst'] == self.name:
            role = 'dst'
        else:
            role = 'repeater'
        
        return role

    def _external_phase(self):
        # generate a pair of ebits for each neighbour
        epr_neighbours = self.neighbours
        for n in epr_neighbours:
            q1, q2 = self._gen_entangled_qubits()
            self.ebits_to_send[n] = q1
            self.ebits_memory[n] = q2

        # signal to all that ebits are ready
        logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: has ebits ready for {epr_neighbours}")
        for n in epr_neighbours:
            self._schedule_after(config.ebits_ready_delay, NodeEntity.ebits_ready_evtype)
        
        # receive any prepared ebits that your neighbours have ready for you
        ebit_ready_events = [
            pydynaa.EventExpression(
                    source = self.node_entities[n],
                    event_type = NodeEntity.ebits_ready_evtype,
                )
            for n in epr_neighbours
        ]
        wait_for_neighbours = reduce(lambda x, y: x & y, ebit_ready_events)
        self._wait_once(
            expression = wait_for_neighbours,
            handler = pydynaa.EventHandler(self._receive_ebits),
        )

    def _gen_entangled_qubits(self):
        q1, q2 = ns.qubits.create_qubits(2)
        ns.qubits.operate(q1, ns.H)
        ns.qubits.operate([q1, q2], ns.CNOT)
        
        return q1, q2

    def _receive_ebits(self, _):
        for n in self.neighbours:
            ebit = self.node_entities[n].ebits_to_send[self.name]
            if ebit_arrives_across_channel():
                self.ebits_received[n] = ebit
                logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: received ebit from {n}.")
                # self._schedule_after(config.ebits_across_channel_delay, self.neighbours_comm_events[n]['received_ebit'])
                self.neighbours_comm_events[n]['ebit_receival']['message'] = 'success'
                self._schedule_after(config.ebits_across_channel_delay, self.neighbours_comm_events[n]['ebit_receival']['event'])
            else:
                self.ebits_received[n] = None
                logging.info(f" sim_time = {ns.sim_time():.1f}: ebit from {n} to {self.name} got lost over the channel.")
                # self._schedule_after(config.ebits_across_channel_delay, self.neighbours_comm_events[n]['not_received_ebit'])
                self.neighbours_comm_events[n]['ebit_receival']['message'] = 'failure'
                self._schedule_after(config.ebits_across_channel_delay, self.neighbours_comm_events[n]['ebit_receival']['event'])
        
        # if applicable, decide which ebit to use (the one you created, or the one you received from the neighbour)
        # find out which of the neighbours got your ebit
        for n in self.neighbours:
            # self._wait_once(
            #         entity = self.node_entities[n],
            #         event_type = self.node_entities[n].neighbours_comm_events[self.name]['received_ebit'],
            #         handler = pydynaa.EventHandler(self._neighbour_received_ebit),
            #     )
            # self._wait_once(
            #         entity = self.node_entities[n],
            #         event_type = self.node_entities[n].neighbours_comm_events[self.name]['not_received_ebit'],
            #         handler = pydynaa.EventHandler(self._neighbour_received_ebit),
            #     )
            self._wait_once(
                    entity = self.node_entities[n],
                    event_type = self.node_entities[n].neighbours_comm_events[self.name]['ebit_receival']['event'],
                    handler = pydynaa.EventHandler(self._neighbour_received_ebit),
                )
        
        sub_events_for_end_of_ext_ph = [
            pydynaa.EventExpression(
                    source = self.node_entities[n],
                    event_type = NodeEntity.done_talking_to_neighbour_end_of_ext_phase_evtype,
                )
            for n in self.neighbours
        ]
        wait_for_end_of_ext_phase_subevents = reduce(lambda x, y: x & y, sub_events_for_end_of_ext_ph)
        self._wait_once(
            expression = wait_for_end_of_ext_phase_subevents,
            handler = pydynaa.ExpressionHandler(self._signal_end_of_ext_phase),
        )

    def _neighbour_received_ebit(self, event):
        # event_name = event.type.name # = "RECEIVED EBIT" or "NOT RECEIVED EBIT"
        neighbour_name = event.source.name
        if self.node_entities[neighbour_name].neighbours_comm_events[self.name]['ebit_receival']['message'] == 'success':
            ebit_received = True
        elif self.node_entities[neighbour_name].neighbours_comm_events[self.name]['ebit_receival']['message'] == 'failure':
            ebit_received = False
        else:
            ebit_received = None
        self.node_entities[neighbour_name].neighbours_comm_events[self.name]['ebit_receival']['message'] = '' # reset message field
        
        # if event_name == "RECEIVED EBIT":
        if ebit_received:
            neighbour_has_both_ebits = True
            # # dismiss the other event wait
            # self._dismiss(
            #     entity = self.node_entities[neighbour_name],
            #     event_type = self.node_entities[neighbour_name].neighbours_comm_events[self.name]['not_received_ebit'],
            #     handler = pydynaa.EventHandler(self._neighbour_received_ebit),
            # )
        elif not ebit_received:
            neighbour_has_both_ebits = False
            # dismiss the other event wait
            # self._dismiss(
            #     entity = self.node_entities[neighbour_name],
            #     event_type = self.node_entities[neighbour_name].neighbours_comm_events[self.name]['received_ebit'],
            #     handler = pydynaa.EventHandler(self._neighbour_received_ebit),
            # )

        bigger_id_node_name = neighbour_name if int(neighbour_name[1:]) > int(self.name[1:]) else self.name
        
        this_node_has_both_ebits = False
        if self.ebits_received[neighbour_name] is not None:
            this_node_has_both_ebits = True

        if this_node_has_both_ebits and neighbour_has_both_ebits:
            # use bigger id's ebits
            if bigger_id_node_name == neighbour_name:
                ebit_to_use = self.ebits_received[bigger_id_node_name]
            else:
                ebit_to_use = self.ebits_memory[neighbour_name]
            self.ebits_memory[neighbour_name] = ebit_to_use
            logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: will use ebit generated by {bigger_id_node_name} for comm. with {neighbour_name}.")
        elif (not this_node_has_both_ebits) and neighbour_has_both_ebits:
            # use own ebit:
            ebit_to_use = self.ebits_memory[neighbour_name]
            self.ebits_memory[neighbour_name] = ebit_to_use
            logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: will use ebit generated by {self.name} for comm. with {neighbour_name}.")
        elif this_node_has_both_ebits and (not neighbour_has_both_ebits):
            # use neighbour's ebit
            ebit_to_use = self.ebits_received[neighbour_name]
            self.ebits_memory[neighbour_name] = ebit_to_use
            logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: will use ebit generated by {neighbour_name} for comm. with {neighbour_name}.")
        else: # case: (not this_node_has_both_ebits) and (not neighbour_has_both_ebits):
            # nothing can be done
            logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: no ebit available for comm. with {neighbour_name}.")
            # if you are the bigger id node, you are responsible to let the controller entity know about this. (using bigger id node to avoid two messages to the controller entity for each edge)
            if bigger_id_node_name == self.name:
                edge_tuple = (self.name, neighbour_name)
                self.controller_entity.log_unsuccessful_ebit_share(edge_tuple) # let the controller entity know about this.
        
        self._schedule_after(config.ext_phase_end_delay, NodeEntity.done_talking_to_neighbour_end_of_ext_phase_evtype)

    def _signal_end_of_ext_phase(self, _):
        logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: signals end of external phase.")
        self._schedule_now(NodeEntity.external_phase_done_evtype)

    def _internal_phase(self, _):
        if self.controller_entity.skip_to_next_ts:
            # logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: skipping internal phase procedure (since no path possible in this ts).")
            return
        
        logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: starting internal phase procedure.")
        self.e2e_path_this_ts = self.controller_entity.e2e_path_this_ts
        if self.role == 'src':
            self._prepare_to_teleport_qubit()
        elif self.role == 'dst':
            self._prepare_to_receive_teleported_qbit()
        else: # role == 'repeater' 
            self._perform_swaps()
    
    # internal phase -> role = src:
    def _prepare_to_teleport_qubit(self):
        logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: role is '{self.role}'.")
        
        # wait for swap operations to finish:
        repeater_nodes_on_path = self.e2e_path_this_ts[1:-1]
        
        if repeater_nodes_on_path == []:
            self.event_msgs['neighbouring-src-dst-case'] = True
            self._teleport_data_qubit()
        else:
            # wait for a signal from the destination that swapping has been performed and it has the e2e ebit.
            dst_node_name = self.traffic_matrix[self.curr_ts]['dst']
            dst_node_entity = self.node_entities[dst_node_name]
            # self._wait_once(
            #     event_type = NodeEntity.swap_operation_done_evtype,
            #     entity = dst_node_entity,
            #     handler = pydynaa.EventHandler(self._teleport_data_qubit),
            # )
            # self._wait_once(
            #     event_type = NodeEntity.swap_operation_fail_evtype,
            #     entity = dst_node_entity,
            #     handler = pydynaa.EventHandler(self._teleport_failure_no_e2e_ebit),
            # )
            self._wait_once(
                event_type = NodeEntity.swap_operation_update_evtype,
                entity = dst_node_entity,
                handler = pydynaa.EventHandler(self._teleport_data_qubit),
            )
    
    def _teleport_data_qubit(self, event = None):
        def prepare_qubit_send_corrections(self=self):
            # prepare the data qubit
            self.data_qbit,  = ns.qubits.create_qubits(1, no_state=True)
            data_qubit_state = self.traffic_matrix[self.curr_ts]['data_qubit_state']
            ns.qubits.assign_qstate([self.data_qbit], data_qubit_state)
            
            # corrections:
            next_node_on_path = self.e2e_path_this_ts[1] # next node with the order: src -> dst
            ebit = self.ebits_memory[next_node_on_path]
            m0, m1 = self._prepare_corrections(self.data_qbit, ebit)
            self.corrections = (m0, m1)
        
        dst_node_entity = self.node_entities[self.traffic_matrix[self.curr_ts]['dst']]
        # # dismiss waiting on the other possible event
        # self._dismiss(
        #         event_type = NodeEntity.swap_operation_fail_evtype,
        #         entity = dst_node_entity,
        #         handler = pydynaa.EventHandler(self._teleport_failure_no_e2e_ebit),
        #     )

        if self.event_msgs['neighbouring-src-dst-case'] == True: # case when src and dst are neighbours
            self.event_msgs['neighbouring-src-dst-case'] = False
            prepare_qubit_send_corrections()
            # signal corrections ready:
            self._schedule_after(config.corrections_delay, NodeEntity.corrections_ready_evtype)
        else:
            if dst_node_entity.event_msgs['swap'] == 'failure':
                dst_node_entity.event_msgs['swap'] = '' # reset
                self._teleport_failure_no_e2e_ebit()
            elif dst_node_entity.event_msgs['swap'] == 'success':
                dst_node_entity.event_msgs['swap'] = '' # reset
                prepare_qubit_send_corrections()
                # signal corrections ready:
                self._schedule_after(config.corrections_delay, NodeEntity.corrections_ready_evtype)
    
    def _teleport_failure_no_e2e_ebit(self, _=None):
        # dismiss waiting on the other possible event
        # dst_node_entity = self.node_entities[self.traffic_matrix[self.curr_ts]['dst']]
        # self._dismiss(
        #     event_type = NodeEntity.swap_operation_done_evtype,
        #     entity = dst_node_entity,
        #     handler = pydynaa.EventHandler(self._teleport_data_qubit),
        # )
        logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: Failed to teleport the data qubit due to a swap failure on path.")
        data_logger.add_data_point([self.curr_ts, 'fail', self.controller_entity.this_ts_xhop, self.controller_entity.this_ts_yhop])


    def _prepare_corrections(self, data_qubit, entangled_qubit):
        ns.qubits.operate([data_qubit, entangled_qubit], ns.CNOT)
        ns.qubits.operate(data_qubit, ns.H)
        m0, _ = ns.qubits.measure(data_qubit)
        m1, _ = ns.qubits.measure(entangled_qubit)

        return m0, m1

    # internal phase -> role = dst:
    def _prepare_to_receive_teleported_qbit(self):
        logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: role is '{self.role}'.")
        src_node_name = self.traffic_matrix[self.curr_ts]['src']
        src_node_entity = self.node_entities[src_node_name]

        # first perform the steps to generate e2e ebit during the swapping process:
        prev_node_on_path = self.e2e_path_this_ts[-2]
        prev_repeater_node_on_path = prev_node_on_path if prev_node_on_path != src_node_name else None
        if prev_repeater_node_on_path is not None: # if == None, then the source is directly on the left. in that case, no swapping required so just move to the next step.
            # wait for the left-side neighbour on path to generate the corrections. When done, apply corrections to get the e2e ebit. then proceed to next step
            left_side_repeater_entity = self.node_entities[prev_repeater_node_on_path]
            self.swap_data['dst-left-side-repeater'] = prev_repeater_node_on_path
            # self._wait_once(
            #     event_type = NodeEntity.swap_operation_done_evtype,
            #     entity = left_side_repeater_entity,
            #     handler = pydynaa.EventHandler(self._dst_gen_e2e_ebit_post_swap),
            # )
            # self._wait_once(
            #     event_type = NodeEntity.swap_operation_fail_evtype,
            #     entity = left_side_repeater_entity,
            #     handler = pydynaa.EventHandler(self._swap_fail),
            # )
            self._wait_once(
                event_type = NodeEntity.swap_operation_update_evtype,
                entity = left_side_repeater_entity,
                handler = pydynaa.EventHandler(self._dst_gen_e2e_ebit_post_swap),
            )
        else:
            # case where the source is your direct neighbour:
            prev_node_on_path = self.e2e_path_this_ts[-2]
            e2e_ebit = self.ebits_memory[prev_node_on_path]
            self.e2e_ebit = e2e_ebit

            # wait for the source to send you the corrections. # here
            self._wait_once(
                    event_type = NodeEntity.corrections_ready_evtype,
                    entity = src_node_entity,
                    handler = pydynaa.EventHandler(self._receive_teleported_qbit),
                )

    def _dst_gen_e2e_ebit_post_swap(self, _):
        l_repeater_node_on_path = self.swap_data['dst-left-side-repeater']
        left_side_repeater_entity = self.node_entities[l_repeater_node_on_path]
        
        if left_side_repeater_entity.event_msgs['swap'] == 'success':
            swap_success = True
            left_side_repeater_entity.event_msgs['swap'] = '' # reset
        elif left_side_repeater_entity.event_msgs['swap'] == 'failure':
            swap_success = False
            left_side_repeater_entity.event_msgs['swap'] = '' # reset
        else:
            swap_success = None
        # # dismiss waiting on the other event (case failure):
        # self._dismiss(
        #     event_type = NodeEntity.swap_operation_fail_evtype,
        #     entity = left_side_repeater_entity,
        #     handler = pydynaa.EventHandler(self._swap_fail),
        # )

        if swap_success:
            ebit_to_correct = self.ebits_memory[l_repeater_node_on_path]
            corrections = left_side_repeater_entity.swap_data['corrections-for-swap']
            _, e2e_ebit = self._apply_corrections(ebit_to_correct, corrections)
            self.e2e_ebit = e2e_ebit
            logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: done with its swapping procedure. It now has the e2e ebit.")
            # self._schedule_after(1, NodeEntity.swap_operation_done_evtype)
            self.event_msgs['swap'] = 'success'
            self._schedule_after(1, NodeEntity.swap_operation_update_evtype)
            # wait for the source to send you the corrections.
            src_node_name = self.traffic_matrix[self.curr_ts]['src']
            src_node_entity = self.node_entities[src_node_name]
            self._wait_once(
                    event_type = NodeEntity.corrections_ready_evtype,
                    entity = src_node_entity,
                    handler = pydynaa.EventHandler(self._receive_teleported_qbit),
                )
        elif not swap_success:
            self._swap_fail()

    def _apply_corrections(self, ebit, corrections, original_state=None):
        m0 = corrections[0]
        m1 = corrections[1]

        if m1:
            ns.qubits.operate(ebit, ns.X)
        if m0:
            ns.qubits.operate(ebit, ns.Z)
        
        if original_state is not None:
            fidelity = ns.qubits.fidelity(ebit, original_state, squared=True)
        else:
            fidelity = None
        
        return fidelity, ebit
    
    def _receive_teleported_qbit(self, _):
        src_node_name = self.traffic_matrix[self.curr_ts]['src']
        logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: ready to receive the data qubit from the source ({src_node_name})")
        logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: got the signal that corrections are ready at {src_node_name}.")
        src_node_entity = self.node_entities[src_node_name]
        original_state = self.traffic_matrix[self.curr_ts]['data_qubit_state']
        corrections = src_node_entity.corrections
        ebit = self.e2e_ebit
        fidelity,_ = self._apply_corrections(ebit, corrections, original_state)
        logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: qubit state teleported with fidelity = {fidelity:.3f}")
        data_logger.add_data_point([self.curr_ts, 'success', self.controller_entity.this_ts_xhop, self.controller_entity.this_ts_yhop])

    # internal phase -> role = repeater:
    def _perform_swaps(self):
        logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: role is '{self.role}'.")
        if self.name not in self.e2e_path_this_ts:
            logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: is not on the path. so this node is done in this ts")
        else:
        # try:
            my_pos_on_path = self.e2e_path_this_ts.index(self.name)
            src_node_name = self.traffic_matrix[self.curr_ts]['src']
            prev_node_on_path = self.e2e_path_this_ts[my_pos_on_path - 1]
            next_node_on_path = self.e2e_path_this_ts[my_pos_on_path + 1]
            prev_repeater_node_on_path = prev_node_on_path if prev_node_on_path != src_node_name else None
            next_repeater_node_on_path = next_node_on_path

            if prev_repeater_node_on_path is None: # if i am the first repeater node on path:
                # do swap operations:
                self.swap_data['ebit-to-teleport'] = self.ebits_memory[src_node_name]
                self.swap_data['ebit-shared'] = self.ebits_memory[next_repeater_node_on_path]
                if swap_op_successful():
                    self._teleport_ebit()
                    # signal that you are done with your part:
                    logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: done with its swapping procedure successfully.")
                    # self._schedule_after(1, NodeEntity.swap_operation_done_evtype)
                    self.event_msgs['swap'] = 'success'
                    self._schedule_after(1, NodeEntity.swap_operation_update_evtype)
                else:
                    logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: swapping procedure failed.")
                    # self._schedule_after(1, NodeEntity.swap_operation_fail_evtype)
                    self.event_msgs['swap'] = 'failure'
                    self._schedule_after(1, NodeEntity.swap_operation_update_evtype)
            else:
                # wait for prev repeater node. receive corrections and apply.
                left_side_repeater_entity = self.node_entities[prev_repeater_node_on_path]
                self.swap_data['left-side-repeater-entity'] = left_side_repeater_entity
                self.swap_data['ebit-to-correct'] = self.ebits_memory[prev_repeater_node_on_path]
                self.swap_data['ebit-shared'] = self.ebits_memory[next_repeater_node_on_path]
                # self._wait_once(
                #     event_type = NodeEntity.swap_operation_done_evtype,
                #     entity = left_side_repeater_entity,
                #     handler = pydynaa.EventHandler(self._apply_corrections_and_swap),
                # )
                # self._wait_once(
                #     event_type = NodeEntity.swap_operation_fail_evtype,
                #     entity = left_side_repeater_entity,
                #     handler = pydynaa.EventHandler(self._swap_fail),
                # )
                self._wait_once(
                    event_type = NodeEntity.swap_operation_update_evtype,
                    entity = left_side_repeater_entity,
                    handler = pydynaa.EventHandler(self._apply_corrections_and_swap),
                )
        # except ValueError:
        #     # if this happens then it means that this repeater node is not on the path.
        #     logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: is not on the path. so this node is done in this ts.")

    def _teleport_ebit(self):
        ebit_to_teleport = self.swap_data['ebit-to-teleport']
        ebit_shared_with_next_node_on_path = self.swap_data['ebit-shared']
        
        m0, m1 = self._prepare_corrections(ebit_to_teleport, ebit_shared_with_next_node_on_path)
        self.swap_data['corrections-for-swap'] = (m0, m1)

    def _apply_corrections_and_swap(self, _):
        left_side_repeater_entity = self.swap_data['left-side-repeater-entity']

        # # dismiss the other event wait
        # self._dismiss(
        #     event_type = NodeEntity.swap_operation_fail_evtype,
        #     entity = left_side_repeater_entity,
        #     handler = pydynaa.EventHandler(self._swap_fail),
        # )

        if left_side_repeater_entity.event_msgs['swap'] == 'success':
            swap_success = True
        elif left_side_repeater_entity.event_msgs['swap'] == 'failure':
            swap_success = False
        else:
            swap_success = None

        if swap_success:
            corrections = left_side_repeater_entity.swap_data['corrections-for-swap']
            ebit_to_correct = self.swap_data['ebit-to-correct']

            _, ebit_to_teleport = self._apply_corrections(ebit_to_correct, corrections)
            self.swap_data['ebit-to-teleport'] = ebit_to_teleport
            if swap_op_successful():
                self._teleport_ebit()
                logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: done with its swapping procedure.")
                # self._schedule_after(1, NodeEntity.swap_operation_done_evtype)
                self.event_msgs['swap'] = 'success'
                self._schedule_after(1, NodeEntity.swap_operation_update_evtype)
            else:
                logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: swapping procedure failed.")
                # self._schedule_after(1, NodeEntity.swap_operation_fail_evtype)
                self.event_msgs['swap'] = 'failure'
                self._schedule_after(1, NodeEntity.swap_operation_update_evtype)
        elif not swap_success:
            self._swap_fail()
    
    def _swap_fail(self, _=None):
        # # dismiss waiting on the other event (case swap done):
        # if self.role == 'dst':
        src_node_name = self.traffic_matrix[self.curr_ts]['src']
        prev_node_on_path = self.e2e_path_this_ts[-2]
        prev_repeater_node_on_path = prev_node_on_path if prev_node_on_path != src_node_name else None
        left_side_repeater_entity = self.node_entities[prev_repeater_node_on_path]
        #     self._dismiss(
        #         event_type = NodeEntity.swap_operation_done_evtype,
        #         entity = left_side_repeater_entity,
        #         handler = pydynaa.EventHandler(self._dst_gen_e2e_ebit_post_swap),
        #     )
        #     # for dst. also dismiss:
        src_node_entity = self.node_entities[src_node_name]
        self._dismiss(
            event_type = NodeEntity.corrections_ready_evtype,
            entity = src_node_entity,
            handler = pydynaa.EventHandler(self._receive_teleported_qbit),
        )
        self._dismiss(
            event_type = NodeEntity.corrections_ready_evtype,
            entity = left_side_repeater_entity,
            handler = pydynaa.EventHandler(self._receive_teleported_qbit),
        )
        # else:
        #     left_side_repeater_entity = self.swap_data['left-side-repeater-entity']
        #     self._dismiss(
        #         event_type = NodeEntity.swap_operation_done_evtype,
        #         entity = left_side_repeater_entity,
        #         handler = pydynaa.EventHandler(self._apply_corrections_and_swap),
        #     )
        logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: got signal that swapping procedure failed for the node before me.")
        self.event_msgs['swap'] = 'failure'
        self._schedule_after(1, NodeEntity.swap_operation_update_evtype)

class ControllerEntity(pydynaa.Entity):
    _init_new_ts_evtype = pydynaa.EventType("INIT_NEW_TIMESLOT", "Prepare for the next timeslot.")
    new_ts_evtype = pydynaa.EventType("NEW_TIMESLOT", "A new timeslot has begun.")
    start_internal_phase_evtype = pydynaa.EventType("START_INTERNAL_PHASE", "Start the internal phase.")

    def __init__(self, node_entities, traffic_matrix, net_graph):
        self.node_entities = node_entities
        self.traffic_matrix = traffic_matrix
        self.net_graph = net_graph
        self.nx_graph = self._create_nx_graph()
        self.name = 'controller'
        self.num_ts = config.num_of_timeslots
        self.ts_length = config.time_slot_length
        self.curr_ts = 0
        self.e2e_path_this_ts = None
        self.unsuccessful_ebit_share_log = []
        self.skip_to_next_ts = False # if no path possible for internal phase, then this becomes true so the nodes skip the internal phase of the current time slot
        self.this_ts_xhop = 0
        self.this_ts_yhop = 0
        self._wait(
                event_type = ControllerEntity._init_new_ts_evtype, # Only events of the given event_type will match the filter.
                entity = self, # Only events from this entity will match the filter
                handler = pydynaa.EventHandler(self._new_ts), # The event or expression handler to be invoked when a triggered event matches the given filter.
            )
    
    def _create_nx_graph(self):
        nx_graph = nx.Graph()
        nodes_names = [i for i in self.net_graph.keys()]
        nx_graph.add_nodes_from(nodes_names)
        done = []
        for u in self.net_graph:
            for v in self.net_graph[u]:
                if ((u, v) not in done) and ((v, u) not in done):
                    nx_graph.add_edge(v, u)
                    nx_graph.add_edge(u, v)
                    done.append((u, v))
                    done.append((v, u))

        return nx_graph

    def start(self):
        logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: starts.")
        self._schedule_now(ControllerEntity._init_new_ts_evtype)
    
    def _new_ts(self, _):
        self.curr_ts += 1
        self.unsuccessful_ebit_share_log = [] # reset to empty list of edges
        self.skip_to_next_ts = False # reset to False
        logging.info(f" sim_time = {ns.sim_time():.1f}: ==== start of ts # {self.curr_ts} ==== ")
        logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: ts # {self.curr_ts} begins.")
        self._schedule_now(ControllerEntity.new_ts_evtype)

        # schedule the event for start of the next timeslot (unless currently in the last ts):
        if self.curr_ts < self.num_ts:
            self._schedule_after(self.ts_length, ControllerEntity._init_new_ts_evtype)

        # wait for external phase to finish:
        external_phase_events = [
            pydynaa.EventExpression(
                    source = self.node_entities[n],
                    event_type = NodeEntity.external_phase_done_evtype,
                )
            for n in self.node_entities
        ]
        
        wait_for_external_phase = reduce(lambda x, y: x & y, external_phase_events)

        self._wait(
            expression = wait_for_external_phase,
            handler = pydynaa.ExpressionHandler(self._ext_phase_done),
            once = True,
        )

    def _ext_phase_done(self, _):
        logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: ext phase done.")
        self.e2e_path_this_ts = self._e2e_path()
        if self.e2e_path_this_ts is None: # i.e. no possible path between src and destination:
            logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: No path possible from src to dst in this timeslot. All nodes moving to next ts.")
            data_logger.add_data_point([self.curr_ts, 'fail', self.controller_entity.this_ts_xhop, self.controller_entity.this_ts_yhop])
            self.skip_to_next_ts = True
        self._schedule_after(config.internal_phase_delay, ControllerEntity.start_internal_phase_evtype)

    def _e2e_path(self):
        src = self.traffic_matrix[self.curr_ts]['src']
        dst = self.traffic_matrix[self.curr_ts]['dst']
        nx_sub_graph = self._subgraph_after_ext_phase(self.nx_graph)
        paths = self._shortest_src_dst_paths(src, dst, nx_sub_graph)
        if paths == []: # i.e. no possible path between src and destination:
            self.this_ts_xhop = -1
            self.this_ts_yhop = -1
            return None
        self.this_ts_xhop = calc_x_sep(src, dst)
        self.this_ts_yhop = calc_y_sep(src, dst)
        return paths[0] # return the shortest of all shortest paths (index 0)

    def _subgraph_after_ext_phase(self, nx_graph_original):
        nx_graph = copy.deepcopy(nx_graph_original)
        edges_list = self.unsuccessful_ebit_share_log
        nx_graph.remove_edges_from(edges_list)
        return nx_graph

    def _shortest_src_dst_paths(self, src, dst, nx_graph_original):
        nx_graph = copy.deepcopy(nx_graph_original)
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

    def log_unsuccessful_ebit_share(self, edge):
        self.unsuccessful_ebit_share_log.append(edge)

def network_graph_setup():
    # multiple src-destination

    graph, traffic_matrix = None, None
    
    ket_minus = ns.h1   # ns.h1 = |−⟩  = 1/√(2)*(|0⟩ − |1⟩)
    ket_plus = ns.h0    # ns.h0 = |+⟩  = 1/√(2)*(|0⟩ + |1⟩)
    ket_1_y = ns.y1     # ns.y0 = |1𝑌⟩ = 1/√(2)*(|0⟩ - 𝑖|1⟩)
    ket_0_y = ns.y0     # ns.y0 = |0𝑌⟩ = 1/√(2)*(|0⟩ + 𝑖|1⟩)
    ket_1 = ns.s1       # ns.s1 = |1⟩
    ket_0 = ns.s0       # ns.s0 = |0⟩

    
    graph = {
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
    
    states = [(ket_minus, '|−⟩'), (ket_plus, '|+⟩'), (ket_1_y, '|1Y⟩'), (ket_0_y, '|1Y⟩'), (ket_1, '|1⟩'), (ket_0, '|0⟩')]
    nodes = [i for i in graph.keys()]
    
    traffic_matrix = {}
    traffic_matrix_print = {}
    for i in range(config.num_of_timeslots):
        src = random.choice(nodes)
        while True:
            dst = random.choice(nodes)
            if src != dst:
                break
        state_tuple = random.choice(states)
        state_state = state_tuple[0]
        state_str = state_tuple[1]
        traffic_matrix[i+1] = { 'src': src, 'dst': dst, 'data_qubit_state': state_state}
        traffic_matrix_print[i+1] = { 'src': src, 'dst': dst, 'data_qubit_state': state_str}
    return graph, traffic_matrix, traffic_matrix_print

def get_args():
    # parser initialization:
    parser = argparse.ArgumentParser(description="slmp global (wo components) experiments related args")

    parser.add_argument('-s', '--seed', required=False, default=0, type=int)
    parser.add_argument('-t', '--num_ts', required=False, default=5, type=int)
    parser.add_argument('-p', '--p_prob', required=False, default=1.0, type=float)
    parser.add_argument('-q', '--q_prob', required=False, default=1.0, type=float)
    parser.add_argument('-c', '--csv_name', required=False, default='slmp-g-no-comp.csv', type=str)

    args = parser.parse_args()

    return args

def handle_args(args):
    config.p = args.p_prob * 100
    config.q = args.q_prob * 100
    config.num_of_timeslots = args.num_ts
    config.seed = args.seed

    ns.set_random_state(seed=config.seed)
    random.seed(config.seed)

def main():
    args = get_args()
    handle_args(args)

    # logging.basicConfig(filename='./examples/slmp-wo-channels.log', encoding='utf-8', level=logging.DEBUG)
    logging.basicConfig(filename='slmp-wo-channels.log', encoding='utf-8', level=logging.DEBUG)
    graph, traffic_matrix, traffic_matrix_print = network_graph_setup()
    logging.info(f" Traffic Matrix:")
    for i in range(config.num_of_timeslots):
        logging.info(f" ts# {i+1}: {traffic_matrix_print[i+1]}")
    logging.info(f" === start ===")
    ns.sim_reset()

    # create node entities:
    node_entities = {}
    for n_name in graph.keys():
        node_entities[n_name] = NodeEntity(n_name, traffic_matrix, graph)
    
    # create the controller entity:
    controller = ControllerEntity(node_entities, traffic_matrix, graph)

    # set the controller entity and node entites properties for the node entities:
    for n_name in graph.keys():
        node_entities[n_name].set_controller_entity(controller)
        node_entities[n_name].set_node_entitities(node_entities)

    for k in node_entities.keys():
        node_entities[k].start() # let all the nodes be ready before the controller starts the first timeslot event.

    # start the controller
    controller.start()

    # start the simulation
    run_stats = ns.sim_run()
    # logging.info(f" === run stats ===")
    # logging.info(run_stats)
    logging.info(f" === end ===")

    data_logger.save_data_csv(args.csv_name)

if __name__ == '__main__':
    main()