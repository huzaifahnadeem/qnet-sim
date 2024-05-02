
from _enums import *

class Defaults: # The default values to use as arguments
    seed = 1 # seed for both ns and random
    network_toplogy = NET_TOPOLOGY.SLMP_GRID_4x4
    algorithm = ALGS.SLMPG
    num_ts = 1
    yen_n = 25 # the paper has this fixed as 25
    # yen_metric = YEN_METRICS.CR # CR performs slightly better than the others in the paper so sticking with this one
    yen_metric = YEN_METRICS.SUMDIST # for now. probably should use CR since that is the one paper chooses to go with.
    p3_hop = 1
    max_sd_pairs_per_ts = 1
    min_sd_pairs_per_ts = 1
    p2_nc = 1
    two_sided_epr = True
    link_establish_timeout = 10 # arbitrary for now
    length = 1 # kilometers      # for any edge that does not have its length specified
    width = 1                    # for any edge that does not have its width specified

    error_model = 'dephase'
    error_param = 0.25
    error_time_independent = 'yes'

    error_model = 'depolar'
    error_param = 0.9
    error_time_independent = 'yes'