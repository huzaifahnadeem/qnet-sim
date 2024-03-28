from enum import Enum

# ALGS = Enum('Algorithm', ['QPASS', 'QCAST'])
class ALGS(Enum):
    QPASS = 'qpass'
    QCAST = 'qcast'

class NET_TOPOLOGY(Enum):
    SLMP_GRID_4x4 = 'slmp_grid_4x4'

class YEN_METRICS(Enum):
    EXT = 'ext'             # Expected throughput/ expected number of ebits
    SUMDIST = 'sumdist'     # Sum of Node distances
    CR = 'cr'               # Creation Rate
    BOTCAP = 'botcap'       # Bottleneck capacity
    HOPCOUNT = 'hopcount'   # the hop count. not part of the paper. might be useful in implementation testing

ROLES = Enum('Roles', ['SOURCE', 'DESTINATION', 'REPEATER'])

MSG_KEYS = Enum('MSG_KEYS', ['SRC', 'DST', 'TS', 'PATH', 'LINK_STATE', 'CONN_NUM', 'TYPE', 'EBIT_RECV_SUCCESS'])

CONN_CHANN_LABELS_FN_PARAM = Enum('CONN_CHANN_LABELS_FN_PARAM', ['CCHANNEL', 'QCHANNEL', 'QCONNECTION', 'CCONNECTION', 'CONN_QMEM'])