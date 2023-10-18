
from netsquid.qubits.qubitapi import operate
from netsquid.qubits import operators as ops
from netsquid.components.instructions import INSTR_MEASURE_BELL
from netsquid.qubits.qubitapi import create_qubits, measure

def entangle_epr_bits(_q1, _q2):
    # 1. Hadamard Gate on q1
    # 2. CNOT(control=q1, target=q2)
    # 3. return the qbits
    qbits = create_qubits(2)
    q1 = qbits[0]
    q2 = qbits[1]
    operate(q1, ops.H) 
    operate([q1, q2], ops.CNOT) # q1=control, q2=target
    return q1, q2

def correction(m1, m2, qbit):
    # 0,0 => I
    # 0,1 => X
    # 1,0 => Z
    # 1,1 => ZX

    if (m1 == 0) and (m2 == 0):
        operate(qbit, ops.I)
    elif (m1 == 0) and (m2 == 1):
        operate(qbit, ops.X)
    elif (m1 == 1) and (m2 == 0):
        operate(qbit, ops.Z)
    elif (m1 == 1) and (m2 == 1):
        operate(qbit, ops.Z)
        operate(qbit, ops.X)
    
    return qbit

def bell_state_measurement(qbit, eprbit):
    # CNOT(c=qbit, t=eprbit)
    # Hadamard(qbit)
    # measure in Z basis (Z basis = computational basis i.e |0> and |1>)
    operate([qbit, eprbit], ops.CNOT) # [control, target]
    operate(qbit, ops.H)
    m1, prob1 = measure(qbit, ops.Z)
    m2, prob2 = measure(eprbit, ops.Z)

    return m1, m2
