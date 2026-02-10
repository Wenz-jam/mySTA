import pygraphviz as pgv

import Arc
import CircuitBuilder
from EnumClass import EnumClockEdge, EnumTimingSense, FOREACH_EL_RF
from Pin import Pin

SIGNIFICANT_DIGITS = 10

def format_capacitance(pin: Pin):
    buffer = []
    FOREACH_EL_RF(lambda el, rf: buffer.append(f"c_{el}_{rf}={pin.get_capacitance(el, rf):.{SIGNIFICANT_DIGITS}f}"))
    return "\n".join(buffer)

def format_slew(pin: Pin):
    buffer = []
    FOREACH_EL_RF(lambda el, rf: buffer.append(f"s_{el}_{rf}={pin.get_slew(el, rf):.{SIGNIFICANT_DIGITS}f}"))
    return "\n".join(buffer)

def format_delay(arc: Arc):
    buffer = []
    FOREACH_EL_RF(lambda el, rf: buffer.append(f"d_{el}_{rf}={arc.get_delay(el, rf):.{SIGNIFICANT_DIGITS}f}"))
    return "\n".join(buffer)

def format_at(pin: Pin):
    buffer = []
    FOREACH_EL_RF(lambda el, rf: buffer.append(f"at_{el}_{rf}={pin.get_arrival_time(el, rf):.{SIGNIFICANT_DIGITS}f}"))
    return "\n".join(buffer)

class Visualizer:
    def __init__(self, circuit):
        self.circuit: CircuitBuilder = circuit

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
                cell_blocks[cell_name].add_node(from_pin.name, label=f"{from_pin.name.split('/')[1]}\n{format_capacitance(from_pin)}\n{format_slew(from_pin)}\n{format_at(to_pin)}")
            if '/' in to_pin.name:
                cell_name = to_pin.name.split('/')[0]
                cell_blocks[cell_name].add_node(to_pin.name, label=f"{to_pin.name.split('/')[1]}\n{format_capacitance(to_pin)}\n{format_slew(to_pin)}\n{format_at(to_pin)}")
            graph.add_edge(from_pin.name, to_pin.name, label=format_delay(arc))
        graph.write('circuit.dot')



        # 输出到文件
        graph.write(output_file)
        print(f"Circuit visualization saved to {output_file}")