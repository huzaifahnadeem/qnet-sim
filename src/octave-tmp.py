from oct2py import octave # allows calling octave/matlab functions in python (need to install octave first): https://pypi.org/project/oct2py/
import os 

lib_path = f'{os.path.dirname(os.path.realpath(__file__))}/lib/quantinf/'
octave.addpath(lib_path)
out = octave.randPsi(2)
print(out)