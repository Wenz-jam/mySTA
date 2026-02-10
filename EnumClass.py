from enum import Enum

class EnumPinType(Enum):
    PRIMARY_INPUT = 1
    PRIMARY_OUTPUT = 2
    INPUT = 3
    OUTPUT = 4
    
    @staticmethod
    def to_enum(value: str):
        mapping = {
            'input': EnumPinType.INPUT,
            'output': EnumPinType.OUTPUT,
            'primary_input': EnumPinType.PRIMARY_INPUT,
            'primary_output': EnumPinType.PRIMARY_OUTPUT
        }
        assert value.lower() in mapping, f"Unknown pin type: {value}"
        return mapping.get(value.lower())

ALL_PIN_TYPES = [EnumPinType.PRIMARY_INPUT, EnumPinType.PRIMARY_OUTPUT, EnumPinType.INPUT, EnumPinType.OUTPUT]

class EnumClockEdge(Enum):
    FALLING = 0
    RISING = 1
    UNKNOWN = 2
    
    @staticmethod
    def to_enum(value: str):
        mapping = {
            'rising': EnumClockEdge.RISING,
            'falling': EnumClockEdge.FALLING
        }
        assert value.lower() in mapping, f"Unknown clock edge: {value}"
        return mapping.get(value.lower())
    
    def __str__(self):
        mapping = {
            EnumClockEdge.RISING: 'r',
            EnumClockEdge.FALLING: 'f',
        }
        return mapping.get(self, 'unknown')

ALL_CLOCK_EDGES = [EnumClockEdge.RISING, EnumClockEdge.FALLING]

class EnumTimingMode(Enum):
    MAX = 1
    MIN = 2
    
    @staticmethod
    def to_enum(value: str):
        mapping = {
            'max': EnumTimingMode.MAX,
            'min': EnumTimingMode.MIN
        }
        assert value.lower() in mapping, f"Unknown timing type: {value}"
        return mapping.get(value.lower())
    
    def __str__(self):
        mapping = {
            EnumTimingMode.MAX: 'max',
            EnumTimingMode.MIN: 'min'
        }
        return mapping.get(self, 'unknown')

ALL_TIMING_MODES = [EnumTimingMode.MAX, EnumTimingMode.MIN]

class EnumTimingSense(Enum):
    POS_UNATE = 1
    NEG_UNATE = 2
    NON_UNATE = 3

    @staticmethod
    def to_enum(value: str):
        mapping = {
            'positive_unate': EnumTimingSense.POS_UNATE,
            'negative_unate': EnumTimingSense.NEG_UNATE,
            'non_unate': EnumTimingSense.NON_UNATE
        }
        assert value.lower() in mapping, f"Unknown arc type: {value}"
        return mapping.get(value.lower())

ALL_TIMING_SENSES = [EnumTimingSense.POS_UNATE, EnumTimingSense.NEG_UNATE]

class EnumTimingType(Enum):
    WIRE = 0
    CLEAR = 1
    COMBINATIONAL = 2
    FALLING_EDGE = 3
    HOLD_FALLING = 4
    HOLD_RISING = 5
    MIN_PULSE_WIDTH = 6
    NON_SEQ_HOLD_RISING = 7
    NON_SEQ_SETUP_RISING = 8
    PRESET = 9
    RECOVERY_FALLING = 10
    RECOVERY_RISING = 11
    REMOVAL_FALLING = 12
    REMOVAL_RISING = 13
    RISING_EDGE = 14
    SETUP_FALLING = 15
    SETUP_RISING = 16
    THREE_STATE_DISABLE = 17
    THREE_STATE_ENABLE = 18
    
    @staticmethod
    def to_enum(value: str):
        mapping = {
            "wire" : EnumTimingType.WIRE,
            "clear" : EnumTimingType.CLEAR,
            "combinational" : EnumTimingType.COMBINATIONAL,
            "falling_edge" : EnumTimingType.FALLING_EDGE,
            "hold_falling" : EnumTimingType.HOLD_FALLING,
            "hold_rising" : EnumTimingType.HOLD_RISING,
            "min_pulse_width" : EnumTimingType.MIN_PULSE_WIDTH,
            "non_seq_hold_rising" : EnumTimingType.NON_SEQ_HOLD_RISING,
            "non_seq_setup_rising" : EnumTimingType.NON_SEQ_SETUP_RISING,
            "preset" : EnumTimingType.PRESET,
            "recovery_falling" : EnumTimingType.RECOVERY_FALLING,
            "recovery_rising" : EnumTimingType.RECOVERY_RISING,
            "removal_falling" : EnumTimingType.REMOVAL_FALLING,
            "removal_rising" : EnumTimingType.REMOVAL_RISING,
            "rising_edge" : EnumTimingType.RISING_EDGE,
            "setup_falling" : EnumTimingType.SETUP_FALLING,
            "setup_rising" : EnumTimingType.SETUP_RISING,
            "three_state_disable" : EnumTimingType.THREE_STATE_DISABLE,
            "three_state_enable" : EnumTimingType.THREE_STATE_ENABLE,
        }
        assert value.lower() in mapping, f"Unknown timing type: {value}"
        return mapping.get(value.lower())

import itertools
def FOREACH_EL_RF(handler):
    for timing_type, clock_edge in itertools.product(ALL_TIMING_MODES, ALL_CLOCK_EDGES):
        handler(timing_type, clock_edge)
    
def FOREACH_EL_FRF_TRF(handler):
    for timing_type, from_clock_edge, to_clock_edge in \
        itertools.product(ALL_TIMING_MODES, ALL_CLOCK_EDGES, ALL_CLOCK_EDGES):    
        handler(timing_type, from_clock_edge, to_clock_edge)