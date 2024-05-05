from enum import Enum
import argparse

class EnumInParamAction(argparse.Action):
    # from: https://stackoverflow.com/questions/43968006/support-for-enum-arguments-in-argparse
    """
    Argparse action for handling Enums
    """
    def __init__(self, **kwargs):
        # Pop off the type value
        enum_type = kwargs.pop("type", None)

        # Ensure an Enum subclass is provided
        if enum_type is None:
            raise ValueError("type must be assigned an Enum when using EnumAction")
        if not issubclass(enum_type, Enum):
            raise TypeError("type must be an Enum when using EnumAction")

        # Generate choices from the Enum
        kwargs.setdefault("choices", tuple(e.value for e in enum_type))

        super(EnumAction, self).__init__(**kwargs)

        self._enum = enum_type

    def __call__(self, parser, namespace, values, option_string=None):
        # Convert value back into an Enum
        value = self._enum(values)
        setattr(namespace, self.dest, value)

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

MSG_KEYS = Enum('MSG_KEYS', ['SRC', 'DST', 'TS', 'PATH', 'LINK_STATE', 'CONN_NUM', 'TYPE', 'EBIT_RECV_SUCCESS', "CORRECTIONS", "DATA_QUBIT_STATE", "SERVING_PAIR", "CORRECTIONS_VIA"])

MSG_TYPE = Enum('MSG_TYPE', ['ebit_sent', 'ebit_received', 'link_state', 'corrections', 'e2e_ready'])

CONN_CHANN_LABELS_FN_PARAM = Enum('CONN_CHANN_LABELS_FN_PARAM', ['CCHANNEL', 'QCHANNEL', 'QCONNECTION', 'CCONNECTION', 'CONN_QMEM'])

QCHANNEL_MODEL_TYPES = Enum('QCHANNEL_MODEL_TYPES', ['delay_model', 'quantum_noise_model', 'quantum_loss_model', 'none']) # netsquid requires these exact strings when setting a model for a channel (except none is my own)
QCHANNEL_NOISE_MODEL = Enum('QCHANNEL_NOISE_MODEL', ['none', 'dephase', 'depolar']) # models that can be used when 'quantum_noise_model' is selected as model type
QCHANNEL_LOSS_MODEL = Enum('QCHANNEL_LOSS_MODEL', []) # models that can be used when 'quantum_loss_model' is selected as model type