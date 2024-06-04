import netsquid as ns
import random
from numpy import pi
import math
import utils
import globals
# oct2py allows calling octave/matlab functions in python (octave needs to be installed in the system to use)
oct2py = None # placeholder variable for the reference to the library.
octave = None  # placeholder variable for the reference to the this module. importlib is called in setup.py which sets these two variables.

# need to install octave and oct2py first.
# oct2py: https://pypi.org/project/oct2py/
# octave: https://wiki.octave.org/Octave_for_GNU/Linux
# only need to use octave if we want to use the quantinf package (./lib/quantinf/) from https://www.dr-qubit.org/matlab.html
# Note: there maybe be an issue with oct2py/io.py file line 376. it does not import spmatrix from scipy but adding "from scipy.sparse import spmatrix" before this line or at the top of file fixes the issue

# possible states that the data qubit can start in (will apply some combination of gates later) (if --dont_use_quantinf_data_state selected)
ket_minus = ns.h1   # ns.h1 = |−⟩  = 1/√(2)*(|0⟩ − |1⟩)
ket_plus = ns.h0    # ns.h0 = |+⟩  = 1/√(2)*(|0⟩ + |1⟩)
ket_1_y = ns.y1     # ns.y0 = |1𝑌⟩ = 1/√(2)*(|0⟩ - 𝑖|1⟩)
ket_0_y = ns.y0     # ns.y0 = |0𝑌⟩ = 1/√(2)*(|0⟩ + 𝑖|1⟩)
ket_1 = ns.s1       # ns.s1 = |1⟩
ket_0 = ns.s0       # ns.s0 = |0⟩
starting_states = {
        '|−⟩': ket_minus,
        '|+⟩': ket_plus,
        '|1Y⟩': ket_1_y,
        '|0Y⟩': ket_0_y,
        '|1⟩': ket_1,
        '|0⟩': ket_0,
    }

data_qubit_states = [] # this keeps actual states in. nodes only have an index for this.
sd_pair_states = {}

def prepare_corrections(qubit_to_teleport, entangled_qubit):
        ns.qubits.operate([qubit_to_teleport, entangled_qubit], ns.CNOT)
        ns.qubits.operate(qubit_to_teleport, ns.H)
        m0, _ = ns.qubits.measure(qubit_to_teleport)
        m1, _ = ns.qubits.measure(entangled_qubit)
        return (m0, m1)

def gen_epr_pair():
    q1, q2 = ns.qubits.create_qubits(2)
    ns.qubits.operate(q1, ns.H)
    ns.qubits.operate([q1, q2], ns.CNOT)
    
    return q1, q2

def apply_corrections(ebit, corrections, original_state_idx=None):
    m0 = corrections[0]
    m1 = corrections[1]

    if m1:
        ns.qubits.operate(ebit, ns.X)
    if m0:
        ns.qubits.operate(ebit, ns.Z)
    
    # if original state provided then also returns the fidelity of it. Otherwise fidelity is just None
    if original_state_idx is not None:
        original_qubit = _generate_data_qubit(original_state_idx)
        original_state = original_qubit.qstate.qrepr
        fidelity = ns.qubits.fidelity(ebit, original_state, squared=True)
    else:
        fidelity = None
    
    return ebit, fidelity # ebit has the teleported qubit's state now

def _generate_data_qubit(state_idx):
    if not globals.args.use_quantinf_data_state: # the old way:
        start_state, operator = data_qubit_states[state_idx]
        data_qubit,  = ns.qubits.create_qubits(1, no_state=True)
        ns.qubits.assign_qstate([data_qubit], starting_states[start_state]) # assign starting state
        ns.qubits.operate(data_qubit, operator) # apply the operator
    else:
        # using quantinf random function to generate the random state for the data qubit
        state = data_qubit_states[state_idx]
        data_qubit,  = ns.qubits.create_qubits(1, no_state=True)
        ns.qubits.assign_qstate([data_qubit], state)
    
    return data_qubit

def _gen_random_state():
    if not globals.args.use_quantinf_data_state: # do the old way:
        angle = pi * random.uniform(0.0, 2.0)
        rot_axis = random.choice([(1, 0, 0), (0, 1, 0), (0, 0, 1)]) # unit vectors representing x, y, and z axes, respectively.
        do_complex_conj = random.choice([True, False])
        
        start_state = random.choice(list(starting_states.keys()))
        operator = ns.qubits.operators.create_rotation_op(angle=angle, rotation_axis=rot_axis, conjugate=do_complex_conj)
        
        next_idx = len(data_qubit_states)
        data_qubit_states.append((start_state, operator)) # saving the starting state and the operator. When generate_data_qubit() is called, it will generate a qubit and assign it this state and then apply the operator.
    else:
        # case when --use_quantinf_data_state is used
        randstate = octave.randPsi(2)
        next_idx = len(data_qubit_states)
        data_qubit_states.append(randstate)
    
    return next_idx


def new_sd_pair(sd_pair):
    global sd_pair_states
    state_idx = _gen_random_state()
    sd_pair_states.setdefault(sd_pair, []).append(state_idx)

def get_data_qubit_for(sd_pair):
    global sd_pair_states
    try:
        state_idx = sd_pair_states[sd_pair].pop(0)
        qubit = _generate_data_qubit(state_idx)
    except IndexError:
        # this will happen if attempting to teleport another qubit but you dont have any further demand for this src-pair
        return None, None
    
    return qubit, state_idx

# Note: I made this simpler loss model to allow for the "p probability" param. The reason why FibreLossModel with p_loss_init=p and p_loss_length=0 wasnt working was probably because (for reasons that I dont understand) there was a check for qubit.is_number_state and it did some amplitude dampening instead of straight up dropping the qubit. This resulted in cases where the qubit was still detected on the other end and only affected the fidelity. So, I worked around this to just have a simpler model that just drops the qubit according to the probablity.
class FixedProbabilityLoss(ns.components.models.qerrormodels.FibreLossModel):
    def __init__(self, p_prob, p_loss_init=0, p_loss_length=0, rng=None):
        super().__init__(p_loss_init, p_loss_length, rng)
        self.p_prob = p_prob

    def error_operation(self, qubits, delta_time=0, **kwargs):
        for idx, qubit in enumerate(qubits):
            if qubit is None:
                continue
            prob_loss = self.p_prob

            p = prob_loss
            discard = not (utils.rand_success(p_of_fail=p))
            if discard:
                ns.qubits.qubitapi.discard(qubit)

class CChannelProbLoss(ns.components.models.cerrormodels.ClassicalErrorModel):
    def __init__(self, prob, **kwargs):
        super().__init__(**kwargs)
        self.prob_loss = prob

    def error_operation(self, items, delta_time=0, **kwargs):
        for i in range(len(items)):
            p = self.prob_loss
            drop = not (utils.rand_success(p_of_fail=p))
            
            if drop:
                items[i] = {}