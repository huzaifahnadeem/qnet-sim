# need to install octave and oct2py first.
# oct2py: https://pypi.org/project/oct2py/
# octave: https://wiki.octave.org/Octave_for_GNU/Linux

from oct2py import octave # allows calling octave/matlab functions in python (octave needs to be installed in the system to use)
import os 

# Note: there is an issue with oct2py/io.py file line 376. it does not import spmatrix from scipy but adding "from scipy.sparse import spmatrix" before this line or at the top of file fixes the issue

lib_path = f'{os.path.dirname(os.path.realpath(__file__))}/lib/quantinf/'
octave.addpath(lib_path)
out = octave.randPsi(2)
print(out)