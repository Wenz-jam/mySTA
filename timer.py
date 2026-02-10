from Arc import Arc, EnumTimingSense
import CircuitBuilder
from Pin import Pin
from EnumClass import ALL_CLOCK_EDGES, ALL_TIMING_MODES, FOREACH_EL_FRF_TRF, FOREACH_EL_RF, EnumClockEdge, EnumPinType, EnumTimingMode

def toposort(circuit: CircuitBuilder):
    visited = set()
    stack = []

    def dfs(pin: Pin):
        if pin in visited:
            return
        visited.add(pin)
        for arc in pin.fanout:
            dfs(arc.to_pin)
        stack.append(pin)

    for pin in circuit.primary_inputs.values():
        dfs(pin)

    return stack[::-1]  # Reverse the stack to get the correct order

def get_all_paths(start_pin: Pin, path):
    if len(start_pin.fanout) == 0:
        yield path.copy()
        return
    for arc in start_pin.fanout:
        assert isinstance(arc, Arc), f"Arc {arc} is not an instance of Arc"
        path.append(arc)
        yield from get_all_paths(arc.to_pin, path)
        path.pop()

class Timer:
    def __init__(self, circuit: CircuitBuilder):
        self.circuit: CircuitBuilder = circuit
        self.all_timing_paths = []

    def update_capacitance(self):
        for pin in self.circuit.pin_factory.get_all_pins():
            assert isinstance(pin, Pin), f"Pin {pin} is not an instance of Pin"
            if pin.type in (EnumPinType.PRIMARY_OUTPUT, EnumPinType.INPUT):
                continue
            FOREACH_EL_RF(pin.update_capacitance)

    def propagate_slew(self):
        # 拓扑排序所有Pin, 传播slew
        for pin in toposort(self.circuit):
            assert isinstance(pin, Pin), f"Pin {pin} is not an instance of Pin"
            FOREACH_EL_FRF_TRF(pin.propagate_slew)
    
    def propagate_delay(self):
        # 拓扑排序所有Pin, 传播delay
        for pin in toposort(self.circuit):
            assert isinstance(pin, Pin), f"Pin {pin} is not an instance of Pin"
            FOREACH_EL_FRF_TRF(pin.propagate_delay)
    
    def propagate_arrival_time(self):
        # 拓扑排序所有Pin, 传播arrival_time
        for pin in toposort(self.circuit):
            assert isinstance(pin, Pin), f"Pin {pin} is not an instance of Pin"
            FOREACH_EL_FRF_TRF(pin.propagate_arrival_time)
    
    def reset_arrival_time(self):
        for pin in self.circuit.pin_factory.get_all_pins():
            assert isinstance(pin, Pin), f"Pin {pin} is not an instance of Pin"
            if pin.type == EnumPinType.PRIMARY_INPUT:
                pin.set_arrival_time(EnumTimingMode.MAX, EnumClockEdge.RISING, 0)
                pin.set_arrival_time(EnumTimingMode.MAX, EnumClockEdge.FALLING, 0)
                continue
            def reset_at(el, rf):
                pin.set_arrival_time(el, rf, None)
                pin.set_arrival_time(el, rf, None)
            FOREACH_EL_RF(reset_at)
    
    def deduce_clock(self):
        # 推断时钟引脚
        for cell in self.circuit.cells:
            if "CK" in cell.port_mapping:
                clock_pin_name = cell.port_mapping["CK"]
                clock_pin = self.circuit.get_pin(clock_pin_name)
                if clock_pin and clock_pin.type == EnumPinType.PRIMARY_INPUT:
                    return clock_pin
        return None
    
    def report_timing(self, delay_type: str, start_type):
        module_clock_pin = self.deduce_clock()
        paths = {
            "in2reg": [],
            "in2out": [],
            "reg2reg": [],
            "reg2out": []
        }
        self.reset_arrival_time()
        # 拓扑排序所有Pin, 传播arrival_time
        for pin in toposort(self.circuit):
            assert isinstance(pin, Pin), f"Pin {pin} is not an instance of Pin"
            if start_type == "in":
                if pin == module_clock_pin:
                    continue
            if start_type == "reg":
                assert module_clock_pin, "Cannot find clock pin for reg2reg or reg2out path"
                if pin in self.circuit.primary_inputs.values() and pin != module_clock_pin:
                    continue
            FOREACH_EL_FRF_TRF(pin.propagate_arrival_time)
        el = EnumTimingMode.to_enum(delay_type)
        # 从所有没有fanout的Pin开始回溯, 生成路径
        endpoints = [pin for pin in self.circuit.pin_factory.get_all_pins() if len(pin.fanout) == 0]
        for end_pin in endpoints:
            if end_pin.type == EnumPinType.PRIMARY_OUTPUT:
                end_type = "out"
            elif end_pin.type == EnumPinType.INPUT:
                end_type = "reg"
            else:
                continue
            pin = end_pin
            assert isinstance(end_pin, Pin), f"Pin {end_pin} is not an instance of Pin"
            atr = pin.arrival_time[el][EnumClockEdge.RISING]
            atf = pin.arrival_time[el][EnumClockEdge.FALLING]
            if atr is None or atf is None:
                continue
            if delay_type == "max":
                if atr > atf:
                    edge = EnumClockEdge.RISING
                else:
                    edge = EnumClockEdge.FALLING
            else:
                if atr < atf:
                    edge = EnumClockEdge.RISING
                else:
                    edge = EnumClockEdge.FALLING
            path = []
            while True:
                path.append((pin.name , edge , pin.arrival_time[el][edge]))
                if pin.predecessor[el][edge] is None:
                    paths[f"{start_type}2{end_type}"].append(path[::-1])
                    break
                edge, arc = pin.predecessor[el][edge]
                pin = arc.from_pin
        return paths
                

            
    