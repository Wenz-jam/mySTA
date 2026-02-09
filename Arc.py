from enum import Enum
from Interpolator import RegularGridInterpolator
from EnumClass import ALL_CLOCK_EDGES, EnumClockEdge, EnumTimingSense, EnumTimingType

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
    from Pin import Pin
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
        self.cell_rise = cell_rise
        self.cell_fall = cell_fall
        self.rise_transition = rise_transition
        self.fall_transition = fall_transition
        self.slew = {EnumClockEdge.RISING: 0.0, EnumClockEdge.FALLING: 0.0}
        self.delay = {EnumClockEdge.RISING: 0.0, EnumClockEdge.FALLING: 0.0}

        # 双向连接
        from_pin.fanout.append(self)
        to_pin.fanin.append(self)

    def __repr__(self):
        return f"Arc({self.from_pin.name} -> {self.to_pin.name})"

    def get_delay(self,clock_edge, input_slew, output_capacitance):
        assert clock_edge in ALL_CLOCK_EDGES
        if clock_edge == EnumClockEdge.RISING:
            return self.cell_rise.get_value(input_slew, output_capacitance)
        else:
            return self.cell_fall.get_value(input_slew, output_capacitance)

    def get_slew(self,clock_edge, input_slew, output_capacitance):
        assert clock_edge in ALL_CLOCK_EDGES
        if clock_edge == EnumClockEdge.RISING:
            return self.rise_transition.get_value(input_slew, output_capacitance)
        else:
            return self.fall_transition.get_value(input_slew, output_capacitance)

    def get_to_pin_clock_edge(self, clock_edge):
        if self.timing_sense == EnumTimingSense.POS_UNATE:
            return clock_edge
        elif self.timing_sense == EnumTimingSense.NEG_UNATE:
            return EnumClockEdge.FALLING if clock_edge == EnumClockEdge.RISING else EnumClockEdge.RISING
        else:
            return EnumClockEdge.UNKNOWN

    def calc_delay(self, clock_edge):
        capacitance = self.to_pin.capacitance
        input_slew = self.from_pin.slew[clock_edge]
        to_pin_clock_edge = self.get_to_pin_clock_edge(clock_edge)
        if to_pin_clock_edge == EnumClockEdge.UNKNOWN:
            self.delay[EnumClockEdge.RISING] = max(self.delay[EnumClockEdge.RISING], self.get_delay(EnumClockEdge.RISING, input_slew, capacitance[EnumClockEdge.RISING]))
            self.delay[EnumClockEdge.FALLING] = max(self.delay[EnumClockEdge.FALLING], self.get_delay(EnumClockEdge.FALLING, input_slew, capacitance[EnumClockEdge.FALLING]))
        else:
            assert to_pin_clock_edge in ALL_CLOCK_EDGES
            delay = self.get_delay(to_pin_clock_edge, input_slew, capacitance[to_pin_clock_edge])
            self.delay[to_pin_clock_edge] = delay

    def propagate_slew(self, clock_edge):
        capacitance = self.to_pin.capacitance
        input_slew = self.from_pin.slew[clock_edge]
        to_pin_clock_edge = self.get_to_pin_clock_edge(clock_edge)
        if to_pin_clock_edge == EnumClockEdge.UNKNOWN:
            # 前级的边沿导致后级的上升沿
            self.slew[EnumClockEdge.RISING] = max(self.slew[EnumClockEdge.RISING], self.get_slew(EnumClockEdge.RISING, input_slew, capacitance[EnumClockEdge.RISING]))
            # 前级的边沿导致后级的下降沿
            self.slew[EnumClockEdge.FALLING] = max(self.slew[EnumClockEdge.FALLING], self.get_slew(EnumClockEdge.FALLING, input_slew, capacitance[EnumClockEdge.FALLING]))
            # 同步更新to_pin的slew
            self.to_pin.slew[EnumClockEdge.RISING] = max(self.to_pin.slew[EnumClockEdge.RISING], self.slew[EnumClockEdge.RISING])
            self.to_pin.slew[EnumClockEdge.FALLING] = max(self.to_pin.slew[EnumClockEdge.FALLING], self.slew[EnumClockEdge.FALLING])
        else:
            assert to_pin_clock_edge in ALL_CLOCK_EDGES
            slew = self.get_slew(to_pin_clock_edge, input_slew, capacitance[to_pin_clock_edge])
            self.slew[to_pin_clock_edge] = slew
            self.to_pin.slew[to_pin_clock_edge] = max(self.to_pin.slew[to_pin_clock_edge], slew)

    
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
