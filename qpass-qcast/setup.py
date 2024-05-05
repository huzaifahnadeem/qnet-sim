import netsquid as ns
import random 
import numpy
import globals
import args

def apply_args() -> None:
    # seed:
    ns.set_random_state(seed=globals.args.seed)
    random.seed(globals.args.seed)
    ns.util.simtools.set_random_state(globals.args.seed)
    numpy.random.seed(globals.args.seed) # used internally by networkx (maybe netsquid too but not sure)

def get_args() -> None:
    args._args()
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