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
    
    def report_all_path(self):
        # 推断时钟引脚
        module_clock_pin = None
        for cell in self.circuit.cells:
            if "CK" in cell.port_mapping:
                clock_pin_name = cell.port_mapping["CK"]
                clock_pin = self.circuit.get_pin(clock_pin_name)
                if clock_pin and clock_pin.type == EnumPinType.PRIMARY_INPUT:
                    module_clock_pin = clock_pin
                    break
        classified_paths = {
            "max":{
                    "in2reg": [],
                    "in2out": [],
                    "reg2reg": [],
                    "reg2out": []
            },
            "min":{
                    "in2reg": [],
                    "in2out": [],
                    "reg2reg": [],
                    "reg2out": []
            }
        }
        for pin in toposort(self.circuit):
            if pin in self.circuit.primary_inputs.values() and pin != module_clock_pin:
                continue
            assert isinstance(pin, Pin), f"Pin {pin} is not an instance of Pin"
            FOREACH_EL_FRF_TRF(pin.propagate_arrival_time)
        endpoints = [pin for pin in self.circuit.pin_factory.get_all_pins() if len(pin.fanout) == 0]
        el = "max"
        for el in ["max", "min"]:
            for end_pin in endpoints:
                assert isinstance(end_pin, Pin), f"Pin {end_pin} is not an instance of Pin"
                pin = end_pin
                path = []
                while True:
                    ats = pin.arrival_time[EnumTimingMode.to_enum(el)]
                    preds = pin.predecessor[EnumTimingMode.to_enum(el)]
                    if ats[EnumClockEdge.RISING] is None and ats[EnumClockEdge.FALLING] is None:
                        break
                    if el == "max":
                        if ats[EnumClockEdge.RISING] > ats[EnumClockEdge.FALLING]:
                            pred = preds[EnumClockEdge.RISING]
                            clock_edge = EnumClockEdge.RISING
                        else:
                            pred = preds[EnumClockEdge.FALLING]
                            clock_edge = EnumClockEdge.FALLING
                    if el == "min":
                        if ats[EnumClockEdge.RISING] < ats[EnumClockEdge.FALLING]:
                            pred = preds[EnumClockEdge.RISING]
                            clock_edge = EnumClockEdge.RISING
                        else:
                            pred = preds[EnumClockEdge.FALLING]
                            clock_edge = EnumClockEdge.FALLING
                    path.append((pin.name, clock_edge, ats[clock_edge]))
                    if pred is not None:
                        pin = pred.from_pin
                        continue
                    if pin.name == module_clock_pin.name:
                        path.pop() # 去掉时钟引脚
                    path = path[::-1] # 反转路径
                    pin = self.circuit.get_pin(path[0][0])
                    if pin.type == EnumPinType.PRIMARY_INPUT:
                        input_type = "in"
                    elif pin.type == EnumPinType.INPUT:
                        input_type = "reg"
                    else:
                        break
                        raise ValueError(f"Unexpected start pin type {pin.type} for pin {pin.name}"
                                        f"path: {[pin.name for pin in path]}")
                    pin = self.circuit.get_pin(path[-1][0])
                    if pin.type == EnumPinType.PRIMARY_OUTPUT:
                        output_type = "out"
                    elif pin.type == EnumPinType.INPUT:
                        output_type = "reg"
                    else:
                        break
                        raise ValueError(f"Unexpected end pin type {pin.type} for pin {pin.name}"
                                        f"path: {[pin.name for pin in path]}")
                    path_type = f"{input_type}2{output_type}"
                    classified_paths[el][path_type].append(path)
                    break
        for pin in self.circuit.get_all_pins():
            if pin.type == EnumPinType.PRIMARY_INPUT:
                continue
            def reset_at(el, rf):
                pin.arrival_time[el][rf] = None
                pin.arrival_time[el][rf] = None
            FOREACH_EL_RF(reset_at)
        for pin in toposort(self.circuit):
            if pin == module_clock_pin:
                continue
            assert isinstance(pin, Pin), f"Pin {pin} is not an instance of Pin"
            FOREACH_EL_FRF_TRF(pin.propagate_arrival_time)
        endpoints = [pin for pin in self.circuit.pin_factory.get_all_pins() if len(pin.fanout) == 0]
        el = "max"
        for el in ["max", "min"]:
            for end_pin in endpoints:
                assert isinstance(end_pin, Pin), f"Pin {end_pin} is not an instance of Pin"
                pin = end_pin
                path = []
                while True:
                    ats = pin.arrival_time[EnumTimingMode.to_enum(el)]
                    preds = pin.predecessor[EnumTimingMode.to_enum(el)]
                    if ats[EnumClockEdge.RISING] is None and ats[EnumClockEdge.FALLING] is None:
                        break
                    if el == "max":
                        if ats[EnumClockEdge.RISING] > ats[EnumClockEdge.FALLING]:
                            pred = preds[EnumClockEdge.RISING]
                            clock_edge = EnumClockEdge.RISING
                        else:
                            pred = preds[EnumClockEdge.FALLING]
                            clock_edge = EnumClockEdge.FALLING
                    if el == "min":
                        if ats[EnumClockEdge.RISING] < ats[EnumClockEdge.FALLING]:
                            pred = preds[EnumClockEdge.RISING]
                            clock_edge = EnumClockEdge.RISING
                        else:
                            pred = preds[EnumClockEdge.FALLING]
                            clock_edge = EnumClockEdge.FALLING
                    path.append((pin.name, clock_edge, ats[clock_edge]))
                    if pred is not None:
                        pin = pred.from_pin
                        continue
                    if pin.name == module_clock_pin.name:
                        path.pop() # 去掉时钟引脚
                    path = path[::-1] # 反转路径
                    pin = self.circuit.get_pin(path[0][0])
                    if pin.type == EnumPinType.PRIMARY_INPUT:
                        input_type = "in"
                    elif pin.type == EnumPinType.INPUT:
                        input_type = "reg"
                    else:
                        break
                        raise ValueError(f"Unexpected start pin type {pin.type} for pin {pin.name}"
                                        f"path: {[pin.name for pin in path]}")
                    pin = self.circuit.get_pin(path[-1][0])
                    if pin.type == EnumPinType.PRIMARY_OUTPUT:
                        output_type = "out"
                    elif pin.type == EnumPinType.INPUT:
                        output_type = "reg"
                    else:
                        break
                        raise ValueError(f"Unexpected end pin type {pin.type} for pin {pin.name}"
                                        f"path: {[pin.name for pin in path]}")
                    path_type = f"{input_type}2{output_type}"
                    classified_paths[el][path_type].append(path)
                    break
        return classified_paths
                

            
    