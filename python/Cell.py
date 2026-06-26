from read_liberty import select_cell
from Arc import ArcFactory
from EnumClass import EnumClockEdge, EnumPinType, EnumTimingMode
from Pin import Pin
class Cell:
    def __init__(self, name, instance, library):
        self.name :str = name
        self.instance = instance
        self.module :str = instance['module']
        self.cell = select_cell(library, self.module)
        self.port_mapping = dict(instance['portlist'])  # cell_port -> net_name
        self.pins = {}  # port_name -> Pin对象

    @staticmethod
    def _lut_by_edge(luts, clock_edge):
        index = 1 if clock_edge == EnumClockEdge.RISING else 0
        if index >= len(luts):
            return None
        return luts[index]

    @staticmethod
    def get_group(timing_info, group_name):
        return None
    
    def create_pins(self, pin_factory):
        """为Cell创建所有Pin"""
        for port_info in self.cell.ports:
            port_name = port_info.name
            pin_name = f"{self.name}/{port_name}"
            pin_type = EnumPinType.to_enum(port_info.pin_type)
            
            pin:Pin = pin_factory.create_pin(pin_name, pin_type)
            pin.set_capacitance(EnumTimingMode.MAX, EnumClockEdge.FALLING, port_info.capacitance[0][0])
            pin.set_capacitance(EnumTimingMode.MAX, EnumClockEdge.RISING, port_info.capacitance[0][1])
            pin.set_capacitance(EnumTimingMode.MIN, EnumClockEdge.FALLING, port_info.capacitance[1][0])
            pin.set_capacitance(EnumTimingMode.MIN, EnumClockEdge.RISING, port_info.capacitance[1][1])
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
        for arc_info in self.cell.arcs:
            from_pin = self.pins.get(arc_info.src_port)
            to_pin = self.pins.get(arc_info.snk_port)
            assert from_pin is not None, f"Related pin {arc_info.src_port} for cell {self.name} not found"
            assert to_pin is not None, f"Sink pin {arc_info.snk_port} for cell {self.name} not found"

            arc = arc_factory.create_arc(
                arc_info.timing_type,
                arc_info.timing_sense,
                from_pin,
                to_pin,
                Cell._lut_by_edge(arc_info.delay_luts, EnumClockEdge.RISING),
                Cell._lut_by_edge(arc_info.delay_luts, EnumClockEdge.FALLING),
                Cell._lut_by_edge(arc_info.slew_luts, EnumClockEdge.RISING),
                Cell._lut_by_edge(arc_info.slew_luts, EnumClockEdge.FALLING),
                Cell._lut_by_edge(arc_info.constraint_luts, EnumClockEdge.RISING),
                Cell._lut_by_edge(arc_info.constraint_luts, EnumClockEdge.FALLING),
            )
            arc.sdf_cond = None
