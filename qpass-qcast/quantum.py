import netsquid as ns

# possible states that the data qubit can be in (v limited rn will add variety later):
ket_minus = ns.h1   # ns.h1 = |−⟩  = 1/√(2)*(|0⟩ − |1⟩)
ket_plus = ns.h0    # ns.h0 = |+⟩  = 1/√(2)*(|0⟩ + |1⟩)
ket_1_y = ns.y1     # ns.y0 = |1𝑌⟩ = 1/√(2)*(|0⟩ - 𝑖|1⟩)
ket_0_y = ns.y0     # ns.y0 = |0𝑌⟩ = 1/√(2)*(|0⟩ + 𝑖|1⟩)
ket_1 = ns.s1       # ns.s1 = |1⟩
ket_0 = ns.s0       # ns.s0 = |0⟩
data_qubit_states = {
        '|−⟩': ket_minus,
        '|+⟩': ket_plus,
        '|1Y⟩': ket_1_y,
        '|0Y⟩': ket_0_y,
        '|1⟩': ket_1,
        '|0⟩': ket_0,
    }

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

def apply_corrections(ebit, corrections, original_state=None):
    m0 = corrections[0]
    m1 = corrections[1]

    if m1:
        ns.qubits.operate(ebit, ns.X)
    if m0:
        ns.qubits.operate(ebit, ns.Z)
    
    # if original state provided then also returns the fidelity of it. Otherwise fidelity is just None
    if original_state is not None:
        original_state = data_qubit_states[original_state]
        fidelity = ns.qubits.fidelity(ebit, original_state, squared=True)
    else:
        fidelity = None
    
    return ebit, fidelity # ebit has the teleported qubit's state now

def generate_data_qubit(state):
    data_qubit,  = ns.qubits.create_qubits(1, no_state=True)
    ns.qubits.assign_qstate([data_qubit], data_qubit_states[state])
    return data_qubit