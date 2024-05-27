import argparse
import globals
import json
import utils
import sys

def get_args(): # TODO: bug fix: using the --help flag only prints help for --config_file and not others. This is probably because that is added first and then we parse_known_args and then add others.
    parser = argparse.ArgumentParser(description="Quantum Entanglement Routing Algorithms Implementation with Netsquid.", add_help=False) # reason for implementing help functionality by myself: due to how config file param is set. calling --help only prints its help and not for the others.
    config = globals.Defaults
    help_case = False

    # check for --help:
    parser.add_argument('-h', '--help', action='store_true', dest='help', help='show this help message and exit')
    known_args = parser.parse_known_args()
    if known_args[0].help:
        help_case = True

    # check if the following arg was used. If it was, then read this json file and update config object properties using whatever is in the json file. Whatever is not defined is kept from globals.Defaults
    parser.add_argument('--config_file', required=False, default=None, type=str, help=f'This argument can be used to specify a configuration file (a json file) to be used for any arguments not explicitly passed. If an argument is passed then that value would be used. If not, then if that argument\'s value was specified in the json configuration file, that value would be used. If neither done for an argument, then values from \'./defaults.py\' are used. Usage: --config_file=/path/to/filename.json. Json format: use curly brackets to make a dictionary and add variables as its keys and define the values as values for this key. Check \'./sample_config.json\' for an example.')
    config_file_check = parser.parse_known_args()
    if config_file_check[0].config_file is not None:
        file_name = config_file_check[0].config_file
        with open(file_name) as conf_file:
            utils.parse_json_config(config, json.loads(conf_file.read())) # the util function overwrites all the variables in the config object and leaves the rest as they are

    # args for results:
    parser.add_argument('--results_dir', required=False, default=config.results_dir, type=str, help=f'The result file will be saved into this directory. The filename is specified by the --results_file parameter. Default set to {config.results_dir}')
    parser.add_argument('--results_file', required=False, default='', type=str, help=f'The results of the experiment will be saved into this file with this name in the directory specified by the --results_dir parameter. If this param is not used then a file with a unique name is created and saved into the aforementioned directory.')
    parser.add_argument('--seed', required=False, default=config.seed, type=int, help=f'The integer to use as the seed value for the netsquid and random libraries. Default set to {config.seed}.')
    
    # args for sim set up:
    parser.add_argument('--num_ts', required=False, default=config.num_ts, type=int, help=f'The total number of timeslots to run for. Default set to {config.num_ts}')
    parser.add_argument('--ts_length', required=False, default=config.ts_length, type=int, help=f'How long each timeslot is in terms of simulation instants. Default set to {config.ts_length}')
    parser.add_argument('--p2_nc', required=False, default=config.p2_nc, type=int, help=f'During P2, each channel can make a number nc of attempts, nc >= 1, until a link is built of timeout. Default set to {config.p2_nc}.')
    parser.add_argument('--two_sided_epr', required=False, default=config.two_sided_epr, type=bool, help=f'If True, both nodes of an edge attempt to establish entanglement. If both sides\' ebit gets across the channel successfully then ebit from the node with the larger ID is used. If False, only the node with the larger ID sends the ebit. Default set to {config.two_sided_epr}.')
    parser.add_argument('--link_establish_timeout', required=False, default=config.link_establish_timeout, type=int, help=f'During establishment of links in phase 2, what time interval to use for timeouts (i.e. if havent received the ebit by time timeout then consider it lost). Default set to {config.link_establish_timeout}.')

    # args for traffic matrix:
    parser.add_argument('--traffic_matrix', required=False, default=config.traffic_matrix, type=globals.TRAFFIC_MATRIX_CHOICES, action=globals.EnumInParamAction, help=f'How to generate the traffic matrix. Options: {[x.name for x in globals.TRAFFIC_MATRIX_CHOICES]}.')
    parser.add_argument('--max_sd', required=False, default=config.max_sd_pairs_per_ts, type=int, help=f'Max number of S-D pairs in each timeslot (inclusive). Default set to {config.max_sd_pairs_per_ts}.')
    parser.add_argument('--min_sd', required=False, default=config.min_sd_pairs_per_ts, type=int, help=f'Min number of S-D pairs in each timeslot (inclusive). Default set to {config.min_sd_pairs_per_ts}.')
    parser.add_argument('--src_set', required=False, default=config.src_set, type=str, nargs='*', help=f'Source nodes would be selected randomly from this set. Usage: "... --src_set node1 node2 node3". Leaving empty means all nodes can be used. Default set to {config.src_set}.')
    parser.add_argument('--dst_set', required=False, default=config.dst_set, type=str, nargs='*', help=f'Destination nodes would be selected randomly from this set. Usage: "... --dst_set node1 node2 node3". Leaving empty means all nodes can be used. Default set to {config.src_set}.')
    parser.add_argument('--x_dist_gte', required=False, default=config.x_dist_gte, type=int, help=f'Will force the src-dst pair to have an x-dist of >= this value. Only works for grid topology with random traffic matrix.')
    parser.add_argument('--y_dist_gte', required=False, default=config.y_dist_gte, type=int, help=f'Will force the src-dst pair to have a  y-dist of >= this value. Only works for grid topology with random traffic matrix.')
    parser.add_argument('--x_dist_lte', required=False, default=config.x_dist_lte, type=int, help=f'Will force the src-dst pair to have an x-dist of <= this value. Only works for grid topology with random traffic matrix.')
    parser.add_argument('--y_dist_lte', required=False, default=config.y_dist_lte, type=int, help=f'Will force the src-dst pair to have a  y-dist of <= this value. Only works for grid topology with random traffic matrix.')
    
    # args for connections models:
    parser.add_argument('--qc_noise_model', required=False, default=config.qc_noise_model, type=globals.QCHANNEL_NOISE_MODEL, action=globals.EnumInParamAction, help=f'This is the noise model to use for quantum channels. Options: {[x.name for x in globals.QCHANNEL_NOISE_MODEL]}')
    parser.add_argument('--qc_noise_rate', required=False, default=config.qc_noise_rate, type=float, help=f'The parameter (rate) to be used with dephase and depolar noise models.')
    parser.add_argument('--qc_noise_t1', required=False, default=config.qc_noise_t1, type=float, help=f'The "T1" parameter for the T1T2 noise model')
    parser.add_argument('--qc_noise_t2', required=False, default=config.qc_noise_t2, type=float, help=f'The "T2" parameter for the T1T2 noise model')
    parser.add_argument('--qc_noise_time_independent', required=False, action='store_true', help=f'If this argument used then the --qc_noise_model is time independent and --qc_noise_rate is the probability to be used with the model.')
    parser.add_argument('--qc_noise_time_dependent', dest='--qc_noise_time_independent', action='store_false', help=f'If this argument used then the --qc_noise_model is time dependent and --qc_noise_rate, in Hz, is to be used with the model.')
    parser.set_defaults(qc_noise_time_independent=config.qc_noise_is_time_independent)
    parser.add_argument('--qc_loss_model', required=False, default=config.qc_loss_model, type=globals.QCHANNEL_LOSS_MODEL, action=globals.EnumInParamAction, help=f'This is the loss model to use for quantum channels. Options: {[x.name for x in globals.QCHANNEL_LOSS_MODEL]}')
    parser.add_argument('--qc_p_loss_init', required=False, default=config.qc_p_loss_init, type=float, help=f'The probability of losing the qubit as it enters the channel. Only used with --qc_loss_model=fibre and as the fixed probability of loss "p" in --qc_loss_model=fixed')
    parser.add_argument('--qc_p_loss_length', required=False, default=config.qc_p_loss_length, type=float, help=f'The probability of losing the qubit over the length of the channel. Only used with --qc_loss_model=fibre')
    parser.add_argument('--qc_delay_model', required=False, default=config.qc_delay_model, type=globals.CHANNEL_DELAY_MODEL, action=globals.EnumInParamAction, help=f'This is the delay model to use for quantum channels. Options: {[x.name for x in globals.CHANNEL_DELAY_MODEL]}')
    parser.add_argument('--qc_delay_fixed', required=False, default=config.qc_delay_fixed, type=float, help=f'The fixed delay in nano seconds to use with channels. Only used with --qc_delay_model=fixed')
    parser.add_argument('--qc_delay_mean', required=False, default=config.qc_delay_mean, type=float, help=f'The mean delay in nano seconds to use with channels. Only used with --qc_delay_model=gaussian')
    parser.add_argument('--qc_delay_std', required=False, default=config.qc_delay_std, type=float, help=f'The standard deviation for delay in nano seconds to use with channels. Only used with --qc_delay_model=gaussian')
    parser.add_argument('--qc_delay_photon_speed', required=False, default=config.qc_delay_photon_speed, type=float, help=f'The speed of photons (in km/s) travelling through the channel. Only used with --qc_delay_model=fibre.')
    parser.add_argument('--cc_loss_model', required=False, default=config.cc_loss_model, type=globals.CCHANNEL_LOSS_MODEL, action=globals.EnumInParamAction, help=f'This is the loss model to use for classical channels. Options: {[x.name for x in globals.CCHANNEL_LOSS_MODEL]}')
    parser.add_argument('--cc_loss_prob', required=False, default=config.cc_loss_prob, type=float, help=f'The probability of losing a packet over a channel. Only used with --cc_loss_model=prob')
    parser.add_argument('--cc_delay_model', required=False, default=config.cc_delay_model, type=globals.CHANNEL_DELAY_MODEL, action=globals.EnumInParamAction, help=f'This is the delay model to use for classical channels. Options: {[x.name for x in globals.CHANNEL_DELAY_MODEL]}')
    parser.add_argument('--cc_delay_fixed', required=False, default=config.cc_delay_fixed, type=float, help=f'The fixed delay in micro seconds to use with channels. Only used with --cc_delay_model=fixed')
    parser.add_argument('--cc_delay_mean', required=False, default=config.cc_delay_mean, type=float, help=f'The mean delay in micro seconds to use with channels. Only used with --cc_delay_model=gaussian')
    parser.add_argument('--cc_delay_std', required=False, default=config.cc_delay_std, type=float, help=f'The standard deviation for delay in micro seconds to use with channels. Only used with --cc_delay_model=gaussian')
    parser.add_argument('--cc_delay_photon_speed', required=False, default=config.cc_delay_photon_speed, type=float, help=f'The speed of photons (in km/s) travelling through the channel. Only used with --cc_delay_model=fibre.')
    
    # args for qmem models:
    parser.add_argument('--qm_noise_model', required=False, default=config.qm_noise_model, type=globals.QMEM_NOISE_MODEL, action=globals.EnumInParamAction, help=f'This is the noise model to use for quantum memories. Options: {[x.name for x in globals.QMEM_NOISE_MODEL]}')
    parser.add_argument('--qm_noise_rate', required=False, default=config.qm_noise_rate, type=float, help=f'')
    parser.add_argument('--qm_noise_time_independent', required=False, action='store_true', help=f'If this argument used then the --qm_noise_model is time independent and --qm_noise_rate is the probability to be used with the model.')
    parser.add_argument('--qm_noise_time_dependent', dest='--qm_noise_time_independent', action='store_false', help=f'If this argument used then the --qm_noise_model is time dependent and --qm_noise_rate, in Hz, is to be used with the model.')
    parser.set_defaults(qm_noise_time_independent=config.qm_noise_time_independent)

    # args for network set up:
    parser.add_argument('--network', required=False, default=config.network_toplogy, type=globals.NET_TOPOLOGY, action=globals.EnumInParamAction, help=f'The network topology to use. Default set to {config.network_toplogy}.')
    parser.add_argument('--grid_dim', required=False, default=config.grid_dim, type=int, help=f'The dimension of the grid topology if using --network=grid_2d. Default set to {config.grid_dim}')
    parser.add_argument('--length', required=False, default=config.length, type=int, help=f'Used for any edge that does not have its length specified. Unit = km. Default set to {config.length} km.')
    parser.add_argument('--width', required=False, default=config.width, type=int, help=f'Used for any edge that does not have its width specified. Default set to {config.width}.')

    # args specific to SLMP:
    parser.add_argument('--single_entanglement_flow_mode', required=False, action='store_true',  help=f'If this argument used then there is only a single unique s-d pair per timeslot (e.g. to use with single entanglement flow in SLMP). The number of qubits to be sent between src and dst is dependent on the --max_sd and --min_sd arguments.')
    parser.add_argument('--not_single_entanglement_flow_mode', dest='--single_entanglement_flow_mode', action='store_false', help=f'Use this if you dont want to toggle --single_entanglement_flow_mode')
    parser.set_defaults(single_entanglement_flow_mode=config.single_entanglement_flow_mode)
    
    # args specific to QPASS:
    parser.add_argument('--yen_n', required=False, default=config.yen_n, type=int, help=f'The starting number of offline paths to compute with yen\'s algorithm. Default set to {config.yen_n}.')
    parser.add_argument('--yen_metric', required=False, default=config.yen_metric, type=globals.YEN_METRICS, action=globals.EnumInParamAction, help=f'The metric to use to compute path length in yen\'s algorithm. Default set to "{config.yen_metric.value}".')
    parser.add_argument('--p3_hop', required=False, default=config.p3_hop, type=int, help=f'In phase 3 exchange link state to this many hop away neighbours. A value of -1 is used to mean infinity. Default set to {config.p3_hop}.')

    # misc. args:
    parser.add_argument('--alg', required=False, default=config.algorithm, type=globals.ALGS, action=globals.EnumInParamAction, help=f'Choice between SLMPg, SLMPl, QPASS, and QCAST. Default set to {config.algorithm}.')
    parser.add_argument('--prob_swap_loss', required=False, default=config.prob_swap_loss, type=float, help=f'The probability that a pair of qubits would be lost when a swap operation is performed. Its the \'q\' parameter.') # TODO: eventually this will be removes and instead a noise model will be added to the PhysicalInstruction objects for the swap operation
    parser.add_argument('--use_quantinf_data_state', required=False, action='store_true', help=f'If this argument used then the randPsi function from the quantinf package is used to randomly generate each data qubit\'s state.')
    parser.add_argument('--dont_use_quantinf_data_state', dest='--use_quantinf_data_state', action='store_false', help=f'If this argument used then instead of using the randPsi function from the quantinf package, each data qubit\'s state is generated by applying a randomly generated rotation operator (random angle between [0, 2pi] radians, a random rotation axis, and randomly deciding whether or not to complex conjugate the operator) on a state randomly selected from: |−⟩, |+⟩, |1Y⟩, |0Y⟩, |1⟩, |0⟩.')
    parser.set_defaults(use_quantinf_data_state=config.use_quantinf_data_state)

    globals.args = parser.parse_args()

    if help_case:
        parser.print_help()
        sys.exit(0)

def args_range_check(): # TODO: https://gist.github.com/dmitriykovalev/2ab1aa33a8099ef2d514925d84aa89e7 provides a better way
    raise_exception = False
    if globals.args.num_ts < 1:
        raise_exception = True
        param = '--num_ts'
        sign = '>='
        limit = '1'
    elif globals.args.yen_n < 1:
        raise_exception = True
        param = '--yen_n'
        sign = '>='
        limit = '1'
    elif globals.args.p3_hop < 1:
        if globals.args.p3_hop == -1: # a special case. => infinity
            globals.args.p3_hop = float('inf')
        else:
            raise_exception = True
            param = '--p3_hop'
            sign = '>='
            limit = '1'
    elif globals.args.min_sd < 0:
        raise_exception = True
        param = '--min_sd'
        sign = '>='
        limit = '0'
    elif globals.args.p2_nc < 1:
        raise_exception = True
        param = '--p2_nc'
        sign = '>='
        limit = '1'
    elif not (globals.args.max_sd >= globals.args.min_sd):
        raise_exception = True
        param = '--max_sd'
        sign = '>='
        limit = "parameter '--min_sd'"
    elif not globals.args.link_establish_timeout >= 0:
        raise_exception = True
        param = '--link_establish_timeout'
        sign = '>='
        limit = '0'
    elif not (globals.args.prob_swap_loss >= 0 and globals.args.prob_swap_loss <= 1):
        raise_exception = True
        param = '--prob_swap_loss'
        sign = '>= 0 and <= 1'
        limit = ""
    elif not (globals.args.cc_loss_prob >= 0 and globals.args.cc_loss_prob <= 1):
        raise_exception = True
        param = '--cc_loss_prob'
        sign = '>= 0 and <= 1'
        limit = ""
    elif not (globals.args.qc_p_loss_init >= 0 and globals.args.qc_p_loss_init <= 1):
        raise_exception = True
        param = '--qc_p_loss_init'
        sign = '>= 0 and <= 1'
        limit = ""
    elif not (globals.args.qc_p_loss_length >= 0 and globals.args.qc_p_loss_length <= 1):
        raise_exception = True
        param = '--qc_p_loss_length'
        sign = '>= 0 and <= 1'
        limit = ""
    if raise_exception:
        raise ValueError(f"The input parameter '{param}' must be {sign} {limit}.")
    

def args_value_check():
    raise_exception = False
    if (globals.args.qc_delay_mean - 3*globals.args.qc_delay_std) < 0: # the 3*std comes fromt the empirical rule "approximately 99.7% of observations fall within three standard deviations of the mean"
        raise_exception = True
        param = '--qc_delay_mean, --qc_delay_std'
        error_msg = 'With the selected mean and standard dev., the delay can be a negative value.'
    elif (globals.args.cc_delay_mean - 3*globals.args.cc_delay_std) < 0:
        raise_exception = True
        param = '--cc_delay_mean, --cc_delay_std'
        error_msg = 'With the selected mean and standard dev., the delay can be a negative value.'
    if raise_exception:
        raise ValueError(f"Invalid value(s) for input parameter(s) '{param}': {error_msg}.")