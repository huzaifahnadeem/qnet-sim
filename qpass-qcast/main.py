import globals

def setup():
    import setup
    
    setup.get_args()
    setup.apply_args()

def main() -> None:
    setup() 

    # basic testing
    from network import Network
    from network_topologies import slmp_grid_4x4
    nw = Network()
    # print(nw.nodes)
    # nodes = [nw.get_node(name) for name in slmp_grid_4x4.keys()]
    # print(nodes)
    # print(nw.get_node('n3').ID)
    # print(nw.get_connection('n1', 'n2'))
    # print(nw.get_connection('n1', 'n2', label='dirConn. | n1<->n2 #3 | quantum'))
    # for conn in nw.connections.values():
    #     print(conn)
    print(nw.offline_paths[('n2', 'n1')][0])

if __name__ == '__main__':
    main()