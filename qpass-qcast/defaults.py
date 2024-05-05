
from _enums import *

# TODO: maybe have categories (as subclasses) for the variables?

class Defaults: # The default values to use as arguments
    seed = 1 # same seed is used wherever there is a possibility to use a seed
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

    noise_model = QCHANNEL_NOISE_MODEL.dephase
    noise_param = 0.25
    # noise_param = 0.9
    noise_time_independent = True

    loss_model = QCHANNEL_LOSS_MODEL.fibre
    p_loss_init = 0
    p_loss_length = 0

    # delay model params for quantum channels
    qc_delay_model = CHANNEL_DELAY_MODEL.none # Need to be careful about the delays since if it is too much then the node will assume that it didnt get it. (TODO: parameterize this timeout)
    qc_delay_fixed = 0 # only used for fixed delay model
    qc_delay_mean = 0 # only used for gaussian delay model
    qc_delay_std = 0 # only used for gaussian delay model

    # delay model params for classical channels
    # Need to be careful about the delays since if it is too much then the node will assume that it didnt get it. (TODO: parameterize this timeout)
    cc_delay_model = CHANNEL_DELAY_MODEL.none # using fixed model by default with delay = 1 ms. QPASS paper says that classical communications in such networks take around ~1 ms so using this value.
    cc_delay_fixed = 1 # only used for fixed delay model
    cc_delay_mean = 0 # only used for gaussian delay model
    cc_delay_std = 0 # only used for gaussian delay model

    prob_swap_loss = 0 # the 'q' param