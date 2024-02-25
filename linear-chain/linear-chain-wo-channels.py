import netsquid as ns
import pydynaa
import logging
from functools import reduce

class config:
    seed = 0
    num_of_timeslots = 6
    linear_chain_length = 5

    time_slot_length = 100
    ebits_ready_delay = 10 # how long it takes for the ebits to be ready after you initiate the generation process
    internal_phase_delay = 30
    ext_phase_end_delay = 20
    corrections_delay = 5

ns.set_random_state(seed=config.seed)

class NodeEntity(pydynaa.Entity):
    ebits_ready_evtype = pydynaa.EventType("EPR_PAIR_READY", "Entangled qubits are ready.")
    _generate_ebits_evtype = pydynaa.EventType("GENERATE", "Generate entangled qubits.")
    external_phase_done_evtype = pydynaa.EventType("EXT_PHASE_DONE", "External Phase complete (epr pair generation + sending to neighbour)")
    _ebit_recv_evtype = pydynaa.EventType("EBIT_RCV", "An ebit received.")
    _node_ready = pydynaa.EventType("NODE_READY", "Node is ready (set-up complete).")
    corrections_ready_evtype = pydynaa.EventType("CORRECTION_READY", "Corrections are ready.")
    swap_operation_done_evtype = pydynaa.EventType("SWAP_DONE", "This repeater node has performed the swap operation.")

    def __init__(self, name, traffic_mat, net_graph):
        self.name = name
        self.traffic_matrix = traffic_mat
        self.controller_entity = None
        self.node_entities = {}
        self.data_qbit = None
        self.ebits_store = {}
        self.ebits_to_send = {}
        self.swap_data = {} # used by repeater nodes
        self.e2e_ebit = None # used by the destination node
        self.corrections = None
        self.curr_ts = 0
        self.role = None
        self.net_graph = net_graph
        self.neighbours = self.net_graph[self.name]
        self.smaller_id_neighbours = [n for n in self.neighbours if int(n[1:]) < int(self.name[1:])]
        self.bigger_id_neighbours = [n for n in self.neighbours if int(n[1:]) > int(self.name[1:])]
        self.e2e_path_this_ts = None
    
    def set_controller_entity(self, controller_entity):
        self.controller_entity = controller_entity
    
    def set_node_entitities(self, node_entities):
        self.node_entities = node_entities

    def _gen_entangled_qubits(self):
        q1, q2 = ns.qubits.create_qubits(2)
        ns.qubits.operate(q1, ns.H)
        ns.qubits.operate([q1, q2], ns.CNOT)
        
        return q1, q2

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
    
    def _role_in_this_ts(self):
        if self.traffic_matrix[self.curr_ts]['src'] == self.name:
            role = 'src'
        elif self.traffic_matrix[self.curr_ts]['dst'] == self.name:
            role = 'dst'
        else:
            role = 'repeater'
        
        return role

    def _external_phase(self):
        # neighbor with larger id responsible for sending the epr pair
        # generate ebits for smaller-id-neighbours
        for n in self.smaller_id_neighbours:
            q1, q2 = self._gen_entangled_qubits()
            self.ebits_to_send[n] = q1
            self.ebits_store[n] = q2
        # signal to all that ebits are ready
        for n in self.smaller_id_neighbours:
            logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: has an ebit ready for {n}")
            self._schedule_after(config.ebits_ready_delay, NodeEntity.ebits_ready_evtype)
        
        if self.bigger_id_neighbours != []:
            # wait for signal from your larger-id-neighbours and get the relevent ebit from them
            logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: waiting for ebits from {self.bigger_id_neighbours}")
            signals_from_bigger_neighbours = [
                pydynaa.EventExpression(
                        source = self.node_entities[n],
                        event_type = NodeEntity.ebits_ready_evtype,
                    )
                for n in self.bigger_id_neighbours
            ]
            wait_for_all_signals = reduce(lambda x, y: x & y, signals_from_bigger_neighbours)
            self._wait_once(
                expression = wait_for_all_signals,
                handler = pydynaa.EventHandler(self._receive_ebits),
            )
        else:
            self._signal_end_of_ext_phase()
    
    def _receive_ebits(self, event):
        for n in self.bigger_id_neighbours:
            ebit = self.node_entities[n].ebits_to_send[self.name]
            self.ebits_store[n] = ebit
            logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: received ebit from {n}.")
        self._signal_end_of_ext_phase()

    def _signal_end_of_ext_phase(self):
        # TODO: what if the ebit does reach you. There should be some kind of a timeout.
        logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: signals end of external phase.")
        self._schedule_after(config.ext_phase_end_delay, NodeEntity.external_phase_done_evtype)

    def _new_ts(self, event):
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

    def _internal_phase(self, event):
        logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: starting internal phase procedure.")
        self.e2e_path_this_ts = self.controller_entity.e2e_path_this_ts
        if self.role == 'src':
            self._prepare_to_teleport_qubit()
        elif self.role == 'dst':
            self._prepare_to_receive_teleported_qbit()
        else: # role == 'repeater' 
            self._perform_swaps()

    def _perform_swaps(self):
        logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: role is '{self.role}'.")
        try:
            my_pos_on_path = self.e2e_path_this_ts.index(self.name)
            src_node_name = self.traffic_matrix[self.curr_ts]['src']
            left_neighbour_on_path = self.e2e_path_this_ts[my_pos_on_path - 1]
            right_neighbour_on_path = self.e2e_path_this_ts[my_pos_on_path + 1]
            l_repeater_node_on_path = left_neighbour_on_path if left_neighbour_on_path != src_node_name else None
            r_repeater_node_on_path = right_neighbour_on_path

            if l_repeater_node_on_path is None: # if i am the first repeater node on path:
                # do swap operations:
                self.swap_data['ebit-to-teleport'] = self.ebits_store[src_node_name]
                self.swap_data['ebit-shared'] = self.ebits_store[r_repeater_node_on_path]
                self._teleport_ebit()
                # signal that you are done with your part:
                logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: done with its swapping procedure.")
                self._schedule_now(NodeEntity.swap_operation_done_evtype)
            else:
                # wait for prev repeater node. receive corrections and apply.
                left_side_repeater_entity = self.node_entities[l_repeater_node_on_path]
                self.swap_data['left-side-repeater-entity'] = left_side_repeater_entity
                self.swap_data['ebit-to-correct'] = self.ebits_store[l_repeater_node_on_path]
                self.swap_data['ebit-shared'] = self.ebits_store[r_repeater_node_on_path]
                self._wait_once(
                    event_type = NodeEntity.swap_operation_done_evtype,
                    entity = left_side_repeater_entity,
                    handler = pydynaa.EventHandler(self._apply_corrections_and_swap),
                )
        except ValueError:
            # if this happens then it means that this repeater node is not on the path.
            logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: is not on the path.")
    
    def _apply_corrections_and_swap(self, event):
        left_side_repeater_entity = self.swap_data['left-side-repeater-entity']
        corrections = left_side_repeater_entity.swap_data['corrections-for-swap']
        ebit_to_correct = self.swap_data['ebit-to-correct']

        _, ebit_to_teleport = self._apply_corrections(ebit_to_correct, corrections)
        self.swap_data['ebit-to-teleport'] = ebit_to_teleport
        self._teleport_ebit()
        logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: done with its swapping procedure.")
        self._schedule_now(NodeEntity.swap_operation_done_evtype)

    def _prepare_corrections(self, data_qubit, entangled_qubit):
        ns.qubits.operate([data_qubit, entangled_qubit], ns.CNOT)
        ns.qubits.operate(data_qubit, ns.H)
        m0, _ = ns.qubits.measure(data_qubit)
        m1, _ = ns.qubits.measure(entangled_qubit)

        return m0, m1

    def _prepare_to_teleport_qubit(self):
        logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: role is '{self.role}'.")
        
        # wait for swap operations to finish:
        repeater_nodes_on_path = self.e2e_path_this_ts[1:-1]
        
        if repeater_nodes_on_path == []:
            self._teleport_data_qubit()
        else:
            # wait for a signal from the destination that swapping has been performed and it has the e2e ebit.
            dst_node_name = self.traffic_matrix[self.curr_ts]['dst']
            dst_node_entity = self.node_entities[dst_node_name]
            self._wait_once(
                event_type = NodeEntity.swap_operation_done_evtype,
                entity = dst_node_entity,
                handler = pydynaa.EventHandler(self._teleport_data_qubit),
            )

    def _teleport_ebit(self):
        ebit_to_teleport = self.swap_data['ebit-to-teleport']
        ebit_shared_with_right_neighbour = self.swap_data['ebit-shared']
        
        m0, m1 = self._prepare_corrections(ebit_to_teleport, ebit_shared_with_right_neighbour)
        self.swap_data['corrections-for-swap'] = (m0, m1)

    def _teleport_data_qubit(self, event = None):
        # prepare the data qubit
        self.data_qbit,  = ns.qubits.create_qubits(1, no_state=True)
        data_qubit_state = self.traffic_matrix[self.curr_ts]['data_qubit_state']
        ns.qubits.assign_qstate([self.data_qbit], data_qubit_state)
        
        # corrections:
        next_neighbour_on_path = self.e2e_path_this_ts[1]
        ebit = self.ebits_store[next_neighbour_on_path]
        m0, m1 = self._prepare_corrections(self.data_qbit, ebit)
        self.corrections = (m0, m1)
        
        # signal corrections ready:
        self._schedule_after(config.corrections_delay, NodeEntity.corrections_ready_evtype)

    def _prepare_to_receive_teleported_qbit(self):
        logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: role is '{self.role}'.")
        src_node_name = self.traffic_matrix[self.curr_ts]['src']
        src_node_entity = self.node_entities[src_node_name]

        # first perform the steps to generate e2e ebit during the swapping process:
        left_neighbour_on_path = self.e2e_path_this_ts[-2]
        l_repeater_node_on_path = left_neighbour_on_path if left_neighbour_on_path != src_node_name else None
        if l_repeater_node_on_path is not None: # if == None, then the source is directly on the left. in that case, no swapping required so just move to the next step.
            # wait for the left-side neighbour on path to generate the corrections. When done, apply corrections to get the e2e ebit. then proceed to next step
            left_side_repeater_entity = self.node_entities[l_repeater_node_on_path]
            self.swap_data['dst-left-side-repeater'] = l_repeater_node_on_path
            self._wait_once(
                event_type = NodeEntity.swap_operation_done_evtype,
                entity = left_side_repeater_entity,
                handler = pydynaa.EventHandler(self._dst_gen_e2e_ebit_post_swap),
            )
        else:
            prev_neighbour_on_path = self.e2e_path_this_ts[-2]
            e2e_ebit = self.ebits_store[prev_neighbour_on_path]
            self.e2e_ebit = e2e_ebit
            
        # wait for the source to send you the corrections.
        self._wait_once(
                event_type = NodeEntity.corrections_ready_evtype,
                entity = src_node_entity,
                handler = pydynaa.EventHandler(self._receive_teleported_qbit),
            )
    
    def _dst_gen_e2e_ebit_post_swap(self, event):
        l_repeater_node_on_path = self.swap_data['dst-left-side-repeater']
        ebit_to_correct = self.ebits_store[l_repeater_node_on_path]
        left_side_repeater_entity = self.node_entities[l_repeater_node_on_path]
        corrections = left_side_repeater_entity.swap_data['corrections-for-swap']
        _, e2e_ebit = self._apply_corrections(ebit_to_correct, corrections)
        self.e2e_ebit = e2e_ebit
        logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: done with its swapping procedure. It now has the e2e ebit.")
        self._schedule_now(NodeEntity.swap_operation_done_evtype)

    def _receive_teleported_qbit(self, event):
        src_node_name = self.traffic_matrix[self.curr_ts]['src']
        logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: ready to receive the data qubit from the source ({src_node_name})")
        logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: got the signal that corrections are ready at {src_node_name}.")
        src_node_entity = self.node_entities[src_node_name]
        original_state = self.traffic_matrix[self.curr_ts]['data_qubit_state']
        corrections = src_node_entity.corrections
        # next_neighbour_on_path = self.e2e_path_this_ts[-2]
        # ebit = self.ebits_store[next_neighbour_on_path]
        ebit = self.e2e_ebit
        fidelity,_ = self._apply_corrections(ebit, corrections, original_state)
        logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: qubit state teleported with fidelity = {fidelity:.3f}")

    def start(self):
        logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: starts.")
        self._wait(
                event_type = ControllerEntity.new_ts_evtype,
                entity = self.controller_entity,
                handler = pydynaa.EventHandler(self._new_ts),
            )

class ControllerEntity(pydynaa.Entity):
    new_ts_evtype = pydynaa.EventType("NEW_TIMESLOT", "A new timeslot has begun.")
    _init_new_ts_evtype = pydynaa.EventType("INIT_NEW_TIMESLOT", "Prepare for the next timeslot.")
    start_internal_phase_evtype = pydynaa.EventType("START_INTERNAL_PHASE", "Start the internal phase.")

    def __init__(self, node_entities, traffic_matrix):
        self.num_ts = config.num_of_timeslots
        self.ts_length = config.time_slot_length
        self.name = 'controller'
        self.curr_ts = 0
        self.node_entities = node_entities
        self.e2e_path_this_ts = None
        self.traffic_matrix = traffic_matrix

        self._wait(
                event_type = ControllerEntity._init_new_ts_evtype, # Only events of the given event_type will match the filter.
                entity = self, # Only events from this entity will match the filter
                handler = pydynaa.EventHandler(self._new_ts), # The event or expression handler to be invoked when a triggered event matches the given filter.
            )
    
    def _new_ts(self, event):
        self.curr_ts += 1
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
    
    def _ext_phase_done(self, event_expr):
        logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: ext phase done.")
        self.e2e_path_this_ts = self._e2e_path()
        self._schedule_after(config.internal_phase_delay, ControllerEntity.start_internal_phase_evtype)

    def _e2e_path(self):
        src_node_num = int(self.traffic_matrix[self.curr_ts]['src'][1:])
        dst_node_num = int(self.traffic_matrix[self.curr_ts]['dst'][1:])

        
        if src_node_num < dst_node_num: # if dst node after src node in the linear chain:
            path = [f'n{n}' for n in range(src_node_num, dst_node_num + 1)]
        else:
            path = [f'n{n}' for n in range(src_node_num, dst_node_num - 1, -1)]
            
        return path
    
    def start(self):
        logging.info(f" sim_time = {ns.sim_time():.1f}: {self.name}: starts.")
        self._schedule_now(ControllerEntity._init_new_ts_evtype)

def network_graph_setup(length):
    graph, traffic_matrix = None, None
    
    ket_minus = ns.h1   # ns.h1 = |−⟩  = 1/√(2)*(|0⟩ − |1⟩)
    ket_plus = ns.h0    # ns.h0 = |+⟩  = 1/√(2)*(|0⟩ + |1⟩)
    ket_1_y = ns.y1     # ns.y0 = |1𝑌⟩ = 1/√(2)*(|0⟩ - 𝑖|1⟩)
    ket_0_y = ns.y0     # ns.y0 = |0𝑌⟩ = 1/√(2)*(|0⟩ + 𝑖|1⟩)
    ket_1 = ns.s1       # ns.s1 = |1⟩
    ket_0 = ns.s0       # ns.s0 = |0⟩

    if length == 2:
        graph = {
            'n1': ['n2'],
            'n2': ['n1'],
        }
        traffic_matrix = {
            1: { 'src': 'n1', 'dst': 'n2', 'data_qubit_state': ket_minus},
            2: { 'src': 'n2', 'dst': 'n1', 'data_qubit_state': ket_plus},
            3: { 'src': 'n2', 'dst': 'n1', 'data_qubit_state': ket_1_y},
            4: { 'src': 'n1', 'dst': 'n2', 'data_qubit_state': ket_0_y},
            5: { 'src': 'n1', 'dst': 'n2', 'data_qubit_state': ket_1},
            6: { 'src': 'n2', 'dst': 'n1', 'data_qubit_state': ket_0},
        }

    if length == 3:
        graph = {
            'n1': ['n2'],
            'n2': ['n1', 'n3'],
            'n3': ['n2'],
        }
        traffic_matrix = {
            1: { 'src': 'n1', 'dst': 'n3', 'data_qubit_state': ket_minus},
            2: { 'src': 'n3', 'dst': 'n1', 'data_qubit_state': ket_plus}, 
            3: { 'src': 'n1', 'dst': 'n2', 'data_qubit_state': ket_1_y},
            4: { 'src': 'n2', 'dst': 'n3', 'data_qubit_state': ket_0_y},
            5: { 'src': 'n3', 'dst': 'n2', 'data_qubit_state': ket_1},
            6: { 'src': 'n2', 'dst': 'n1', 'data_qubit_state': ket_0},
        }
    
    if length == 4:
        graph = {
            'n1': ['n2'],
            'n2': ['n1', 'n3'],
            'n3': ['n2', 'n4'],
            'n4': ['n3'],
        }
        traffic_matrix = {
            1: { 'src': 'n1', 'dst': 'n4', 'data_qubit_state': ket_minus},
            2: { 'src': 'n1', 'dst': 'n3', 'data_qubit_state': ket_plus},
            3: { 'src': 'n2', 'dst': 'n3', 'data_qubit_state': ket_1_y},
            4: { 'src': 'n3', 'dst': 'n1', 'data_qubit_state': ket_0_y},
            5: { 'src': 'n4', 'dst': 'n1', 'data_qubit_state': ket_1},
            6: { 'src': 'n4', 'dst': 'n2', 'data_qubit_state': ket_0},
        }
    
    if length == 5:
        graph = {
            'n1': ['n2'],
            'n2': ['n1', 'n3'],
            'n3': ['n2', 'n4'],
            'n4': ['n3', 'n5'],
            'n5': ['n4'],
        }
        traffic_matrix = {
            1: { 'src': 'n1', 'dst': 'n4', 'data_qubit_state': ket_minus},
            2: { 'src': 'n1', 'dst': 'n5', 'data_qubit_state': ket_plus},
            3: { 'src': 'n1', 'dst': 'n3', 'data_qubit_state': ket_1_y},
            4: { 'src': 'n1', 'dst': 'n2', 'data_qubit_state': ket_0_y},
            5: { 'src': 'n5', 'dst': 'n1', 'data_qubit_state': ket_1},
            6: { 'src': 'n4', 'dst': 'n2', 'data_qubit_state': ket_0},
        }

    return graph, traffic_matrix

def main():
    # TODO: multiple src-dst. maybe not in linear chain but still do.

    logging.basicConfig(filename='./linear-chain/linear-chain-wo-channels.log', encoding='utf-8', level=logging.DEBUG)
    logging.info(f" === start ===")
    
    ns.sim_reset()

    graph, traffic_matrix = network_graph_setup(length = config.linear_chain_length)
    
    node_entities = {}

    # create node entities:
    for n_name in graph.keys():
        node_entities[n_name] = NodeEntity(n_name, traffic_matrix, graph)
    
    # create the controller entity:
    controller = ControllerEntity(node_entities, traffic_matrix)
    
    # set the controller entity and node entites properties for the node entities:
    for n_name in graph.keys():
        node_entities[n_name].set_controller_entity(controller)
        node_entities[n_name].set_node_entitities(node_entities)


    # start node entities:
    for k in node_entities.keys():
        node_entities[k].start() # let all the nodes be ready before the controller starts the first timeslot event.

    # start the controller
    controller.start()

    # start the simulation
    run_stats = ns.sim_run()
    logging.info(f" === run stats ===")
    logging.info(run_stats)
    logging.info(f" === end ===")

if __name__ == '__main__':
    main()