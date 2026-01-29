from read_liberty import *
from read_verilog import *

class Pin:
    def __init__(self, name, pin_type = None):
        self.name = name
        self.net = None
        self.type = pin_type
        self.capacitance = 0.0
        self.slew = 0.0
        self.arcs = []
    
    def set_net(self, net):
        self.net = net
    
    def add_arc(self, arc):
        self.arcs.append(arc)

from enum import Enum

class EnumPinType(Enum):
    PRIMARY_INPUT = 1
    PRIMARY_OUTPUT = 2
    INPUT = 3
    OUTPUT = 4

to_enum = {
        'input': EnumPinType.INPUT,
        'output': EnumPinType.OUTPUT
}


class Net:
    def __init__(self, name):
        self.name = name
        self.source = None
        self.sinks = []
        self.capacitance = 0.0

    def set_source(self, pin):
        self.source = pin
        pin.set_net(self)
    
    def add_sink(self, pin):
        self.sinks.append(pin)
        pin.set_net(self)

class Arc:
    def __init__(self, from_pin, to_pin):
        self.from_pin = from_pin
        self.to_pin = to_pin
        self.slew = 0.0
        self.delay = 0.0
        from_pin.arcs.append(self)
        to_pin.arcs.append(self)

class Cell:
    def __init__(self, name , instance):
        self.name = name
        self.module = instance['module']
        self.cell = select_cell(library, self.module)
        self.cellport2pin = dict(instance['portlist'])
        self.pin2cellport = {v: k for k, v in self.cellport2pin.items()}
    
    def get_pins(self):
        return self.cell.get_groups('pin')



_nets = {}
def insert_net(name):
    if name in _nets:
        return _nets[name]
    net = Net(name)
    _nets[name] = net
    return net

def connetct_pin_to_net(pin : Pin, net : Net):
    if pin.type == EnumPinType.INPUT:
        net.add_sink(pin)
    elif pin.type == EnumPinType.PRIMARY_INPUT:
        net.set_source(pin)
    elif pin.type == EnumPinType.PRIMARY_OUTPUT:
        net.add_sink(pin)
    elif pin.type == EnumPinType.OUTPUT or pin.type:
        net.set_source(pin)
    else:
        raise ValueError(f"Unknown pin type: {pin.type}")

for name in wires:
    insert_net(name)

_primary_input = {}
def insert_primary_input(name):
    if name in _primary_input:
        return _primary_input[name]
    pin = Pin(name , EnumPinType.PRIMARY_INPUT)
    _primary_input[name] = pin
    return pin

for name in inputs:
    pin = insert_primary_input(name)
    net = insert_net(name)
    connetct_pin_to_net(pin, net)

_primary_output = {}
def insert_primary_output(name):
    pin = Pin(name, EnumPinType.PRIMARY_OUTPUT)
    _primary_output[name] = pin
    return pin

for name in outputs:
    pin = insert_primary_output(name)
    net = insert_net(name)
    connetct_pin_to_net(pin, net)


_pins = {}
_arcs = {}

def insert_pin(name, type = None):
    if name in _pins:
        return _pins[name]
    pin = Pin(name, type)
    _pins[name] = pin
    return pin

def generate_pin_name(cell_name, port_name):
    # AND instance1 ( .A(net1), .B(net2), .Y(net3) );
    # return "instance1/A"
    return f"{cell_name}/{port_name}"

for instance_name, instance in instances.items(): # TODO: 根据笔记分三步走创建Pin, 插入Net, 创建Arc
    cell = Cell(instance_name, instance)
    for instance_pin in cell.get_pins():
        port_name = instance_pin.args[0] # 这个是门的pin名称, 比如说AND(A, B, Y)中的A,B,Y
        pin_name = generate_pin_name(instance_name, port_name)
        pin = insert_pin(pin_name, to_enum.get(instance_pin.get_attribute('direction'), None))
    for instance_pin in cell.get_pins():
        port_name = instance_pin.args[0]
        pin_name = generate_pin_name(instance_name, port_name)
        pin = _pins.get(pin_name, None)
        assert pin is not None
        net_name = cell.cellport2pin.get(port_name, None)
        assert net_name is not None
        net = _nets.get(net_name, None)
        assert net is not None
        connetct_pin_to_net(pin, net)
    for instance_pin in cell.get_pins():
        port_name = instance_pin.args[0]
        pin_name = generate_pin_name(instance_name, port_name)
        pin = _pins.get(pin_name, None)
        assert pin is not None
        if pin.type == EnumPinType.OUTPUT:
            arcs_info = instance_pin.get_groups('timing')
            for arc_info in arcs_info:
                from_port_name = arc_info.get_attribute('related_pin').value
                from_pin_name = generate_pin_name(instance_name, from_port_name)
                from_pin = _pins.get(from_pin_name, None)
                assert from_pin is not None
                arc = Arc(from_pin, pin)
                arc_key = f"{from_pin_name}:{pin_name}"
                _arcs[arc_key] = arc

for _ , net in _nets.items():
    assert isinstance(net, Net)
    assert net.source is not None
    assert net.source.net == net

for _ , net in _nets.items():
    assert isinstance(net, Net)
    for sink in net.sinks:
        assert sink.net == net

for _ , pin in _pins.items():
    assert isinstance(pin, Pin)
    if len(pin.arcs) == 0:
        continue
    pin_set = set()
    for arc in pin.arcs:
        pin_set.add(arc.from_pin)
        pin_set.add(arc.to_pin)
    assert len(pin_set) == len(pin.arcs) + 1 # arc + pin本身

pass