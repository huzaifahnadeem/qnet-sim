"""
TODO: add papers ref here
"""

import copy
import networkx as nx
from .. import globals

from . import _slmp_common

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..entities import NodeEntity

paths_found_already = {}

# This function is here and is not a property of entities (like it was previously) because of the fact that nx.shortest_path() returns any of the shortest paths and when this function was running seperately on each node entity, the results were inconsistent across nodes. So now the first time it is called, it caches the result and uses that later on.
def find_paths(links_graph: nx.MultiGraph, sd_pairs):
    # use cached result if it exists
    if tuple(sd_pairs) in paths_found_already.keys():
        return paths_found_already[tuple(sd_pairs)]
    
    G = copy.deepcopy(links_graph)
    paths = []
    
    for s, d in sd_pairs:
        try:
            p = nx.shortest_path(G, source=s, target=d, weight='length')
            # nx only returns the nodes in the node -- no matter if the graph is nx.Graph or ns.MultiGraph
            # but since for this codebase, we assume that any parallel edges are not separate edges per se but rather just a channel in the connection (and hence equal in length and all properties)
            # so we can just pick an arbitrary edge between the two given nodes, remove that from the graph and move from there.
            path_edges = [(p[i-1], p[i]) for i in range(1, len(p))]
            path_edges_w_channel_nums = []
            path_edges_w_nx_edge_keys = []
            for u, v in path_edges:
                e_data = G.get_edge_data(u, v)
                path_edges_w_channel_nums.append((u, v, e_data[list(e_data.keys())[0]]['channel_num']))   # arbitrarily pick first key (index 0) -- lengths are all the same so arbitrary is ok
                path_edges_w_nx_edge_keys.append((u, v, list(e_data.keys())[0]))                          # arbitrarily pick first key (index 0) -- lengths are all the same so arbitrary is ok
            path_obj = _slmp_common.RoutingPath(path_edges_w_channel_nums)
            paths.append(path_obj)
            G.remove_edges_from(path_edges_w_nx_edge_keys)
        except nx.NetworkXNoPath: # no path possible
            pass
        except nx.NodeNotFound: # if src/dst is not able to make link to any node
            pass
    
    paths_found_already[tuple(sd_pairs)] = paths # cache the result
    return paths

def pre_ts_1_tasks():
    ''' Any tasks that need to be done before the first time slot go here
    '''
    pass # nothing has to be done before ts 1

def p1():
    pass

def p2(this_node_entity: 'NodeEntity'):
    _slmp_common.p2(this_node_entity)

def p3(this_node_entity: 'NodeEntity'):
    this_node_entity._gen_final_link_state() # see which ebits to use. discard one of the ebits where both side were success

    # TODO: maybe. Add an option to send through the internet/NIS (larger delays, uncertain delays etc)
    # To send directly through neighbours, create a message and send it to next neighbour in the shortest path who forwards it further. All nodes know the topology. Also, might want to add that drop any message from an earlier ts.
    
    for k_neighbour in this_node_entity.k_hop_neighbours:
        send_through_node = this_node_entity.network.get_node(k_neighbour.path_to[1]).entity
        msg_packet = this_node_entity._gen_message_packet(msg_type=globals.MSG_TYPE.link_state, src_name=this_node_entity.name, dst_name=k_neighbour.name, path=k_neighbour.path_to, curr_ts=this_node_entity.curr_ts, link_state=this_node_entity.link_state)
        
        this_node_entity.send_message(send_through_node.name, msg_packet)
    
    # TODO: Sending to next hop on path right now. maybe an option for sending via internet/NIS or whatever should be implemented

def p4(this_node_entity: 'NodeEntity'):
    links_graph = this_node_entity._gen_links_graph(this_node_entity.network.graph, this_node_entity.neighbours_link_state)
    sd_pairs = this_node_entity.sd_pairs
    # print(f"sd pairs: {sd_pairs}")
    paths = find_paths(links_graph, sd_pairs)
    role_for_path = this_node_entity._role(paths)
    ROLES = globals.ROLES
    for i in range(len(paths)):
        role = role_for_path[i]
        if role in [ROLES.REPEATER, ROLES.DESTINATION]:
            prev_node_name = paths[i][paths[i].index(this_node_entity.name) - 1]
            src_name = paths[i][0]
            dst_name = paths[i][-1]
            serving_pair = (src_name, dst_name)
            if prev_node_name == src_name: # then this node is the first repeater on the path
                # this node is the first repeater on the path
                if role is not ROLES.DESTINATION: # if this node is dest and prev node on path is source then already have e2e ebits. handled that later
                    this_node_entity._swap(serving_pair, paths[i])
                else: # case when src and dst are neighbours 
                    this_node_entity._send_e2e_ready_message(serving_pair, paths[i])
        else:
            # nothing to do for this path role is ROLES.NO_TASK
            pass