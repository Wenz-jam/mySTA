from enum import Enum
from Pin import Pin
from Interpolator import RegularGridInterpolator
from EnumClass import ALL_CLOCK_EDGES, ALL_TIMING_MODES, EnumClockEdge, EnumTimingMode, EnumTimingSense, EnumTimingType

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
                timing_type: EnumTimingType,
                timing_sense: EnumTimingSense,
                from_pin: Pin,
                to_pin: Pin,
                cell_rise: Lut,
                cell_fall: Lut,
                rise_transition: Lut,
                fall_transition: Lut):
        self.timing_type = timing_type
        self.timing_sense = timing_sense
        self.from_pin = from_pin
        self.to_pin = to_pin
        self.cell_rise = None
        self.cell_fall = None
        self.rise_transition = None
        self.fall_transition = None
        self.delay_lut = {EnumClockEdge.RISING: cell_rise, EnumClockEdge.FALLING: cell_fall}
        self.slew_lut  = {EnumClockEdge.RISING: rise_transition, EnumClockEdge.FALLING: fall_transition}
        self.capacitance = {EnumTimingMode.MAX: {EnumClockEdge.RISING: 0.0, EnumClockEdge.FALLING: 0.0},
                            EnumTimingMode.MIN: {EnumClockEdge.RISING: 0.0, EnumClockEdge.FALLING: 0.0}}
        self.delay = {EnumTimingMode.MAX: {EnumClockEdge.RISING: 0.0, EnumClockEdge.FALLING: 0.0},
                        EnumTimingMode.MIN: {EnumClockEdge.RISING: 1e8, EnumClockEdge.FALLING: 1e8}}

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
        self.capacitance[timing_mode][clock_edge] = capacitance_value

    def get_delay(self, timing_mode, clock_edge):
        """获取Arc的delay值"""
        assert timing_mode in ALL_TIMING_MODES
        assert clock_edge in ALL_CLOCK_EDGES
        return self.delay[timing_mode][clock_edge]

    def set_delay(self, timing_mode, clock_edge, delay_value):
        """设置Arc的delay值"""
        assert timing_mode in ALL_TIMING_MODES
        assert clock_edge in ALL_CLOCK_EDGES
        self.delay[timing_mode][clock_edge] = delay_value

    def calc_slew(self, clock_edge, input_slew, capacitance):
        """根据Arc的LUT计算slew值"""
        return self.slew_lut[clock_edge].get_value(input_slew, capacitance)
    
    def propagate_slew(self, timing_mode, clock_edge, slew_value):
        """依据前级的slew值, 计算to_pin的slew并更新到to_pin中"""
        to_pin: Pin = self.to_pin
        if self.timing_sense == EnumTimingSense.NON_UNATE:
            # 前级导致上升沿
            to_pin_clock_edge = EnumClockEdge.RISING
            capacitance = self.get_capacitance(timing_mode, to_pin_clock_edge)
            to_pin_slew = self.calc_slew(to_pin_clock_edge, slew_value, capacitance)
            to_pin.update_slew(timing_mode, to_pin_clock_edge, to_pin_slew)
            # 前级导致下降沿
            to_pin_clock_edge = EnumClockEdge.FALLING
            capacitance = self.get_capacitance(timing_mode, to_pin_clock_edge)
            to_pin_slew = self.calc_slew(to_pin_clock_edge, slew_value, capacitance)
            to_pin.update_slew(timing_mode, to_pin_clock_edge, to_pin_slew)
            return
        to_pin_clock_edge = self.get_to_pin_clock_edge(clock_edge)
        capacitance = self.get_capacitance(timing_mode, to_pin_clock_edge)
        to_pin_slew = self.calc_slew(to_pin_clock_edge, slew_value, capacitance)
        to_pin.update_slew(timing_mode, to_pin_clock_edge, to_pin_slew)
    
    def calc_delay(self, clock_edge, input_slew, capacitance):
        """根据Arc的LUT计算delay值"""
        return self.delay_lut[clock_edge].get_value(input_slew, capacitance)

    def update_delay(self, timing_mode, clock_edge):
        """更新Arc的delay值，并同步更新to_pin的delay值"""
        from_pin: Pin = self.from_pin
        to_pin: Pin = self.to_pin
        from_pin_slew = from_pin.get_slew(timing_mode, clock_edge)
        to_pin_capacitance = to_pin.get_capacitance(timing_mode, clock_edge)
        delay = self.calc_delay(clock_edge, from_pin_slew, to_pin_capacitance)
        if ((timing_mode == EnumTimingMode.MAX and delay > self.delay[timing_mode][clock_edge]) or
        (timing_mode == EnumTimingMode.MIN and delay < self.delay[timing_mode][clock_edge])):
            self.set_delay(timing_mode, clock_edge, delay)

    def get_to_pin_clock_edge(self, clock_edge):
        if self.timing_sense == EnumTimingSense.POS_UNATE:
            return clock_edge
        elif self.timing_sense == EnumTimingSense.NEG_UNATE:
            return EnumClockEdge.FALLING if clock_edge == EnumClockEdge.RISING else EnumClockEdge.RISING
        else:
            return EnumClockEdge.UNKNOWN
    
    @property
    def key(self):
        """Arc的唯一标识符"""
        return f"{self.from_pin.name}:{self.to_pin.name}"

class ArcFactory:
    """Arc对象工厂，管理Arc的创建和查询"""
    def __init__(self):
        self._arcs = {}
    
    def create_arc(self,
                   timing_type,
                   timing_sense,
                   from_pin,
                   to_pin,
                   cell_rise,
                   cell_fall,
                   rise_transition,
                   fall_transition):
        arc_key = f"{from_pin.name}:{to_pin.name}"
        
        if arc_key in self._arcs:
            return self._arcs[arc_key]

        timing_type = EnumTimingType.to_enum(timing_type) if not isinstance(timing_type, EnumTimingType) else timing_type
        timing_sense = EnumTimingSense.to_enum(timing_sense) if not isinstance(timing_sense, EnumTimingSense) else timing_sense
        cell_rise = Lut(cell_rise) if not isinstance(cell_rise, Lut) else cell_rise
        cell_fall = Lut(cell_fall) if not isinstance(cell_fall, Lut) else cell_fall
        rise_transition = Lut(rise_transition) if not isinstance(rise_transition, Lut) else rise_transition
        fall_transition = Lut(fall_transition) if not isinstance(fall_transition, Lut) else fall_transition

        arc = Arc(timing_type, timing_sense, from_pin, to_pin, cell_rise, cell_fall, rise_transition, fall_transition)
        self._arcs[arc_key] = arc
        return arc
    
    def get_arc(self, key):
        return self._arcs.get(key)
    
    def get_all_arcs(self):
        return list(self._arcs.values())
