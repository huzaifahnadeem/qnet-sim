'''
This file contains the functions to import certain network topologies from saved data files on the disk as well as functions and hard-coded dictionaries that specify network topologies.
'''
import globals

# TODO: functions to import all those collected data files that specified networks. (from quantum overlay paper) + others if any

slmp_grid_4x4 = {   
                'n1': {'n2':{'length':1, 'width':3,}, 'n5':{'length':1, 'width':1,}},
                'n2': {'n3':{'length':1, 'width':1,}, 'n6':{'length':1, 'width':1,}},
                'n3': {'n7':{'length':1, 'width':1,}, 'n4':{'length':1, 'width':1,}},
                'n4': {'n8':{'length':1, 'width':1,}},

                'n5': {'n6':{'length':1, 'width':1,}, 'n9':{'length':1, 'width':1,}},
                'n6': {'n7':{'length':1, 'width':1,}, 'n10':{'length':1, 'width':1,}},
                'n7': {'n8':{'length':1, 'width':1,}, 'n11':{'length':1, 'width':1,}},
                'n8': {'n12':{'length':1, 'width':1,}},

                'n9': {'n10':{'length':1, 'width':1,}, 'n13':{'length':1, 'width':1,}},
                'n10': {'n11':{'length':1, 'width':1,}, 'n14':{'length':1, 'width':1,}},
                'n11': {'n12':{'length':1, 'width':1,}, 'n15':{'length':1, 'width':1,}},
                'n12': {'n16':{'length':1, 'width':1,}},

                'n13': {'n14':{'length':1, 'width':1,}},
                'n14': {'n15':{'length':1, 'width':1,}},
                'n15': {'n16':{'length':1, 'width':1,}},
                'n16': {}, 
            }


def network_choice() -> dict:
    network_choice = globals.args.network
    network_dict = dict()
    
    if network_choice is globals.NET_TOPOLOGY.SLMP_GRID_4x4:
        network_dict = slmp_grid_4x4
    else:
        # TODO: other choices
        raise NotImplementedError("Can only use SLMP_GRID_4x4 right now.")
    
    return network_dict