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

class EnumTimingType(Enum):
    MAX = 1
    MIN = 2
    
    @staticmethod
    def to_enum(value: str):
        mapping = {
            'max': EnumTimingType.MAX,
            'min': EnumTimingType.MIN
        }
        assert value.lower() in mapping, f"Unknown timing type: {value}"
        return mapping.get(value.lower())

ALL_TIMING_TYPES = [EnumTimingType.MAX, EnumTimingType.MIN]

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