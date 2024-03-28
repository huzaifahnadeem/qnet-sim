# import globals
from entities import NodeEntity, NIS
import netsquid as ns

def setup():
    import setup
    
    setup.get_args()
    setup.apply_args()

def main() -> None:
    setup() 

    # basic testing
    # from network import Network
    # from network_topologies import slmp_grid_4x4
    # nw = Network()
    
    # print(nw.nodes)
    # nodes = [nw.get_node(name) for name in slmp_grid_4x4.keys()]
    # print(nodes)
    # print(nw.get_node('n3').ID)
    # print(nw.get_connection('n1', 'n2'))
    # print(nw.get_connection('n1', 'n2', label='dirConn. | n1<->n2 #3 | quantum'))
    # for conn in nw.connections.values():
    #     print(conn)
    # print(nw.offline_paths[('n2', 'n1')][0])

    #============#
    #============#
    #============#

    # network fixed for now
    from network import Network
    from network_topologies import slmp_grid_4x4
    # create network object. (entities are part of each node property in the network object)
    nw = Network()
    node_names = [n for n in nw.node_names()]

    # create the network information server / controller entity:
    nis = NIS(nw)
    nis.init_random_traffic_matrix(node_names) # also have "set_traffic_matrix" method

    # set the nis entity and node entites properties for the node entities:
    node_entities = []
    for n_name in node_names:
        n_entity = nw.get_node(n_name).entity
        n_entity.set_nis_entity(nis)
        n_entity.set_network(nw)
        node_entities.append(n_entity)

    for ne in node_entities:
        ne.start() # let all the nodes be ready before the nis starts the first timeslot event.

    # start the controller/nis
    nis.start()
    
    # u = 'n16'
    # v = 'n12'
    # classic_label = f"dirConn. | {u}<->{v} | classical"
    # # port_1, port_2 = nw.get_connected_ports(u, v, label=classic_label)
    # # node_1 = nw.get_node(u)
    # # node_2 = nw.get_node(v)
    # # node_2.ports[port_2].tx_output("Test msg1!")
    # channel = nw.get_connection(u, v, classic_label)
    # channel.send("hello world!")
    # items, delay = channel.receive()
    # print(items)


    # start the simulation
    run_stats = ns.sim_run()
    print(run_stats)

if __name__ == '__main__':
    main()