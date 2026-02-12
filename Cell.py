from EnumClass import EnumTimingSense, EnumTimingType
from read_liberty import select_cell
from Arc import ArcFactory, Lut, EnumTimingMode
from Pin import EnumClockEdge, EnumPinType, Pin
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
            
            pin:Pin = pin_factory.create_pin(pin_name, pin_type)
            capacitance = pin_info.get_attribute('capacitance')
            rise_capacitance = pin_info.get_attribute('rise_capacitance')
            fall_capacitance = pin_info.get_attribute('fall_capacitance')
            rise_capacitance_range = pin_info.get_attribute('rise_capacitance_range')
            fall_capacitance_range = pin_info.get_attribute('fall_capacitance_range')
            if rise_capacitance_range:
                min_cap, max_cap = rise_capacitance_range
                pin.set_capacitance(EnumTimingMode.MIN, EnumClockEdge.RISING, min_cap)
                pin.set_capacitance(EnumTimingMode.MAX, EnumClockEdge.RISING, max_cap)
            elif rise_capacitance:
                pin.set_capacitance(EnumTimingMode.MIN, EnumClockEdge.RISING, rise_capacitance)
                pin.set_capacitance(EnumTimingMode.MAX, EnumClockEdge.RISING, rise_capacitance)
            else:
                pin.set_capacitance(EnumTimingMode.MIN, EnumClockEdge.RISING, capacitance)
                pin.set_capacitance(EnumTimingMode.MAX, EnumClockEdge.RISING, capacitance)
            if fall_capacitance_range:
                min_cap, max_cap = fall_capacitance_range
                pin.set_capacitance(EnumTimingMode.MIN, EnumClockEdge.FALLING, min_cap)
                pin.set_capacitance(EnumTimingMode.MAX, EnumClockEdge.FALLING, max_cap)
            elif fall_capacitance:
                pin.set_capacitance(EnumTimingMode.MIN, EnumClockEdge.FALLING, fall_capacitance)
                pin.set_capacitance(EnumTimingMode.MAX, EnumClockEdge.FALLING, fall_capacitance)
            else:
                pin.set_capacitance(EnumTimingMode.MIN, EnumClockEdge.FALLING, capacitance)
                pin.set_capacitance(EnumTimingMode.MAX, EnumClockEdge.FALLING, capacitance)
            self.pins[port_name] = pin
    
    def connect_pins_to_nets(self, net_factory):
        """将Cell的Pin连接到对应的Net"""
        for port_name, pin in self.pins.items():
            net_name = self.port_mapping.get(port_name)
            if net_name:
                net = net_factory.get_net(net_name)
                if net:
                    pin.connect_to_net(net)

    def create_arcs(self, arc_factory: ArcFactory):
        """为Cell创建所有时序弧"""
        for pin_info in self.cell.get_groups('pin'):
            port_name = pin_info.args[0]
            to_pin = self.pins.get(port_name)

            
            for timing_info in pin_info.get_groups('timing'):
                # 目前只处理组合逻辑和时序逻辑的arc
                timing_type = timing_info.get_attribute('timing_type')
                timing_type = EnumTimingType.to_enum(timing_type) if timing_type is not None else None
                if not EnumTimingType.is_sequential(timing_type) and not EnumTimingType.is_combinational(timing_type):
                    continue

                related_pin_name = timing_info.get_attribute('related_pin')
                assert related_pin_name is not None, f"Pin {port_name} in cell {self.name} does not have a related_pin attribute"
                from_pin = self.pins.get(related_pin_name.value)
                assert from_pin is not None, f"Related pin {related_pin_name.value} for pin {port_name} in cell {self.name} not found"
                
                timing_sense = timing_info.get_attribute('timing_sense')
                timing_sense = EnumTimingSense.to_enum(timing_sense) if timing_sense is not None else None

                cell_rise = Cell.get_group(timing_info, 'cell_rise')
                cell_fall = Cell.get_group(timing_info, 'cell_fall')
                rise_transition = Cell.get_group(timing_info, 'rise_transition')
                fall_transition = Cell.get_group(timing_info, 'fall_transition')
                rise_constraint = Cell.get_group(timing_info, 'rise_constraint')
                fall_constraint = Cell.get_group(timing_info, 'fall_constraint')

                arc = arc_factory.create_arc(timing_type,
                                        timing_sense,
                                        from_pin,
                                        to_pin,
                                        cell_rise,
                                        cell_fall,
                                        rise_transition,
                                        fall_transition,
                                        rise_constraint,
                                        fall_constraint)
                
                arc.sdf_cond = timing_info.get_attribute('sdf_cond')
