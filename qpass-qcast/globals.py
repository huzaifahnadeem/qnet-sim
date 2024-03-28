'''
This file is supposed to contain all the global variable
'''
from _enums import *

args = None # This is placeholder for the arguments object returned by arg parser

class Defaults: # The default values to use as arguments
    seed = 0 # seed for both ns and random
    network_toplogy = NET_TOPOLOGY.SLMP_GRID_4x4
    algorithm = ALGS.QPASS
    num_ts = 10
    yen_n = 25 # the paper has this fixed as 25
    # yen_metric = YEN_METRICS.CR # CR performs slightly better than the others in the paper so sticking with this one
    yen_metric = YEN_METRICS.SUMDIST # for now. probably should use CR since that is the one paper chooses to go with.
    p3_hop = 1
    max_sd_pairs_per_ts = 5
    min_sd_pairs_per_ts = 0
    p2_nc = 1
    two_sided_epr = True
    link_establish_timeout = 10 # arbitrary for now