import sys
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
    def __init__(self, circuit: CircuitBuilder, clock_cycle= 10, clock_rise_at = None, clock_fall_at = None):
        self.circuit: CircuitBuilder = circuit
        self.clock_pin = None
        self.clock_cycle = clock_cycle
        self.clock_rise_at = 0 if clock_rise_at is None else clock_rise_at
        self.clock_fall_at = clock_cycle /2 + self.clock_rise_at if clock_fall_at is None else clock_fall_at

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

    def propagate_request_arrival_time(self):
        for pin in self.circuit.primary_outputs.values():
            def reset_rat(el, rf):
                pin.set_request_arrival_time(el, rf, self.clock_cycle + self.clock_rise_at)
            FOREACH_EL_RF(reset_rat)
        
        for arc in self.circuit.get_all_constraint_arcs():
            assert isinstance(arc, Arc), f"Arc {arc} is not an instance of Arc"
            FOREACH_EL_FRF_TRF(arc.propagate_request_arrival_time)

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
        if self.clock_pin is not None:
            return self.clock_pin
        # 推断时钟引脚
        for cell in self.circuit.cells:
            if "CK" in cell.port_mapping:
                clock_pin_name = cell.port_mapping["CK"]
                clock_pin = self.circuit.get_pin(clock_pin_name)
                if clock_pin and clock_pin.type == EnumPinType.PRIMARY_INPUT:
                    self.clock_pin = clock_pin
                    return clock_pin
        return None
    
    def report_timing(self, delay_type: str, start_type):
        if self.clock_pin is None:
            print("Warning: Clock pin not found, Trying to deduce clock pin...", file=sys.stderr)
            self.clock_pin = self.deduce_clock()

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
                if pin == self.clock_pin:
                    continue
            if start_type == "reg":
                assert self.clock_pin, "Cannot find clock pin for reg2reg or reg2out path"
                if pin in self.circuit.primary_inputs.values() and pin != self.clock_pin:
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
            ratr = pin.request_arrival_time[el][EnumClockEdge.RISING]
            ratf = pin.request_arrival_time[el][EnumClockEdge.FALLING]
            slackr = ratr - atr if atr is not None and ratr is not None else None
            slackf = ratf - atf if atf is not None and ratf is not None else None
            if slackf is None or slackr is None:
                continue
            if slackr > slackf:
                edge = EnumClockEdge.RISING
            else:
                edge = EnumClockEdge.FALLING
            # if delay_type == "max":
            #     if atr > atf:
            #         edge = EnumClockEdge.RISING
            #     else:
            #         edge = EnumClockEdge.FALLING
            # else:
            #     if atr < atf:
            #         edge = EnumClockEdge.RISING
            #     else:
            #         edge = EnumClockEdge.FALLING
            path = []
            while True:
                path.append((pin.name , edge , pin.arrival_time[el][edge]))
                if pin.predecessor[el][edge] is None:
                    paths[f"{start_type}2{end_type}"].append(path[::-1])
                    break
                edge, arc = pin.predecessor[el][edge]
                pin = arc.from_pin
        return paths
                

            
    