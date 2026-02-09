from enum import Enum

from EnumClass import EnumClockEdge, EnumPinType
class Pin:
    def __init__(self, name, pin_type=None):
        self.name = name
        self.net = None
        self.type = pin_type  # 避免与Python的type关键字冲突
        self.capacitance = {EnumClockEdge.RISING: 0.0, EnumClockEdge.FALLING: 0.0}
        self.slew = {EnumClockEdge.RISING: 0.0, EnumClockEdge.FALLING: 0.0}
        self.arcs = None # decrapated
        self.fanin = []
        self.fanout = []
    
    def __repr__(self):
        return f"Pin({self.name}, type={self.type})"
    
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