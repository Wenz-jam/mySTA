from enum import Enum
import sys
from Pin import Pin
from Interpolator import RegularGridInterpolator
from EnumClass import ALL_CLOCK_EDGES, ALL_TIMING_MODES, EnumClockEdge, EnumTimingMode, EnumTimingSense, EnumTimingType

from typing import Optional

class Lut:
    def __init__(self, lut_group):
        if lut_group is None:
            self.index_1 = [1e8]
            self.index_2 = [1e8]
            self.lut_values = [[0.0]]
            return
        self.index_1 = lut_group.get_array('index_1')[0]
        self.index_2 = lut_group.get_array('index_2')[0]
        self.lut_values = lut_group.get_array('values')
        self.interpolator = RegularGridInterpolator(
            lut_group.get_array('index_1')[0], 
            lut_group.get_array('index_2')[0],
            lut_group.get_array('values'))
    
    def get_value(self, x, y):
        return self.interpolator.interpolate(x, y)
        i = 0
        for idx, index in enumerate(self.index_1):
            if x <= index:
                i = idx
                break
        j = 0
        for idx, index in enumerate(self.index_2):
            if y <= index:
                j = idx
                break
        return self.lut_values[i][j]

class ZeroLut(Lut):
    def __init__(self):
        super().__init__(None)
    
    def get_value(self, x, y):
        return 0.0

class PassThroughLut(Lut):
    def __init__(self):
        super().__init__(None)

    def get_value(self, x, y):
        return x


# Arc.delay以及Arc.slew在C++实现中使用引用的方式与to_pin中的delay, slew绑定, 同步发生变化
class Arc:
    def __init__(self,
                timing_type: Optional[EnumTimingType],
                timing_sense: Optional[EnumTimingSense],
                from_pin: Pin,
                to_pin: Pin,
                cell_rise: Optional[Lut],
                cell_fall: Optional[Lut],
                rise_transition: Optional[Lut],
                fall_transition: Optional[Lut],
                rise_constraint: Optional[Lut],
                fall_constraint: Optional[Lut]):
        self.name = f"{from_pin.name}:{to_pin.name}"
        self.timing_type = timing_type
        self.timing_sense = timing_sense
        self.from_pin = from_pin
        self.to_pin = to_pin
        self.constraint_lut = {EnumClockEdge.RISING: rise_constraint, EnumClockEdge.FALLING: fall_constraint}
        self.delay_lut = {EnumClockEdge.RISING: cell_rise, EnumClockEdge.FALLING: cell_fall}
        self.slew_lut  = {EnumClockEdge.RISING: rise_transition, EnumClockEdge.FALLING: fall_transition}
        self.capacitance = {EnumTimingMode.MAX: {EnumClockEdge.RISING: 0.0, EnumClockEdge.FALLING: 0.0},
                            EnumTimingMode.MIN: {EnumClockEdge.RISING: 0.0, EnumClockEdge.FALLING: 0.0}}
        self.delay = {EnumTimingMode.MAX: {EnumClockEdge.RISING: {EnumClockEdge.RISING: None, EnumClockEdge.FALLING: None},
                                            EnumClockEdge.FALLING: {EnumClockEdge.RISING: None, EnumClockEdge.FALLING: None}},
                        EnumTimingMode.MIN: {EnumClockEdge.RISING: {EnumClockEdge.RISING: None, EnumClockEdge.FALLING: None}, 
                                             EnumClockEdge.FALLING: {EnumClockEdge.RISING: None, EnumClockEdge.FALLING: None}}}

        # 双向连接
        from_pin.fanout.append(self)
        to_pin.fanin.append(self)

    def __repr__(self):
        return f"Arc({self.from_pin.name} -> {self.to_pin.name})"
    
    def get_capacitance(self, timing_mode, clock_edge):
        """获取Arc的capacitance值"""
        assert timing_mode in ALL_TIMING_MODES
        assert clock_edge in ALL_CLOCK_EDGES
        return self.capacitance[timing_mode][clock_edge] + self.to_pin.get_capacitance(timing_mode, clock_edge)
    
    def set_capacitance(self, timing_mode, clock_edge, capacitance_value):
        """设置Arc的capacitance值"""
        assert timing_mode in ALL_TIMING_MODES
        assert clock_edge in ALL_CLOCK_EDGES
        assert capacitance_value is not None, "Capacitance value cannot be None"
        self.capacitance[timing_mode][clock_edge] = capacitance_value

    def get_delay(self, timing_mode, from_clock_edge, to_clock_edge):
        """获取Arc的delay值"""
        assert timing_mode in ALL_TIMING_MODES
        assert from_clock_edge in ALL_CLOCK_EDGES
        assert to_clock_edge in ALL_CLOCK_EDGES
        return self.delay[timing_mode][from_clock_edge][to_clock_edge]

    def set_delay(self, timing_mode, from_clock_edge, to_clock_edge, delay_value):
        """设置Arc的delay值"""
        assert timing_mode in ALL_TIMING_MODES
        assert from_clock_edge in ALL_CLOCK_EDGES
        assert to_clock_edge in ALL_CLOCK_EDGES
        assert delay_value is not None, "Delay value cannot be None"
        self.delay[timing_mode][from_clock_edge][to_clock_edge] = delay_value

    def is_clock_edge_valid(self, from_clock_edge, to_clock_edge):
        """判断给定的from_clock_edge和to_clock_edge是否符合Arc的timing_sense"""
        if self.timing_type in [EnumTimingType.RISING_EDGE]:
            return from_clock_edge == EnumClockEdge.RISING
        if self.timing_type in [EnumTimingType.FALLING_EDGE]:
            return from_clock_edge == EnumClockEdge.FALLING

        if self.timing_type == EnumTimingType.HOLD_RISING:
            return from_clock_edge == EnumClockEdge.RISING
        if self.timing_type == EnumTimingType.HOLD_FALLING:
            return from_clock_edge == EnumClockEdge.FALLING
        
        if self.timing_type == EnumTimingType.SETUP_RISING:
            return from_clock_edge == EnumClockEdge.RISING
        if self.timing_type == EnumTimingType.SETUP_FALLING:
            return from_clock_edge == EnumClockEdge.FALLING

        if self.timing_sense == EnumTimingSense.POS_UNATE:
            return from_clock_edge == to_clock_edge
        if self.timing_sense == EnumTimingSense.NEG_UNATE:
            return from_clock_edge != to_clock_edge
        if self.timing_sense == EnumTimingSense.NON_UNATE:
            return True
        return False
        raise ValueError(f"Unknown timing sense: {self.timing_sense} or timing type: {self.timing_type}")

    def calc_slew(self, from_clock_edge, to_clock_edge, slew, capacitance):
        """根据Arc的LUT计算slew值"""
        if not self.is_clock_edge_valid(from_clock_edge, to_clock_edge):
            return None
        if self.slew_lut[to_clock_edge] is None:
            return None
        return self.slew_lut[to_clock_edge].get_value(slew, capacitance)

    def calc_delay(self, from_clock_edge, to_clock_edge, slew, capacitance):
        """根据Arc的LUT计算delay值"""
        if not self.is_clock_edge_valid(from_clock_edge, to_clock_edge):
            return None
        if self.delay_lut[to_clock_edge] is None:
            return None
        return self.delay_lut[to_clock_edge].get_value(slew, capacitance)

    def calc_request_arrival_time(self, timing_mode, from_clock_edge, to_clock_edge, constrainted_pin_slew, related_pin_slew):
        """根据Arc的LUT计算request arrival_time值"""
        if not self.is_clock_edge_valid(from_clock_edge, to_clock_edge):
            return None
        if self.constraint_lut[to_clock_edge] is None:
            return None
        if self.timing_type in [EnumTimingType.SETUP_RISING, EnumTimingType.SETUP_FALLING]:
            assert timing_mode == EnumTimingMode.MAX, "Setup timing should be calculated in MAX mode"
        if self.timing_type in [EnumTimingType.HOLD_RISING, EnumTimingType.HOLD_FALLING]:
            assert timing_mode == EnumTimingMode.MIN, "Hold timing should be calculated in MIN mode"
        return self.constraint_lut[to_clock_edge].get_value(constrainted_pin_slew, related_pin_slew)

    def propagate_slew(self, timing_mode, from_clock_edge, to_clock_edge):
        """依据前级的slew值, 计算to_pin的slew并更新到to_pin中"""
        if not self.is_clock_edge_valid(from_clock_edge, to_clock_edge):
            return
        input_slew = self.from_pin.get_slew(timing_mode, from_clock_edge)
        capacitance = self.get_capacitance(timing_mode, to_clock_edge)
        to_pin_slew = self.calc_slew(from_clock_edge, to_clock_edge, input_slew, capacitance)
        if to_pin_slew is None:
            return
        self.to_pin.update_slew(timing_mode, to_clock_edge, to_pin_slew)

    def update_delay(self, timing_mode, from_clock_edge, to_clock_edge, delay):
        """更新Arc的delay值，并同步更新to_pin的delay值"""
        assert self.is_clock_edge_valid(from_clock_edge, to_clock_edge), \
            f"Invalid clock edge transition from {from_clock_edge} to {to_clock_edge} for timing sense {self.timing_sense}"
        old_value = self.get_delay(timing_mode, from_clock_edge, to_clock_edge)
        if timing_mode == EnumTimingMode.MAX:
            if not old_value or delay > old_value:
                self.set_delay(timing_mode, from_clock_edge, to_clock_edge, delay)
        elif timing_mode == EnumTimingMode.MIN:
            if not old_value or delay < old_value:
                self.set_delay(timing_mode, from_clock_edge, to_clock_edge, delay)
        else:
            raise ValueError(f"Unknown timing mode: {timing_mode}")

    def propagate_delay(self, timing_mode, from_clock_edge, to_clock_edge):
        """更新Arc的delay值，并同步更新to_pin的delay值"""
        if not self.is_clock_edge_valid(from_clock_edge, to_clock_edge):
            return
        from_pin_slew = self.from_pin.get_slew(timing_mode, from_clock_edge)
        capacitance = self.get_capacitance(timing_mode, to_clock_edge)
        delay = self.calc_delay(from_clock_edge, to_clock_edge, from_pin_slew, capacitance)
        if delay is None:
            return
        self.update_delay(timing_mode, from_clock_edge, to_clock_edge, delay)
    
    def propagate_arrival_time(self, timing_mode, from_clock_edge, to_clock_edge):
        """更新Arc的delay值，并同步更新to_pin的arrival_time值"""
        if not self.is_clock_edge_valid(from_clock_edge, to_clock_edge):
            return
        from_pin_arrival_time = self.from_pin.get_arrival_time(timing_mode, from_clock_edge)
        delay = self.get_delay(timing_mode, from_clock_edge, to_clock_edge)
        # 部分路径被剪枝
        if from_pin_arrival_time is None or delay is None:
            return
        arrival_time = from_pin_arrival_time + delay
        self.to_pin.update_arrival_time(timing_mode, from_clock_edge, to_clock_edge, arrival_time, self)

    def propagate_request_arrival_time(self, timing_mode, from_clock_edge, to_clock_edge):
        """更新Arc的delay值，并同步更新to_pin的request arrival_time值"""
        if not self.is_clock_edge_valid(from_clock_edge, to_clock_edge):
            return
        if self.timing_type in [EnumTimingType.SETUP_RISING, EnumTimingType.SETUP_FALLING]:
            if timing_mode != EnumTimingMode.MAX:
                return
        if self.timing_type in [EnumTimingType.HOLD_RISING, EnumTimingType.HOLD_FALLING]:
            if timing_mode != EnumTimingMode.MIN:
                return
        from_pin_request_arrival_time = self.from_pin.get_arrival_time(timing_mode, from_clock_edge)
        def get_delay(_timing_mode):
            constrainted_pin_slew = self.to_pin.get_slew(_timing_mode, to_clock_edge)
            if constrainted_pin_slew == None:
                print(f"Warning: Constrainted pin slew is None for {self.to_pin.name} at {_timing_mode} {to_clock_edge}, using 0.0 instead", file=sys.stderr)
                constrainted_pin_slew = 0.0
            related_pin_slew = self.from_pin.get_slew(_timing_mode, from_clock_edge)
            if related_pin_slew == None:
                print(f"Warning: Related pin slew is None for {self.from_pin.name} at {_timing_mode} {from_clock_edge}, using 0.0 instead", file=sys.stderr)
                related_pin_slew = 0.0
            delay = self.calc_request_arrival_time(timing_mode, from_clock_edge, to_clock_edge, constrainted_pin_slew, related_pin_slew)
            return delay
        max_delay = get_delay(EnumTimingMode.MAX)
        min_delay = get_delay(EnumTimingMode.MIN)
        max_delay , min_delay = max(max_delay, min_delay), min(max_delay, min_delay)
        if timing_mode == EnumTimingMode.MAX:
            delay = max_delay
        elif timing_mode == EnumTimingMode.MIN:
            delay = min_delay
        # 部分路径被剪枝
        if from_pin_request_arrival_time is None or delay is None:
            return
        request_arrival_time = from_pin_request_arrival_time + delay
        self.to_pin.update_request_arrival_time(timing_mode, from_clock_edge, to_clock_edge, request_arrival_time)

class ArcFactory:
    """Arc对象工厂，管理Arc的创建和查询"""
    def __init__(self):
        self._arcs = []
        self._constraint_arcs = []
    
    def create_arc(self,
                   timing_type,
                   timing_sense,
                   from_pin,
                   to_pin,
                   cell_rise,
                   cell_fall,
                   rise_transition,
                   fall_transition,
                   rise_constraint,
                   fall_constraint):

        timing_type = EnumTimingType.to_enum(timing_type) if not isinstance(timing_type, EnumTimingType) and timing_type is not None else timing_type
        timing_sense = EnumTimingSense.to_enum(timing_sense) if not isinstance(timing_sense, EnumTimingSense) and timing_sense is not None else timing_sense
        cell_rise = Lut(cell_rise) if not isinstance(cell_rise, Lut) and cell_rise is not None else cell_rise
        cell_fall = Lut(cell_fall) if not isinstance(cell_fall, Lut) and cell_fall is not None else cell_fall
        rise_transition = Lut(rise_transition) if not isinstance(rise_transition, Lut) and rise_transition is not None else rise_transition
        fall_transition = Lut(fall_transition) if not isinstance(fall_transition, Lut) and fall_transition is not None else fall_transition
        rise_constraint = Lut(rise_constraint) if not isinstance(rise_constraint, Lut) and rise_constraint is not None else rise_constraint
        fall_constraint = Lut(fall_constraint) if not isinstance(fall_constraint, Lut) and fall_constraint is not None else fall_constraint

        arc = Arc(timing_type, timing_sense, from_pin, to_pin, cell_rise, cell_fall, rise_transition, fall_transition, rise_constraint, fall_constraint)
        self._arcs.append(arc)
        if rise_constraint is not None and fall_constraint is not None and timing_sense is None:
            self._constraint_arcs.append(arc)
        return arc
    
    def get_all_arcs(self):
        return self._arcs
    
    def get_all_constraint_arcs(self):
        return self._constraint_arcs
