from read_liberty import select_cell
from Arc import Lut, EnumTimingSense
from Pin import EnumPinType
class Cell:
    def __init__(self, name, instance, library):
        self.name :str = name
        self.instance = instance
        self.module :str = instance['module']
        self.cell = select_cell(library, self.module)
        self.port_mapping = dict(instance['portlist'])  # cell_port -> net_name
        self.pins = {}  # port_name -> Pin对象
    
    def create_pins(self, pin_factory):
        """为Cell创建所有Pin"""
        for pin_info in self.cell.get_groups('pin'):
            port_name = pin_info.args[0]
            pin_name = f"{self.name}/{port_name}"
            direction = pin_info.get_attribute('direction')
            pin_type = EnumPinType.to_enum(direction)
            
            pin = pin_factory.create_pin(pin_name, pin_type)
            capacitance = pin_info.get_attribute('capacitance')
            if capacitance:
                pin.capacitance = float(capacitance)
            self.pins[port_name] = pin
    
    def connect_pins_to_nets(self, net_factory):
        """将Cell的Pin连接到对应的Net"""
        for port_name, pin in self.pins.items():
            net_name = self.port_mapping.get(port_name)
            if net_name:
                net = net_factory.get_net(net_name)
                if net:
                    pin.connect_to_net(net)
    
    def create_arcs(self, arc_factory):
        """为Cell创建所有时序弧"""
        for pin_info in self.cell.get_groups('pin'):
            port_name = pin_info.args[0]
            to_pin = self.pins.get(port_name)
            
            # 只处理输出pin的时序弧
            if to_pin and to_pin.type == EnumPinType.OUTPUT:
                for timing_info in pin_info.get_groups('timing'):
                    from_port_name = timing_info.get_attribute('related_pin').value
                    from_pin = self.pins.get(from_port_name)
                    
                    if from_pin:
                        timing_sense = timing_info.get_attribute('timing_sense')
                        cell_rise = timing_info.get_group('cell_rise')
                        cell_fall = timing_info.get_group('cell_fall')
                        rise_transition = timing_info.get_group('rise_transition')
                        fall_transition = timing_info.get_group('fall_transition')
                        arc_factory.create_arc(timing_sense, from_pin, to_pin, cell_rise, cell_fall, rise_transition, fall_transition)
