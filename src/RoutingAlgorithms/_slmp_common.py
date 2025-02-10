
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..entities import NodeEntity

def p2(this_node_entity: 'NodeEntity'):
    this_node_entity.curr_qubit_channel_assignment = {} # key = memory index for the qubit. value = num corresponding to channels (starts at 0)
    # in slmp, all nodes attempt to establish links with each of their neighbours:
    qubit_mem_index = -1
    for neighbour in this_node_entity.imm_neighbours:
        u = this_node_entity.name
        v = neighbour.name
        uv_width = this_node_entity.network.graph.edges[u, v]['width']
        for w in range(uv_width):
            qubit_mem_index += 1
            this_node_entity.curr_qubit_channel_assignment[qubit_mem_index] = (neighbour.name, w)