import netsquid as ns
import pydynaa


seed = 0

ns.set_random_state(seed=seed)

network_graph_grid = {
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


def main():
    pass

if __name__ == '__main__':
    main()