from enum import Enum

class ALGS(Enum):
    QPASS = 'QPASS'
    QCAST = 'QCAST'
    SLMPG = 'SLMPg'
    SLMPL = 'SLMPl'

class NET_TOPOLOGY(Enum):
    SLMP_GRID_4x4 = 'slmp_grid_4x4'
    ATT = 'att'
    IBM = 'ibm'
    ABILENE = 'abilene'
    SURFNET = 'surfnet'
    ER_50_01 = 'er_50_01'   # erdos_renyi_graph(50, 0.1)
    ER_50_005 = 'er_50_005' # erdos_renyi_graph(50, 0.05)
    PA_50_2 = 'pa_50_2'     # PA(50, 2) // Preferential Attachment Model
    PA_50_3 = 'pa_50_3'     # PA(50, 3) // Preferential Attachment Model

class YEN_METRICS(Enum):
    EXT = 'ext'             # Expected throughput/ expected number of ebits
    SUMDIST = 'sumdist'     # Sum of Node distances
    CR = 'cr'               # Creation Rate
    BOTCAP = 'botcap'       # Bottleneck capacity
    HOPCOUNT = 'hopcount'   # the hop count. not part of the paper. might be useful in implementation testing

ROLES = Enum('Roles', ['SOURCE', 'DESTINATION', 'REPEATER', 'NO_TASK'])

MSG_KEYS = Enum('MSG_KEYS', ['SRC', 'DST', 'TS', 'PATH', 'LINK_STATE', 'CONN_NUM', 'TYPE', 'EBIT_RECV_SUCCESS', "CORRECTIONS", "DATA_QUBIT_STATE"])

MSG_TYPE = Enum('MSG_TYPE', ['ebit_sent', 'ebit_received', 'link_state', 'corrections'])

CONN_CHANN_LABELS_FN_PARAM = Enum('CONN_CHANN_LABELS_FN_PARAM', ['CCHANNEL', 'QCHANNEL', 'QCONNECTION', 'CCONNECTION', 'CONN_QMEM'])

EVENT_MSG_PASSING_KEYS = Enum('EVENT_MSG_PASSING_KEYS', [])