'''
This file is supposed to contain all the global variable
'''
from _enums import *

args = None # This is placeholder for the arguments object returned by arg parser

class Defaults: # The default values to use as arguments
    seed = 0
    network_toplogy = NET_TOPOLOGY.SLMP_GRID_4x4
    algorithm = ALGS.QPASS
    num_ts = 10
    yen_n = 25 # the paper has this fixed as 25
    yen_metric = YEN_METRICS.CR # CR performs slightly better than the others in the paper so sticking with this one