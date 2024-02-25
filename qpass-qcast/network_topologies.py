'''
This file contains the functions to import certain network topologies from saved data files on the disk as well as functions and hard-coded dictionaries that specify network topologies.
'''
import globals

# TODO: functions to import all those collected data files that specified networks. (from quantum overlay paper) + others if any

slmp_grid_4x4 = {   # node_u: list of tuples -- tuple = (node_v, width of edge, length)
                'n1': [('n2', 1), ('n5', 1)],
                'n2': [('n1', 1), ('n3', 1), ('n6', 1)],
                'n3': [('n2', 1), ('n7', 1), ('n4', 1)],
                'n4': [('n3', 1), ('n8', 1)],

                'n5': [('n1', 1), ('n6', 1), ('n9', 1)],
                'n6': [('n5', 1), ('n2', 1), ('n7', 1), ('n10', 1)],
                'n7': [('n6', 1), ('n3', 1), ('n8', 1), ('n11', 1)],
                'n8': [('n7', 1), ('n4', 1), ('n12', 1)],

                'n9': [('n5', 1), ('n10', 1), ('n13', 1)],
                'n10': [('n9', 1), ('n6', 1), ('n11', 1), ('n14', 1)],
                'n11': [('n10', 1), ('n7', 1), ('n12', 1), ('n15', 1)],
                'n12': [('n11', 1), ('n8', 1), ('n16', 1)],

                'n13': [('n9', 1), ('n14', 1)],
                'n14': [('n13', 1), ('n10', 1), ('n15', 1)],
                'n15': [('n14', 1), ('n11', 1), ('n16', 1)],
                'n16': [('n15', 1), ('n12', 1)], 
            }

def network_choice() -> dict:
    network_choice = globals.args.net_top
    network_dict = dict()
    
    if network_choice is globals.NET_TOPOLOGY.SLMP_GRID_4x4:
        network_dict = slmp_grid_4x4
    
    return network_dict