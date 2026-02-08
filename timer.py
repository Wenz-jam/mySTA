from Arc import Arc, EnumTimingSense
import CircuitBuilder
from Pin import EnumClockEdge, EnumPinType, Pin

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
            if pin.type in (EnumPinType.PRIMARY_INPUT, EnumPinType.OUTPUT):
                pin.capacitance = sum([arc.to_pin.capacitance for arc in pin.fanout])
    
    def propagate_slew(self):
        clock_edges = [EnumClockEdge.RISING, EnumClockEdge.FALLING]
        # 拓扑排序所有Pin, 传播slew
        for pin in toposort(self.circuit):
            assert isinstance(pin, Pin), f"Pin {pin} is not an instance of Pin"
            for clock_edge_from_rise in clock_edges:
                for arc in pin.fanout:
                    assert isinstance(arc, Arc), f"Arc {arc} is not an instance of Arc"
                    arc.propagate_slew(clock_edge_from_rise)

    def calc_delay(self):
        clock_edges = [EnumClockEdge.RISING, EnumClockEdge.FALLING]
        # 拓扑排序所有Pin, 计算delay
        for pin in toposort(self.circuit):
            assert isinstance(pin, Pin), f"Pin {pin} is not an instance of Pin"
            for clock_edge_from_rise in clock_edges:
                for arc in pin.fanout:
                    assert isinstance(arc, Arc), f"Arc {arc} is not an instance of Arc"
                    arc.calc_delay(clock_edge_from_rise)
    
    def report_all_path(self):
        self.all_timing_paths = []
        for pin in self.circuit.primary_inputs.values():
            for path in get_all_paths(pin, []):
                if len(path) == 0:
                    continue
                timing_path_bad = []
                path_from_rise = [(pin.name, EnumClockEdge.RISING  , 0.0)] # pin name, clock edge, delay
                path_from_fall = [(pin.name, EnumClockEdge.FALLING , 0.0)]
                clock_edge_from_rise = EnumClockEdge.RISING
                clock_edge_from_fall = EnumClockEdge.FALLING

                for arc in path:
                    assert isinstance(arc, Arc), f"Arc {arc} is not an instance of Arc"
                    clock_edge_from_rise = arc.get_to_pin_clock_edge(clock_edge_from_rise)
                    clock_edge_from_fall = arc.get_to_pin_clock_edge(clock_edge_from_fall)
                    if arc.timing_sense == EnumTimingSense.NON_UNATE:
                        delay_from_rise = sum([delay for _, _, delay in path_from_rise])
                        delay_from_fall = sum([delay for _, _, delay in path_from_fall])
                        worse_path = path_from_rise if delay_from_rise >= delay_from_fall else path_from_fall
                        timing_path_bad.extend(worse_path)
                        path_from_rise.clear()
                        path_from_fall.clear()
                        clock_edge_from_rise = EnumClockEdge.RISING
                        clock_edge_from_fall = EnumClockEdge.FALLING
                    path_from_rise.append((arc.to_pin.name, clock_edge_from_rise, arc.delay[clock_edge_from_rise]))
                    path_from_fall.append((arc.to_pin.name, clock_edge_from_fall, arc.delay[clock_edge_from_fall]))
                # 处理剩余路径
                delay_from_rise = sum([delay for _, _, delay in path_from_rise])
                delay_from_fall = sum([delay for _, _, delay in path_from_fall])
                worse_path = path_from_rise if delay_from_rise >= delay_from_fall else path_from_fall
                timing_path_bad.extend(worse_path)
                self.all_timing_paths.append(timing_path_bad)
        
        return self.all_timing_paths
    