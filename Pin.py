from enum import Enum

from EnumClass import ALL_CLOCK_EDGES, ALL_TIMING_MODES, EnumClockEdge, EnumPinType, EnumTimingMode

class Pin:
    def __init__(self, name, pin_type=None):
        self.name = name
        self.net = None
        self.type = pin_type  # 避免与Python的type关键字冲突
        self.capacitance = {EnumTimingMode.MAX: {EnumClockEdge.RISING: 0.0, EnumClockEdge.FALLING: 0.0}, 
                            EnumTimingMode.MIN: {EnumClockEdge.RISING: 0.0, EnumClockEdge.FALLING: 0.0}}
        self.slew = {EnumTimingMode.MAX: {EnumClockEdge.RISING: None, EnumClockEdge.FALLING: None}, 
                     EnumTimingMode.MIN: {EnumClockEdge.RISING: None, EnumClockEdge.FALLING: None}}
        self.arrival_time = {EnumTimingMode.MAX: {EnumClockEdge.RISING: None, EnumClockEdge.FALLING: None}, 
                      EnumTimingMode.MIN: {EnumClockEdge.RISING: None, EnumClockEdge.FALLING: None}}
        self.predecessor = {EnumTimingMode.MAX: {EnumClockEdge.RISING: None, EnumClockEdge.FALLING: None},
                            EnumTimingMode.MIN: {EnumClockEdge.RISING: None, EnumClockEdge.FALLING: None}}
        self.arcs = None # deprecated
        self.fanin = []
        self.fanout = []
    
    def __repr__(self):
        return f"Pin({self.name}, type={self.type})"

    def get_slew(self, timing_mode, clock_edge):
        """获取Pin的slew值"""
        assert timing_mode in ALL_TIMING_MODES
        assert clock_edge in ALL_CLOCK_EDGES
        return self.slew[timing_mode][clock_edge]

    def set_slew(self, timing_mode, clock_edge, slew_value):
        """更新Pin的slew值"""
        assert timing_mode in ALL_TIMING_MODES
        assert clock_edge in ALL_CLOCK_EDGES
        self.slew[timing_mode][clock_edge] = slew_value

    def get_capacitance(self, timing_mode, clock_edge):
        """获取Pin的capacitance值"""
        assert timing_mode in ALL_TIMING_MODES
        assert clock_edge in ALL_CLOCK_EDGES
        return self.capacitance[timing_mode][clock_edge]

    def set_capacitance(self, timing_mode, clock_edge, capacitance_value):
        """更新Pin的capacitance值"""
        assert timing_mode in ALL_TIMING_MODES
        assert clock_edge in ALL_CLOCK_EDGES
        self.capacitance[timing_mode][clock_edge] = capacitance_value

    def update_capacitance(self, timing_mode, clock_edge):
        total_capacitance = sum(arc.get_capacitance(timing_mode, clock_edge) for arc in self.fanout)
        self.set_capacitance(timing_mode, clock_edge, total_capacitance)

    def connect_to_net(self, net):
        """将Pin连接到Net，根据Pin类型确定是source还是sink"""
        assert net is not None
        self.net = net
        if self.type == EnumPinType.INPUT or self.type == EnumPinType.PRIMARY_OUTPUT:
            net.add_sink(self)
        elif self.type == EnumPinType.OUTPUT or self.type == EnumPinType.PRIMARY_INPUT:
            net.set_source(self)
        else:
            raise ValueError(f"Unknown pin type: {self.type} for pin {self.name}")

    def propagate_slew(self, timing_mode, from_clock_edge, to_clock_edge):
        """传播Pin的slew值到fanout的Arc和to_pin"""
        for arc in self.fanout:
            arc.propagate_slew(timing_mode, from_clock_edge, to_clock_edge)

    def propagate_delay(self, timing_mode, from_clock_edge, to_clock_edge):
        """传播Pin的arrival_time值到fanout的Arc和to_pin"""
        for arc in self.fanout:
            arc.propagate_delay(timing_mode, from_clock_edge, to_clock_edge)

    def update_predecessor(self, timing_mode, clock_edge, predecessor_arc):
        """更新Pin的predecessor"""
        self.predecessor[timing_mode][clock_edge] = predecessor_arc

    def update_slew(self, timing_mode, clock_edge, slew_value):
        """更新Pin的slew值"""
        old_slew = self.get_slew(timing_mode, clock_edge)
        if timing_mode == EnumTimingMode.MAX:
            if not old_slew or slew_value > old_slew:
                self.set_slew(timing_mode, clock_edge, slew_value)
        elif timing_mode == EnumTimingMode.MIN:
            if not old_slew or slew_value < old_slew:
                self.set_slew(timing_mode, clock_edge, slew_value)
        else:
            raise ValueError(f"Unknown timing mode: {timing_mode} for pin {self.name}")
    
    def get_arrival_time(self, timing_mode, clock_edge):
        """获取Pin的arrival_time值"""
        assert timing_mode in ALL_TIMING_MODES
        assert clock_edge in ALL_CLOCK_EDGES
        at = self.arrival_time[timing_mode][clock_edge]
        return at
    
    def set_arrival_time(self, timing_mode, clock_edge, arrival_time_value):
        """更新Pin的arrival_time值"""
        assert timing_mode in ALL_TIMING_MODES
        assert clock_edge in ALL_CLOCK_EDGES
        self.arrival_time[timing_mode][clock_edge] = arrival_time_value
    
    def update_arrival_time(self, timing_mode, clock_edge, arrival_time_value, from_arc):
        """更新Pin的arrival_time值"""
        assert timing_mode in ALL_TIMING_MODES
        assert clock_edge in ALL_CLOCK_EDGES
        old_at = self.get_arrival_time(timing_mode, clock_edge)
        if timing_mode == EnumTimingMode.MAX:
            if not old_at or arrival_time_value > old_at:
                self.set_arrival_time(timing_mode, clock_edge, arrival_time_value)
                self.update_predecessor(timing_mode, clock_edge, from_arc)
        elif timing_mode == EnumTimingMode.MIN:
            if not old_at or arrival_time_value < old_at:
                self.set_arrival_time(timing_mode, clock_edge, arrival_time_value)
                self.update_predecessor(timing_mode, clock_edge, from_arc)
        else:
            raise ValueError(f"Unknown timing mode: {timing_mode} for pin {self.name}")

    def propagate_arrival_time(self, timing_mode, from_clock_edge, to_clock_edge):
        """传播Pin的arrival_time值到fanout的Arc和to_pin"""
        for arc in self.fanout:
            arc.propagate_arrival_time(timing_mode, from_clock_edge, to_clock_edge)

class PinFactory:
    """Pin对象工厂，管理Pin的创建和查询"""
    def __init__(self):
        self._pins = {}
    
    def create_pin(self, name, pin_type=None):
        if name in self._pins:
            return self._pins[name]
        
        pin = Pin(name, pin_type)
        self._pins[name] = pin
        return pin
    
    def get_pin(self, name):
        return self._pins.get(name)
    
    def get_all_pins(self):
        return list(self._pins.values())