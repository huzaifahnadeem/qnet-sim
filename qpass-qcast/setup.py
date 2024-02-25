import argparse
import netsquid as ns

import globals

def apply_args() -> None:
    # seed:
    ns.set_random_state(seed=globals.args.seed)
    # random.seed(globals.args.seed)

def get_args() -> None:
    parser = argparse.ArgumentParser(description="QPASS + QCAST Entanglement Routing Algorithms Implementation with Netsquid")

    parser.add_argument('-s', '--seed', required=False, default=globals.Defaults.seed, type=int, help='The integer to use as the seed value for the netsquid and random libraries')
    parser.add_argument('-n', '--net_top', required=False, default=globals.Defaults.network_toplogy, choices=[nt.value for nt in globals.NET_TOPOLOGY], help='The network topology to use')
    parser.add_argument('-a', '--alg', required=False, default=globals.Defaults.algorithm, choices=[a.value for a in globals.ALGS], help='Choice between QPASS and QCAST')
    parser.add_argument('-t', '--num_ts', required=False, default=globals.Defaults.num_ts, type=int, help='The total number of timeslots to run for')
    parser.add_argument('-y', '--yen_n', required=False, default=globals.Defaults.yen_n, type=int, help='The starting number of offline paths to compute with yen\'s algorithm.')
    parser.add_argument('-y', '--yen_metric', required=False, default=globals.Defaults.yen_metric, choices=[a.value for a in globals.YEN_METRICS], help='The metric to use to compute path length in yen\'s algorithm.')

    globals.args = parser.parse_args()