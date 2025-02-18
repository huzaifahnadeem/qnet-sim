"""
TODO: add papers ref here
"""

import networkx as nx
from math import sqrt
import random
from . import _slmp_common
from .. import globals

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..entities import NodeEntity

def pre_ts_1_tasks():
    ''' Any tasks that need to be done before the first time slot go here
    '''
    pass # nothing has to be done before ts 1


def calc_dist(node_entity: 'NodeEntity', node1, node2, method="shortest_path_length"):
    # method = "L1" # TODO: parameterize method (L1 norm/ L2 norm/ something else)
    # method = "L2"
    # method = "shortest_path_length" 
    # TODO: other than `method = "shortest_path_length"`` this is hardcodded for 4x4 grid right now
    def delta_x(n1, n2):
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

    def delta_y(n1, n2):
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

    if method == 'L2':
        return sqrt((delta_x(node1, node2)**2) + (delta_y(node1, node2)**2))
    if method == 'L1':
        return delta_x(node1, node2) + delta_y(node1, node2)
    if method == "shortest_path_length": # not in the paper. just adding it because why not
        return nx.shortest_path_length(node_entity.network.graph, source=node1, target=node2)


def p1():
    pass

def p2(this_node_entity: 'NodeEntity'):
    _slmp_common.p2(this_node_entity)

def p3():
    pass

def p4(this_node_entity: 'NodeEntity'):
    random.seed(globals.args.seed)
    sd_pairs = this_node_entity.sd_pairs
    # print(f"sd pairs: {sd_pairs}")

    for pair_num in range((len(sd_pairs))):
        src = sd_pairs[pair_num][0]
        dst = sd_pairs[pair_num][1]
        
        if this_node_entity.name not in [src, dst]: # src and dst dont do these swaps
            linked_n_nodes = set() # neighbour nodes that you have links with
            for link in this_node_entity.link_state:
                node1, node2 = link
                neighbour_node = node1 if node1 != this_node_entity.name else node2
                for channel_num in this_node_entity.link_state[link].keys():
                    if this_node_entity.link_state[link][channel_num] == True:
                        linked_n_nodes.add((neighbour_node, channel_num))
            linked_n_nodes = list(linked_n_nodes)
            
            # lists to store distance of a linked neighbour to src/dst:
            d_src = []
            d_dst = []

            for n, chann_num in linked_n_nodes:
                d_src.append(((n, chann_num), calc_dist(this_node_entity, n, src)))
                d_dst.append(((n, chann_num), calc_dist(this_node_entity, n, dst)))
            
            # in the paper, if two neighbours have same d_src and d_dst then one of them is chosen randomly. To add this aspect, we just shuffle the list so any nodes of equal length can be in any order and the sorting alg will order them arbitrarily.
            random.shuffle(d_src)
            random.shuffle(d_dst)
            d_src.sort(key=lambda elem: elem[1]) 
            d_dst.sort(key=lambda elem: elem[1])

            # local strategy part:
            if len(linked_n_nodes) <= 1: # if you dont have at least 2 linked neighbours then you cant swap.
                pass # nothing can be done
            else:
                # find the pair of best 2 neighbours (closest to src and dst). and swap them. move on to next 2 and so on. stop if <= 1 neighbours left
                while True: # TODO: if you have multiple links with the same neighbour then this is probably not as straightforward.
                    try:
                        (closest_to_src, _), d0_src = d_src[0]
                        (closest_to_dst, _), d0_dst = d_dst[0]

                        if closest_to_src == closest_to_dst: # then look at next best d_src and d_dst such that the chosen 2 nodes' sum of d_src and d_dst is minimum among the possibilities
                            _, d1_src = d_src[1]
                            _, d1_dst = d_dst[1]
                            # closest_to_dst, _ = d_dst.pop(1)
                            if (d0_src + d1_dst) < (d0_dst + d1_src):
                                chosen_src_side_idx = 0
                                chosen_dst_side_idx = 1
                            else:
                                chosen_src_side_idx = 1
                                chosen_dst_side_idx = 0
                        else:
                            chosen_src_side_idx = 0
                            chosen_dst_side_idx = 0

                        # pop from the lists the nodes that are selected
                        (closest_to_src, closest_to_src_chann_num), _ = d_src.pop(chosen_src_side_idx)
                        (closest_to_dst, closest_to_dst_chann_num), _ = d_dst.pop(chosen_dst_side_idx)

                        # remove from the other list too
                        d_src = [x for x in d_src if x[0][0] != closest_to_dst]
                        d_dst = [x for x in d_dst if x[0][0] != closest_to_src]
                        
                        # print(f" sim_time = {ns.sim_time():.1f}: {this_node_entity.name} is swapping for [{closest_to_src}, {this_node_entity.name}, {closest_to_dst}]")
                        serving_pair = (src, dst)
                        # path = [closest_to_src, this_node_entity.name, closest_to_dst]
                        edge_path = [(closest_to_src, this_node_entity.name, closest_to_src_chann_num), (this_node_entity.name, closest_to_dst, closest_to_dst_chann_num)]
                        path = _slmp_common.RoutingPath(edge_path)
                        this_node_entity._swap(serving_pair, path)
                    except IndexError:
                        break # we get there when are no more pairs to be made
