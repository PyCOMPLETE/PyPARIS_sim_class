import sys
sys.path.append('../../../')

modname = 'numpy.fft'
mod = __import__(modname)

import importlib
mod2 = importlib.import_module(modname)
