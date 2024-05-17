# need to install octave and oct2py first.
# oct2py: https://pypi.org/project/oct2py/
# octave: https://wiki.octave.org/Octave_for_GNU/Linux

from oct2py import octave # allows calling octave/matlab functions in python (octave needs to be installed in the system to use)
import os 
import netsquid as ns

# Note: there is an issue with oct2py/io.py file line 376. it does not import spmatrix from scipy but adding "from scipy.sparse import spmatrix" before this line or at the top of file fixes the issue

lib_path = f'{os.path.dirname(os.path.realpath(__file__))}/lib/quantinf/'
octave.addpath(lib_path)
seed = 1
# octave.rand('state', seed) # setting the seed for random number generator
octave.randn('state', seed) # setting the seed for random number generator
# so randPsi uses randU which uses randn so need to set seed ('state') for randn. setting the seed for rand does nothing.

randstate = octave.randPsi(2)
print(randstate)
print(type(randstate))

data_qubit,  = ns.qubits.create_qubits(1, no_state=True)
print(data_qubit.qstate)
ns.qubits.assign_qstate([data_qubit], randstate)
print(data_qubit.qstate.qrepr)