import argparse
import globals

def get_args():
    parser = argparse.ArgumentParser(description="Quantum Entanglement Routing Algorithms Implementation with Netsquid.")

    config = globals.Defaults # TODO: add option to use a config file (would contain a class with properties exactly like globals.Default class)

    parser.add_argument('--seed', required=False, default=config.seed, type=int, help=f'The integer to use as the seed value for the netsquid and random libraries. Default set to {config.seed}.c')
    parser.add_argument('--network', required=False, default=config.network_toplogy, type=globals.NET_TOPOLOGY, action=globals.EnumInParamAction, help=f'The network topology to use. Default set to {config.network_toplogy}.')
    parser.add_argument('--alg', required=False, default=config.algorithm, type=globals.ALGS, action=globals.EnumInParamAction, help=f'Choice between SLMPg, SLMPl, QPASS, and QCAST. Default set to {config.algorithm}.')
    parser.add_argument('--num_ts', required=False, default=config.num_ts, type=int, help=f'The total number of timeslots to run for. Default set to {config.num_ts}')
    parser.add_argument('--yen_n', required=False, default=config.yen_n, type=int, help=f'The starting number of offline paths to compute with yen\'s algorithm. Default set to {config.yen_n}.')
    parser.add_argument('--yen_metric', required=False, default=config.yen_metric, type=globals.YEN_METRICS, action=globals.EnumInParamAction, help=f'The metric to use to compute path length in yen\'s algorithm. Default set to "{config.yen_metric.value}".')
    parser.add_argument('--p3_hop', required=False, default=config.p3_hop, type=int, help=f'In phase 3 exchange link state to this many hop away neighbours. Default set to {config.p3_hop}.')
    parser.add_argument('--max_sd', required=False, default=config.max_sd_pairs_per_ts, type=int, help=f'Max number of S-D pairs in each timeslot (inclusive). Default set to {config.max_sd_pairs_per_ts}.')
    parser.add_argument('--min_sd', required=False, default=config.min_sd_pairs_per_ts, type=int, help=f'Min number of S-D pairs in each timeslot (inclusive). Default set to {config.min_sd_pairs_per_ts}.')
    parser.add_argument('--p2_nc', required=False, default=config.p2_nc, type=int, help=f'During P2, each channel can make a number nc of attempts, nc >= 1, until a link is built of timeout. Default set to {config.p2_nc}.')
    parser.add_argument('--two_sided_epr', required=False, default=config.two_sided_epr, type=bool, help=f'If True, both nodes of an edge attempt to establish entanglement. If both sides\' ebit gets across the channel successfully then ebit from the node with the larger ID is used. If False, only the node with the larger ID sends the ebit. Default set to {config.two_sided_epr}.')
    parser.add_argument('--link_establish_timeout', required=False, default=config.link_establish_timeout, type=int, help=f'During establishment of links in phase 2, what time interval to use for timeouts (i.e. if havent received the ebit by time timeout then consider it lost). Default set to {config.link_establish_timeout}.')
    parser.add_argument('--length', required=False, default=config.length, type=int, help=f'Used for any edge that does not have its length specified. Unit = km. Default set to {config.length} km.')
    parser.add_argument('--width', required=False, default=config.width, type=int, help=f'Used for any edge that does not have its width specified. Default set to {config.width}.')
    parser.add_argument('--noise_model', required=False, default=config.noise_model, type=globals.QCHANNEL_NOISE_MODEL, action=globals.EnumInParamAction, help=f'This is the noise model to use for quantum channels. Options: {[x.name for x in globals.QCHANNEL_NOISE_MODEL]}')
    parser.add_argument('--noise_param', required=False, default=config.noise_param, type=float, help=f'')
    # adding pair of args for whether noise model is time independent or not. If it is independent then noise_param is probability. If not, then it is the in Hz.
    parser.add_argument('--noise_time_independent', required=False, action='store_true', help=f'If this argument used then the --noise_model is time independent and --noise_param is the probability to be used with the model.')
    parser.add_argument('--noise_time_dependent', dest='--noise_time_independent', action='store_false', help=f'If this argument used then the --noise_model is time dependent and --noise_param, in Hz, is to be used with the model.')
    parser.set_defaults(noise_time_independent=config.noise_time_independent)
    parser.add_argument('--loss_model', required=False, default=config.loss_model, type=globals.QCHANNEL_LOSS_MODEL, action=globals.EnumInParamAction, help=f'This is the loss model to use for quantum channels. Options: {[x.name for x in globals.QCHANNEL_LOSS_MODEL]}')
    parser.add_argument('--p_loss_init', required=False, default=config.p_loss_init, type=float, help=f'The probability of losing the qubit as it enters the channel. Only used with --loss_model=fibre')
    parser.add_argument('--p_loss_length', required=False, default=config.p_loss_length, type=float, help=f'The probability of losing the qubit over the length of the channel. Only used with --loss_model=fibre')
    parser.add_argument('--qc_delay_model', required=False, default=config.qc_delay_model, type=globals.CHANNEL_DELAY_MODEL, action=globals.EnumInParamAction, help=f'This is the delay model to use for quantum channels. Options: {[x.name for x in globals.CHANNEL_DELAY_MODEL]}')
    parser.add_argument('--qc_delay_fixed', required=False, default=config.qc_delay_fixed, type=float, help=f'The fixed delay in nano seconds to use with channels. Only used with --qc_delay_model=fixed')
    parser.add_argument('--qc_delay_mean', required=False, default=config.qc_delay_mean, type=float, help=f'The mean delay in nano seconds to use with channels. Only used with --qc_delay_model=gaussian')
    parser.add_argument('--qc_delay_std', required=False, default=config.qc_delay_std, type=float, help=f'The standard deviation for delay in nano seconds to use with channels. Only used with --qc_delay_model=gaussian')
    parser.add_argument('--cc_delay_model', required=False, default=config.cc_delay_model, type=globals.CHANNEL_DELAY_MODEL, action=globals.EnumInParamAction, help=f'This is the delay model to use for classical channels. Options: {[x.name for x in globals.CHANNEL_DELAY_MODEL]}')
    parser.add_argument('--cc_delay_fixed', required=False, default=config.cc_delay_fixed, type=float, help=f'The fixed delay in micro seconds to use with channels. Only used with --cc_delay_model=fixed')
    parser.add_argument('--cc_delay_mean', required=False, default=config.cc_delay_mean, type=float, help=f'The mean delay in micro seconds to use with channels. Only used with --cc_delay_model=gaussian')
    parser.add_argument('--cc_delay_std', required=False, default=config.cc_delay_std, type=float, help=f'The standard deviation for delay in micro seconds to use with channels. Only used with --cc_delay_model=gaussian')
    # TODO: arg for q probability.
    
    globals.args = parser.parse_args()

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
    if raise_exception:
        raise ValueError(f"The input parameter '{param}' must be {sign} {limit}.")