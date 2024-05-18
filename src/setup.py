import netsquid as ns
import random 
import numpy
import globals
import args
import quantum
import importlib
import os

def apply_args() -> None:
    # import oct2py if needed (its v slow to import and use it so only import if needed)
    if globals.args.use_quantinf_data_state:
        quantum.oct2py = importlib.import_module("oct2py", package=None) # oct2py allows calling octave/matlab functions in python (octave needs to be installed in the system to use)
        quantum.octave = quantum.oct2py.octave
        lib_path = f'{os.path.dirname(os.path.realpath(__file__))}/lib/quantinf/'
        quantum.octave.addpath(lib_path)

    # setting seeds:
    seed = globals.args.seed
    ns.set_random_state(seed=seed)
    random.seed(seed)
    ns.util.simtools.set_random_state(seed)
    numpy.random.seed(seed) # used internally by networkx (maybe netsquid too but not sure)
    if quantum.octave is not None: # set seed if the library is imported
        quantum.octave.randn('state', seed) # setting the seed for octave's random number generator. # Note that randPsi uses randU which uses randn so need to set seed ('state') for randn. setting the seed for rand does nothing. If other functions are used then make sure the appropriate internal function's seed is set

def get_args() -> None:
    args.get_args()
    args.args_range_check()
    args.args_value_check()