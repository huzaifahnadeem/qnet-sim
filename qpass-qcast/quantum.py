import netsquid as ns
import random
from numpy import pi

# possible states that the data qubit can start in (will apply some combination of gates later)
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
        original_qubit = generate_data_qubit(original_state_idx)
        original_state = original_qubit.qstate.qrepr
        fidelity = ns.qubits.fidelity(ebit, original_state, squared=True)
    else:
        fidelity = None
    
    return ebit, fidelity # ebit has the teleported qubit's state now

def generate_data_qubit(state_idx):
    start_state, operator = data_qubit_states[state_idx]
    data_qubit,  = ns.qubits.create_qubits(1, no_state=True)
    ns.qubits.assign_qstate([data_qubit], starting_states[start_state]) # assign starting state
    ns.qubits.operate(data_qubit, operator) # apply the operator
    
    return data_qubit

def gen_random_state():
    angle_factor = random.uniform(0.0, 2.0) # this will be multiplied by pi
    rot_axis = random.choice([(1, 0, 0), (0, 1, 0), (0, 0, 1)]) # Unit vector representing x, y, and z axes, respectively.
    do_complex_conj = random.choice([True, False])
    
    start_state = random.choice(list(starting_states.keys()))
    operator = ns.qubits.operators.create_rotation_op(angle=angle_factor*pi, rotation_axis=rot_axis, conjugate=do_complex_conj)
    
    next_idx = len(data_qubit_states)
    data_qubit_states.append((start_state, operator)) # saving the starting state and the operator. When generate_data_qubit() is called, it will generate a qubit and assign it this state and then apply the operator.
    return next_idx