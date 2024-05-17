import netsquid as ns
import random 
import numpy
import globals
import args
import quantum

def apply_args() -> None:
    # seed:
    seed = globals.args.seed
    ns.set_random_state(seed=seed)
    random.seed(seed)
    ns.util.simtools.set_random_state(seed)
    numpy.random.seed(seed) # used internally by networkx (maybe netsquid too but not sure)
    quantum.octave.randn('state', seed) # setting the seed for octave's random number generator. # Note that randPsi uses randU which uses randn so need to set seed ('state') for randn. setting the seed for rand does nothing. If other functions are used then make sure the appropriate internal function's seed is set

def get_args() -> None:
    args.get_args()
    args.args_range_check()
    args.args_value_check()