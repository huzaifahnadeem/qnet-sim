import argparse
import netsquid as ns
import random 
import globals

def apply_args() -> None:
    # seed:
    ns.set_random_state(seed=globals.args.seed)
    random.seed(globals.args.seed)

def get_args() -> None:
    parser = argparse.ArgumentParser(description="Quantum Entanglement Routing Algorithms Implementation with Netsquid.")

    config = globals.Defaults # TODO: add option to use a config file (would contain a class with properties exactly like globals.Default class)

    parser.add_argument('--seed', required=False, default=config.seed, type=int, help=f'The integer to use as the seed value for the netsquid and random libraries. Default set to {config.seed}.c')
    parser.add_argument('--network', required=False, default=config.network_toplogy, choices=[nt.name.lower() for nt in globals.NET_TOPOLOGY], help=f'The network topology to use. Default set to {config.network_toplogy}.')
    parser.add_argument('--alg', required=False, default=config.algorithm, choices=[a.value for a in globals.ALGS], help=f'Choice between SLMPg, SLMPl, QPASS, and QCAST. Default set to {config.algorithm}.')
    parser.add_argument('--num_ts', required=False, default=config.num_ts, type=int, help=f'The total number of timeslots to run for. Default set to {config.num_ts}')
    parser.add_argument('--yen_n', required=False, default=config.yen_n, type=int, help=f'The starting number of offline paths to compute with yen\'s algorithm. Default set to {config.yen_n}.')
    parser.add_argument('--yen_metric', required=False, default=config.yen_metric, choices=[a.value for a in globals.YEN_METRICS], help=f'The metric to use to compute path length in yen\'s algorithm. Default set to "{config.yen_metric.value}".')
    parser.add_argument('--p3_hop', required=False, default=config.p3_hop, type=int, help=f'In phase 3 exchange link state to this many hop away neighbours. Default set to {config.p3_hop}.')
    parser.add_argument('--max_sd', required=False, default=config.max_sd_pairs_per_ts, type=int, help=f'Max number of S-D pairs in each timeslot (inclusive). Default set to {config.max_sd_pairs_per_ts}.')
    parser.add_argument('--min_sd', required=False, default=config.min_sd_pairs_per_ts, type=int, help=f'Min number of S-D pairs in each timeslot (inclusive). Default set to {config.min_sd_pairs_per_ts}.')
    parser.add_argument('--p2_nc', required=False, default=config.p2_nc, type=int, help=f'During P2, each channel can make a number nc of attempts, nc >= 1, until a link is built of timeout. Default set to {config.p2_nc}.')
    parser.add_argument('--two_sided_epr', required=False, default=config.two_sided_epr, type=bool, help=f'If True, both nodes of an edge attempt to establish entanglement. If both sides\' ebit gets across the channel successfully then ebit from the node with the larger ID is used. If False, only the node with the larger ID sends the ebit. Default set to {config.two_sided_epr}.')
    parser.add_argument('--link_establish_timeout', required=False, default=config.link_establish_timeout, type=int, help=f'During establishment of links in phase 2, what time interval to use for timeouts (i.e. if havent received the ebit by time timeout then consider it lost). Default set to {config.link_establish_timeout}.')
    parser.add_argument('--length', required=False, default=config.length, type=int, help=f'Used for any edge that does not have its length specified. Unit = km. Default set to {config.length} km.')
    parser.add_argument('--width', required=False, default=config.width, type=int, help=f'Used for any edge that does not have its width specified. Default set to {config.width}.')
    # TODO: args for probs p and q. there should be an option to use the same p or q probs for each edge, internal link or separate values defined based on a function (like slmp mentions to be possible) or maybe a dict or something.

    parser.add_argument('--error_model', required=False, default=config.error_model, type=str, help=f'')
    parser.add_argument('--error_param', required=False, default=config.error_param, type=float, help=f'')
    parser.add_argument('--error_time_independent', required=False, default=config.error_time_independent, type=str, help=f'')
    globals.args = parser.parse_args()
    args_range_check()
    
def args_range_check():
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