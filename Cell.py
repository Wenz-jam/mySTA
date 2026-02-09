from read_liberty import select_cell
from Arc import Lut, EnumTimingSense
from Pin import EnumClockEdge, EnumPinType
class Cell:
    def __init__(self, name, instance, library):
        self.name :str = name
        self.instance = instance
        self.module :str = instance['module']
        self.cell = select_cell(library, self.module)
        self.port_mapping = dict(instance['portlist'])  # cell_port -> net_name
        self.pins = {}  # port_name -> Pin对象

    @staticmethod
    def get_group(timing_info, group_name):
        groups = timing_info.get_groups(group_name)
        if groups:
            return groups[0]
        return None
    
    def create_pins(self, pin_factory):
        """为Cell创建所有Pin"""
        for pin_info in self.cell.get_groups('pin'):
            port_name = pin_info.args[0]
            pin_name = f"{self.name}/{port_name}"
            direction = pin_info.get_attribute('direction')
            pin_type = EnumPinType.to_enum(direction)
            
            pin = pin_factory.create_pin(pin_name, pin_type)
            capacitance = pin_info.get_attribute('capacitance')
            rise_capacitance = pin_info.get_attribute('rise_capacitance')
            fall_capacitance = pin_info.get_attribute('fall_capacitance')
            if capacitance:
                pin.capacitance[EnumClockEdge.RISING] = float(capacitance)
                pin.capacitance[EnumClockEdge.FALLING] = float(capacitance)
            if rise_capacitance:
                pin.capacitance[EnumClockEdge.RISING] = float(rise_capacitance)
            if fall_capacitance:
                pin.capacitance[EnumClockEdge.FALLING] = float(fall_capacitance)
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
                        cell_rise = Cell.get_group(timing_info, 'cell_rise')
                        cell_fall = Cell.get_group(timing_info, 'cell_fall')
                        rise_transition = Cell.get_group(timing_info, 'rise_transition')
                        fall_transition = Cell.get_group(timing_info, 'fall_transition')
                        # 存在情况: 某些arc可能没有cell_rise/fall或transition信息，这时我们可以选择跳过这些arc，或者为它们设置默认值（例如0）。这里我们选择跳过。
                        # 例如'DFFRQX2H7R'的异步复位引脚, PT的时序分析直接切断了他们, 我们在这里也不为他们创建arc.
                        if not all([cell_rise, cell_fall, rise_transition, fall_transition]):
                            continue
                        arc_factory.create_arc(timing_sense, from_pin, to_pin, cell_rise, cell_fall, rise_transition, fall_transition)
