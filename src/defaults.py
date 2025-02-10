
from src._enums import *
import os

# TODO: maybe have categories (as subclasses) for the variables?

class Defaults: # The default values to use as arguments
    results_dir = f'{os.path.dirname(os.path.realpath(__file__))}/../experiments-results/'

    traffic_matrix = TRAFFIC_MATRIX_CHOICES.random
    tm_file = None
    
    seed = 1 # same seed is used wherever there is a possibility to use a seed. unless mentioned otherwise
    network_toplogy = NET_TOPOLOGY.GRID_2D
    network_file = '' # '' or None will both return the same error
    er_seed = 0 # the seed to use when generating Erdős–Rényi model graphs (--network=er_50_01 or --network=er_50_005)
    qubit_capacity = 0 # the default qubit capacity for a node. If set to 0 then degree of node = its qubit capacity
    grid_dim = 4
    algorithm = ALGS.SLMPG
    num_ts = 5
    ts_length = 10000
    yen_n = 25 # the paper has this fixed as 25
    # yen_metric = YEN_METRICS.CR # CR performs slightly better than the others in the paper so sticking with this one
    yen_metric = YEN_METRICS.SUMDIST # for now. probably should use CR since that is the one paper chooses to go with.
    p3_hop = 1
    max_sd_pairs_per_ts = 10
    min_sd_pairs_per_ts = 1
    single_entanglement_flow_mode = True
    src_set = [] # empty list => all nodes
    dst_set = [] # empty list => all nodes
    x_dist_gte = -1
    x_dist_lte = -1
    y_dist_gte = -1
    y_dist_lte = -1
    p2_nc = 1
    two_sided_epr = True
    link_establish_timeout = 10 # arbitrary for now
    length = 1 # kilometers      # for any edge that does not have its length specified
    width = 1                    # for any edge that does not have its width specified
    scale_length = 1

    p1_delay = 1
    p2_delay = 100 # p2 also has a timeout delay (args.link_establish_timeout). Overall delay in p2 is p2_delay + args.link_establish_timeout
    p3_delay = 100
    p4_delay = 1

    qc_noise_model = QCHANNEL_NOISE_MODEL.none
    qc_noise_rate = 0.0
    qc_noise_is_time_independent = True
    qc_noise_t1 = 0
    qc_noise_t2 = 0

    qc_loss_model = QCHANNEL_LOSS_MODEL.none
    qc_p_loss_init = 0.0
    qc_p_loss_length = 0.0

    # delay model params for quantum channels
    qc_delay_model = CHANNEL_DELAY_MODEL.none # Need to be careful about the delays since if it is too much then the node will assume that it didnt get it. (TODO: parameterize this timeout)
    qc_delay_fixed = 0 # only used for fixed delay model
    qc_delay_mean = 0 # only used for gaussian delay model
    qc_delay_std = 0 # only used for gaussian delay model
    qc_delay_photon_speed = 200000 # in km/s. 200000 km/s is the default set by netsquid

    # delay model params for classical channels
    cc_delay_model = CHANNEL_DELAY_MODEL.none # using fixed model by default with delay = 1 ms. QPASS paper says that classical communications in such networks take around ~1 ms so using this value.
    cc_delay_fixed = 0 # only used for fixed delay model
    cc_delay_mean = 0 # only used for gaussian delay model
    cc_delay_std = 0 # only used for gaussian delay model
    cc_delay_photon_speed = 200000 # in km/s. 200000 km/s is the default set by netsquid

    cc_loss_model = CCHANNEL_LOSS_MODEL.none
    cc_loss_prob = 0.0

    prob_swap_loss = 0.0 # the 'q' param

    qm_noise_model = QMEM_NOISE_MODEL.none
    qm_noise_rate = 0
    qm_noise_time_independent = True

    use_quantinf_data_state = False