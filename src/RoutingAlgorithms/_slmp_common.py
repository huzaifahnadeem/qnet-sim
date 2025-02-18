
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..entities import NodeEntity

class RoutingPath:
    # the routing path being used in the swap process
    def __init__(self, edge_path: list) -> None:
        # edge_path = [(n1, n2, channel_num_n1_n2), (n2, n3, channel_num_n2_n3), ...]
        self.edges = edge_path
        self.nodes = self._create_node_path()
    
    def channel_num_between(self, n1, n2):
        return [self.edges[i][2] for i in range(len(self.edges)) if ((self.edges[i][0] == n1) and self.edges[i][1] == n2)][0]
    
    def _create_node_path(self) -> list:
        nodes_from_e_path = []
        # loop over the edges list
        # put start node of the edge
        # repeat until the last edge
        # for last edge, also need to add the end node of the edge in the list
        for i in range(len(self.edges)):
            e = self.edges[i]
            n = e[0]
            nodes_from_e_path.append(n)
        n_last = self.edges[-1][1]
        nodes_from_e_path.append(n_last)

        return nodes_from_e_path

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