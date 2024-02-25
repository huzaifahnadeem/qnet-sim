from enum import Enum

# ALGS = Enum('Algorithm', ['QPASS', 'QCAST'])
class ALGS(Enum):
    QPASS = 'qpass'
    QCAST = 'qcast'

class NET_TOPOLOGY(Enum):
    SLMP_GRID_4x4 = 'slmp_grid_4x4'

class YEN_METRICS(Enum):
    SUMDIST = 'sumdist'     # Sum of Node distances
    CR = 'cr'               # Creation Rate
    BOTCAP = 'botcap'       # Bottleneck capacity
    HOPCOUNT = 'hopcount'   # the hop count. not part of the paper. might be useful in implementation testing