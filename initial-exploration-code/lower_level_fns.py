
# from netsquid.qubits.qubitapi import operate
# from netsquid.qubits import operators as ops
# from netsquid.components.instructions import INSTR_MEASURE_BELL
from netsquid.qubits.qubitapi import create_qubits, measure
import netsquid as ns

def entangle_epr_bits(_q1, _q2):
    # 1. Hadamard Gate on q1
    # 2. CNOT(control=q1, target=q2)
    # 3. return the qbits
    qbits = create_qubits(2)
    q1 = qbits[0]
    q2 = qbits[1]
    ns.qubits.operate(q1, ns.H) 
    ns.qubits.operate([q1, q2], ns.CNOT) # q1=control, q2=target
    return q1, q2

def correction(m1, m2, qbit):
    # 0,0 => I
    # 0,1 => X
    # 1,0 => Z
    # 1,1 => ZX
    # 
    # Gate: X^(m2)Z^(m1)

    # if (m1 == 0) and (m2 == 0):
    #     ns.qubits.operate(qbit, ns.I)
    # elif (m1 == 0) and (m2 == 1):
    #     ns.qubits.operate(qbit, ns.X)
    # elif (m1 == 1) and (m2 == 0):
    #     ns.qubits.operate(qbit, ns.Z)
    # elif (m1 == 1) and (m2 == 1):
    #     ns.qubits.operate(qbit, ns.Z)
    #     ns.qubits.operate(qbit, ns.X)
    
    if m2 == 1:
        ns.qubits.operate(qbit, ns.X)
    if m1 == 1:
        ns.qubits.operate(qbit, ns.Z)

    return qbit

def bell_state_measurement(qbit, eprbit):
    # CNOT(c=qbit, t=eprbit)
    # Hadamard(qbit)
    # measure in Z basis (Z basis = computational basis i.e |0> and |1>)
    ns.qubits.operate([qbit, eprbit], ns.CNOT) # [control, target]
    ns.qubits.operate(qbit, ns.H)
    # m1, prob1 = measure(qbit, ns.Z)
    # m2, prob2 = measure(eprbit, ns.Z)
    m1, prob1 = ns.qubits.measure(qbit)
    m2, prob2 = ns.qubits.measure(eprbit)

    return m1, m2

def temp_assign_state(qbit):
    # assumes qubit is in |0⟩. Changes the state to (|0⟩+𝑖|1⟩)/(√2) == ns.y0 state
    ns.qubits.operate(qbit, ns.H)
    ns.qubits.operate(qbit, ns.S)
    return qbit