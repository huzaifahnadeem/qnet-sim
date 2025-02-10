"""
TODO: add papers ref here
"""

import networkx as nx
from .. import globals
import copy
from queue import PriorityQueue

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..entities import NIS
  
def _run_yens_alg(self: 'NIS'):
    if globals.args.qpass_yen_file is not None:
        import pickle
        yenfile = open(globals.args.qpass_yen_file, 'rb') # binary mode
        self.offline_paths = pickle.load(yenfile)
        yenfile.close()
        return
    
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
            self.offline_paths[(n1, n2)] = k_shortest_paths(self.network.graph, source=n1, target=n2, k=k, weight=weight_fn)

    # # Intentionally commented this part. But may uncomment to save results into a pkl file for later use:
    # import pickle
    # data = self.offline_paths
    # pklfile_name = '/home/hun13/qnet-sim/tmp-misc-random/yenfile_5x5grid_ndefault.pkl'
    # pklfile = open(pklfile_name, 'ab') # binary mode
    # pickle.dump(data, pklfile)                    
    # pklfile.close()
    # print(f'yen file created at: {pklfile_name}')

def _run_qpass_p2_alg(self: 'NIS'):
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
                width_original = G.graph[u][v]["width"]
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
                    m += G.graph[u][v]["length"]
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
    # self.curr_sd_pairs is list of (s, d, state)
    sd_pairs_list = [(pair[0], pair[1]) for pair in self.curr_sd_pairs]
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

def pre_ts_1_tasks(self: 'NIS'):
    ''' Any tasks that need to be done before the first time slot go here
    '''
    _run_yens_alg(self)

def p1():
    pass

def p2(self):
    pass

def p3():
    pass

def p4():
    # QPASS P4 alg:
    # Inputs: S-D pairs from P1, Major Path list from P2, Recovery Path list from P2, k-hop link states of this node from P3
    # 
    # for path in major_paths:
    #   h = len(path) - 1 # num of hops in the path
    #   k = globals.args.p3_hop
    #   num_of_segments = utils.ceildiv(h, k+1)
    #   len_of_a_segment = k+1
    #   segments = calc_segments(path)
    #   for s in segments:
    #       for node in s:
    #           if node != self.name:
    #               continue
    #           seg_start_node = s[0]
    #           seg_end_node = s[-1]
    #           connect(seg_start_node, seg_end_node, s, link_state)
    #
    #
    pass