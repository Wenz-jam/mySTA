from read_liberty import *
from CircuitBuilder import CircuitBuilder, build_circuit
from VerilogParser import VerilogParser
from Pin import EnumClockEdge, EnumPinType, Pin
from Arc import Arc, EnumTimingSense


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




def main():
    verilog_file = "/home/wenz/git/mySTA/example/simple.v"
    # verilog_file = '/home/wenz/git/mySTA/example/gcd.netlist.v'
    # verilog_file = '/home/wenz/git/mySTA/example/ysyx_23060004.netlist.v'
    top_module = "top"
    parser = VerilogParser()
    module = parser.parse_file(verilog_file)
    if(len(module) == 1):
        module = module.get(next(iter(module)), None)
        assert module is not None, f"Module not found in {verilog_file}"
    else:
        module = module.get(top_module, None)
        assert module is not None, f"Top module {top_module} not found in {verilog_file}"

    wires = module.wires
    inputs = module.inputs
    outputs = module.outputs
    instances = module.instances

    # 构建电路
    circuit = build_circuit(library, wires, inputs, outputs, instances)
    
    # 获取所有Pin、Net、Arc用于后续分析
    all_pins = circuit.pin_factory.get_all_pins()
    all_nets = circuit.net_factory.get_all_nets()
    all_arcs = circuit.arc_factory.get_all_arcs()
    
    print(f"\nReady for PBA analysis with {len(all_pins)} pins, {len(all_nets)} nets, {len(all_arcs)} arcs")

    # 遍历所有输出Pin, 汇总其负载电容
    for pin in circuit.pin_factory.get_all_pins():
        assert isinstance(pin, Pin), f"Pin {pin} is not an instance of Pin"
        if pin.type in (EnumPinType.PRIMARY_INPUT, EnumPinType.OUTPUT):
            pin.capacitance = sum([arc.to_pin.capacitance for arc in pin.fanout])

    clock_edges = [EnumClockEdge.RISING, EnumClockEdge.FALLING]
    # 拓扑排序所有Pin, 传播slew
    for pin in toposort(circuit):
        assert isinstance(pin, Pin), f"Pin {pin} is not an instance of Pin"
        for clock_edge_from_rise in clock_edges:
            for arc in pin.fanout:
                assert isinstance(arc, Arc), f"Arc {arc} is not an instance of Arc"
                arc.propagate_slew(clock_edge_from_rise)

    # 拓扑排序所有Pin, 计算delay
    for pin in toposort(circuit):
        assert isinstance(pin, Pin), f"Pin {pin} is not an instance of Pin"
        for clock_edge_from_rise in clock_edges:
            for arc in pin.fanout:
                arc.calc_delay(clock_edge_from_rise)
                
        # for arc in pin.fanout:
        #     to_pin = arc.to_pin
        #     slew = pin.slew
        #     capacitance = to_pin.capacitance
        #     to_pin.slew = max(to_pin.slew, arc.get_slew(slew, capacitance))
        #     arc.slew = arc.get_slew(slew, capacitance)
        #     arc.delay = max(arc.delay, arc.get_delay(slew, capacitance)) # 这里是否需要max? 
    all_timing_paths = []
    for pin in circuit.primary_inputs.values():
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
            all_timing_paths.append(timing_path_bad)
    
    if __name__ != '__main__':
        return all_timing_paths
    
    # 输出路径
    for timing_path_bad in all_timing_paths:
        print("Timing Path:")
        total_delay = 0
        for name, clock_edge_from_rise, delay in timing_path_bad:
            total_delay += delay
            print(f"{name:<15} {clock_edge_from_rise.name:<8} delay: {delay:.10f} ns, total_delay: {total_delay:.10f} ns")
        print("-"*20)

    import pygraphviz as pgv
    G = pgv.AGraph(directed=True)
    G.graph_attr['rankdir'] = 'LR'
    # G.graph_attr['splines'] = 'ortho'
    prim_in = G.add_subgraph(name='cluster_inputs', label='Primary Inputs', color='blue', rank='source')
    prim_out = G.add_subgraph(name='cluster_outputs', label='Primary Outputs', color='blue', rank='sink')
    dut = G.add_subgraph(name='cluster_dut', label='DUT', color='black', rank= 'middle', style="invis")
    cell_blocks = {}
    for cell in circuit.cells:
        cell_block = dut.add_subgraph(name=f"cluster_{cell.name}", 
                                      label=f"{cell.module}\n{cell.name}",
                                      style='',
                                      color= 'red' if 'FF' in cell.module else 'black')
        cell_blocks[cell.name] = cell_block
    
    for pin in circuit.primary_inputs.values():
        prim_in.add_node(pin.name, label=f"{pin.name}\nc={pin.capacitance:.6f}")

    for pin in circuit.primary_outputs.values():
        prim_out.add_node(pin.name, label=f"{pin.name}\nc={pin.capacitance:.6f}")

    for arc in all_arcs:
        from_pin = arc.from_pin
        to_pin = arc.to_pin
        if '/' in from_pin.name:
            cell_name = from_pin.name.split('/')[0]
            cell_blocks[cell_name].add_node(from_pin.name, label=f"{from_pin.name.split('/')[1]}\nc={from_pin.capacitance:.6f}\ns_f={from_pin.slew[EnumClockEdge.FALLING]:.6f}\ns_r={from_pin.slew[EnumClockEdge.RISING]:.6f}")
        if '/' in to_pin.name:
            cell_name = to_pin.name.split('/')[0]
            cell_blocks[cell_name].add_node(to_pin.name, label=f"{to_pin.name.split('/')[1]}\nc={to_pin.capacitance:.6f}\ns_f={to_pin.slew[EnumClockEdge.FALLING]:.6f}\ns_r={to_pin.slew[EnumClockEdge.RISING]:.6f}")
        G.add_edge(from_pin.name, to_pin.name, label=f"d_f={arc.delay[EnumClockEdge.FALLING]:.6f}\nd_r={arc.delay[EnumClockEdge.RISING]:.6f}\ns_f={arc.slew[EnumClockEdge.FALLING]:.6f}\ns_r={arc.slew[EnumClockEdge.RISING]:.6f}",
                   color = 'red' if arc.timing_sense == EnumTimingSense.POS_UNATE else ('blue' if arc.timing_sense == EnumTimingSense.NEG_UNATE else 'black'))
    G.write('circuit.dot')

    P = pgv.AGraph(directed=True)
    # P.graph_attr['rankdir'] = 'LR'
    for idx, timing_path in enumerate(all_timing_paths):
        path_subgraph = P.add_subgraph(name=f'cluster_path_{idx}', label=f'Timing Path {idx}', color='green')
        total_delay = 0.0
        for name, clock_edge, delay in timing_path:
            total_delay += delay
            path_subgraph.add_node(f"{name}_{idx}", label=f"{name}\n{clock_edge.name}\ndelay={delay:.6f} ns\ntotal={total_delay:.6f} ns")
        for i in range(len(timing_path)-1):
            from_name, _, _ = timing_path[i]
            to_name, _, _ = timing_path[i+1]
            path_subgraph.add_edge(f"{from_name}_{idx}", f"{to_name}_{idx}")
    P.write('timing_paths.dot')

if __name__ == '__main__':
    main()