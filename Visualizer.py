import re
import sys
import pygraphviz as pgv

import Arc
from Cell import Cell
import CircuitBuilder
from EnumClass import FOREACH_EL_FRF_TRF, EnumClockEdge, EnumPinType, EnumTimingSense, FOREACH_EL_RF
from Pin import Pin

SIGNIFICANT_DIGITS = 10

def format_capacitance(pin: Pin):
    buffer = []
    FOREACH_EL_RF(lambda el, rf: buffer.append(f"c_{el}_{rf}={cap if (cap := pin.get_capacitance(el, rf)) is not None else 0.0:.{SIGNIFICANT_DIGITS}f}"))
    return "\n".join(buffer)

def format_slew(pin: Pin):
    buffer = []
    FOREACH_EL_RF(lambda el, rf: buffer.append(f"s_{el}_{rf}={sl if (sl := pin.get_slew(el, rf)) is not None else 0.0:.{SIGNIFICANT_DIGITS}f}"))
    return "\n".join(buffer)

def format_delay(arc: Arc):
    buffer = []
    def format_arc_delay(el, frf, trf):
        delay = arc.get_delay(el, frf, trf)
        if delay is not None:
            buffer.append(f"d_{el}_{frf}_{trf}={delay:.{SIGNIFICANT_DIGITS}f}")
    FOREACH_EL_FRF_TRF(format_arc_delay)
    return "\n".join(buffer)

def format_at(pin: Pin):
    buffer = []
    FOREACH_EL_RF(lambda el, rf: buffer.append(f"at_{el}_{rf}={at if (at := pin.get_arrival_time(el, rf)) is not None else 0.0:.{SIGNIFICANT_DIGITS}f}"))
    return "\n".join(buffer)

def format_rat(pin: Pin):
    buffer = []
    FOREACH_EL_RF(lambda el, rf: buffer.append(f"req_at_{el}_{rf}={rat if (rat := pin.get_request_arrival_time(el, rf)) is not None else 0.0:.{SIGNIFICANT_DIGITS}f}"))
    return "\n".join(buffer)

def get_module_name(pin: Pin):
    if '/' in pin.name:
        return pin.name.split('/')[0]
    return None

def get_port_name(pin: Pin):
    if '/' in pin.name:
        return pin.name.split('/')[1]
    return pin.name

class Visualizer:
    def __init__(self, circuit):
        self.circuit: CircuitBuilder = circuit

    def visualize_path(self, path):
        graph = pgv.AGraph(strict=False, directed=True)
        graph.graph_attr['rankdir'] = 'LR'  # 从左到右布局
        pins = {}
        modules = {}
        for info in path:
            pin_name = info['name']
            module_name = get_module_name(info['pin'])
            if module_name is None:
                continue
            if module_name in modules:
                continue
            cell = self.circuit.get_cell(module_name)
            if cell is None:
                continue
            module = modules[module_name] = graph.add_subgraph(name=f"cluster_{module_name}", label=module_name, color='lightgray')
            for name, pin in cell.pins.items():
                port_name = get_port_name(pin)
                label = f"{port_name}\n{format_capacitance(pin)}\n{format_slew(pin)}\n{format_at(pin)}\n{format_rat(pin)}"
                module.add_node(pin.name, label=label)
                for arc in pin.fanin:
                    from_pin = arc.from_pin
                    if get_module_name(from_pin) != module_name: # 只画模块内的连接
                        continue
                    timing_sense_label = "None"
                    if arc.timing_sense is not None:
                        timing_sense_label = arc.timing_sense.name
                    module.add_edge(from_pin.name, pin.name, label=f"{format_delay(arc)}\n{timing_sense_label}")

        last = None
        for info in path:
            pin = info['pin']
            if last is not None:
                if get_module_name(last) == get_module_name(pin): # 同一个模块不画连接
                    last = pin
                    continue
                arc = None
                for _arc in pin.fanin:
                    if _arc.from_pin == last:
                        arc = _arc
                        break
                if arc is not None:
                    graph.add_edge(last.name, pin.name, label=format_delay(arc))
            last = pin
        from_point_name = re.sub(r"[\\\/\[\]]", "_", path[0]['name'])
        end_point_name = re.sub(r"[\\\/\[\]]", "_", path[-1]['name'])
        graph.write(f'path/{from_point_name}_{end_point_name}.dot')


    def visualize(self, output_file="circuit.dot"):
        graph = pgv.AGraph(strict=False, directed=True)
        graph.graph_attr['rankdir'] = 'LR'  # 从左到右布局
        prim_in = graph.add_subgraph(name='cluster_prim_in', label='Primary Inputs', color='lightblue')
        prim_out = graph.add_subgraph(name='cluster_prim_out', label='Primary Outputs', color='lightblue')
        dut = graph.add_subgraph(name='cluster_dut', label='DUT', color='lightgray')

        cell_blocks = {}
        for cell in self.circuit.cells:
            cell_block = dut.add_subgraph(name=f"cluster_{cell.name}", 
                                          label=f"{cell.module}\n{cell.name}",
                                          style='', fillcolor='white')
            cell_blocks[cell.name] = cell_block

        for pin in self.circuit.primary_inputs.values():
            prim_in.add_node(pin.name, label=f"{pin.name}\n{format_capacitance(pin)}")

        for pin in self.circuit.primary_outputs.values():
            prim_out.add_node(pin.name, label=f"{pin.name}\n{format_capacitance(pin)}")

        for arc in self.circuit.get_all_arcs():
            from_pin = arc.from_pin
            to_pin = arc.to_pin
            if '/' in from_pin.name:
                cell_name = from_pin.name.split('/')[0]
                cell_blocks[cell_name].add_node(from_pin.name, label=f"{from_pin.name.split('/')[1]}\n{format_capacitance(from_pin)}\n{format_slew(from_pin)}\n{format_at(from_pin)}\n{format_rat(from_pin)}")
            if '/' in to_pin.name:
                cell_name = to_pin.name.split('/')[0]
                cell_blocks[cell_name].add_node(to_pin.name, label=f"{to_pin.name.split('/')[1]}\n{format_capacitance(to_pin)}\n{format_slew(to_pin)}\n{format_at(to_pin)}\n{format_rat(to_pin)}")
            if arc.timing_sense is not None:
                arc_label = f"{format_delay(arc)}\n{arc.timing_sense.name}"
            else:
                arc_label = f"None"
            graph.add_edge(from_pin.name, to_pin.name, label=arc_label)
        graph.write('circuit.dot')



        # 输出到文件
        graph.write(output_file)
        print(f"Circuit visualization saved to {output_file}", file=sys.stderr)