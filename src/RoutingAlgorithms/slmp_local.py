"""
TODO: add papers ref here
"""

from . import _slmp_common

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..entities import NodeEntity

def pre_ts_1_tasks():
    ''' Any tasks that need to be done before the first time slot go here
    '''
    pass # nothing has to be done before ts 1

def p1():
    pass

def p2(this_node_entity: 'NodeEntity'):
    _slmp_common.p2(this_node_entity)

def p3():
    pass

def p4(this_node_entity: 'NodeEntity'):
    sd_pairs = this_node_entity.sd_pairs
    # print(f"sd pairs: {sd_pairs}")

    for pair_num in range((len(sd_pairs))):
        src = sd_pairs[pair_num][0]
        dst = sd_pairs[pair_num][1]
        
        if this_node_entity.name not in [src, dst]: # src and dst dont do these swaps
            linked_n_nodes = set() # neighbour nodes that you have links with
            for link in this_node_entity.link_state['final']:
                node1, node2, _ = link
                linked_n_nodes.add(node1)
                linked_n_nodes.add(node2)
            linked_n_nodes = list(linked_n_nodes)
            linked_n_nodes.remove(this_node_entity.name) # the way ive done it, the list would also contain this_node_entity.name. remove it.
            
            # lists to store distance of a linked neighbour to src/dst:
            d_src = []
            d_dst = []

            for n in linked_n_nodes:
                d_src.append((n, this_node_entity._slmpl_calc_dist(n, src)))
                d_dst.append((n, this_node_entity._slmpl_calc_dist(n, dst)))
            
            d_src.sort(key=lambda elem: elem[1]) # in the paper, if two neighbours have same d_src and d_dst then an unbiased coin toss is used to select one. That aspect is missing here since same values are sorted in some other order. TODO: take a look later
            d_dst.sort(key=lambda elem: elem[1])

            # local strategy part:
            if len(linked_n_nodes) <= 1: # if you dont have at least 2 linked neighbours then you cant swap.
                pass # nothing can be done
            else:
                # find the pair of best 2 neighbours (closest to src and dst). and swap them. move on to next 2 and so on. stop if <= 1 neighbours left
                while True: # TODO: if you have multiple links with the same neighbour then this is probably not as straightforward.
                    try:
                        closest_to_src, d0_src = d_src[0]
                        closest_to_dst, d0_dst = d_dst[0]

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
                        closest_to_src, _ = d_src.pop(chosen_src_side_idx)
                        closest_to_dst, _ = d_dst.pop(chosen_dst_side_idx)

                        # remove from the other list too
                        d_src = [x for x in d_src if x[0] != closest_to_dst]
                        d_dst = [x for x in d_dst if x[0] != closest_to_src]
                        
                        # print(f" sim_time = {ns.sim_time():.1f}: {this_node_entity.name} is swapping for [{closest_to_src}, {this_node_entity.name}, {closest_to_dst}]")
                        serving_pair = (src, dst)
                        path = [closest_to_src, this_node_entity.name, closest_to_dst]
                        this_node_entity._swap(serving_pair, path)
                    except IndexError:
                        break # we get there when are no more pairs to be made
