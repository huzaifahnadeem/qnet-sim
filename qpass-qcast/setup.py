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
    args.get_args()
    args.args_range_check()
    args.args_value_check()