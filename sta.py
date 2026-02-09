from read_liberty import libs as library
from CircuitBuilder import CircuitBuilder, build_circuit
from VerilogParser import VerilogParser
from Pin import EnumClockEdge, EnumPinType, Pin
from Arc import Arc, EnumTimingSense
from timer import Timer

__debug_export__ = {
    "circuit": None,
    "timer": None,
    "all_timing_paths": None
}



def main(verilog_file = "/home/wenz/git/mySTA/report/simple/simple.v"):
    if __name__ == '__main__':
        verilog_file = "/home/wenz/git/mySTA/report/Booth_Multiplier/Booth_Multiplier.v"
        verilog_file = "/home/wenz/git/mySTA/report/ascon/ascon.v"
        verilog_file = "/home/wenz/git/mySTA/report/s5378/s5378.v"
        verilog_file = "/home/wenz/git/mySTA/report/simple/simple.v"
        # verilog_file = '/home/wenz/git/mySTA/example/gcd.netlist.v'
        # verilog_file = '/home/wenz/git/mySTA/example/ysyx_23060004.netlist.v'
    top_module = "top"
    parser = VerilogParser()
    modules = parser.parse_file(verilog_file)
    if(len(modules) == 1):
        module = modules.get(next(iter(modules)), None)
        assert module is not None, f"Module not found in {verilog_file}"
    else:
        module = modules.get(top_module, None)
        assert module is not None, f"Top module {top_module} not found in {verilog_file}"

    # 构建电路
    circuit = build_circuit(library, module)
    timer = Timer(circuit)
    
    timer.update_capacitance()
    timer.propagate_slew()
    timer.calc_delay()

    all_timing_paths = timer.report_all_path()
    __debug_export__["circuit"] = circuit
    __debug_export__["timer"] = timer
    __debug_export__["all_timing_paths"] = all_timing_paths
    
    # 自动推断时钟引脚
    module_clock_pin = None
    for cell in circuit.cells:
        if "CK" in cell.port_mapping:
            clock_pin_name = cell.port_mapping["CK"]
            clock_pin = circuit.get_pin(clock_pin_name)
            if clock_pin and clock_pin.type == EnumPinType.PRIMARY_INPUT:
                module_clock_pin = clock_pin
                break
    # filterd timing path中没有时钟引脚
    filtered_timing_paths = []
    if module_clock_pin is not None:
        for timing_path in all_timing_paths:
            if timing_path[0][0] == module_clock_pin.name:
                filtered_timing_paths.append(timing_path[1:]) # 去掉时钟引脚
            else:
                filtered_timing_paths.append(timing_path)
        # 自动推断路径类型
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
        el = "max" # 目前还没实现min的路径匹配，所以先用max占位
        for timing_path in filtered_timing_paths:
            start_pin_name = timing_path[0][0]
            end_pin_name = timing_path[-1][0]
            start_pin = circuit.get_pin(start_pin_name)
            end_pin = circuit.get_pin(end_pin_name)
            assert isinstance(start_pin, Pin) and isinstance(end_pin, Pin), \
                f"Pin not found: {start_pin_name} or {end_pin_name}"
            if start_pin.type == EnumPinType.PRIMARY_INPUT:
                input_type = "in"
            elif start_pin.type == EnumPinType.INPUT:
                assert start_pin.fanin[0].from_pin == module_clock_pin, f"Unexpected start pin {start_pin_name} for timing path"
                input_type = "reg"
            else:
                continue
                raise ValueError(f"Unexpected start pin type {start_pin.type} for pin {start_pin_name}"
                                 f"path: {[pin_name for pin_name, _, _ in timing_path]}")
            if end_pin.type == EnumPinType.PRIMARY_OUTPUT:
                output_type = "out"
            elif end_pin.type == EnumPinType.INPUT:
                assert len(end_pin.fanout) == 0, f"Unexpected end pin: {end_pin_name} has fanout"
                output_type = "reg"
            else:
                continue
                raise ValueError(f"Unexpected end pin type {end_pin.type} for pin {end_pin_name}"
                                 f"path: {[pin_name for pin_name, _, _ in timing_path]}")
            path_type = f"{input_type}2{output_type}"
            classified_paths[el][path_type].append(timing_path)
        for el in ["max", "min"]:
            for path_type in ["in2reg","in2out","reg2reg","reg2out"]:
                paths = classified_paths[el][path_type]
                uniq_endpoints = {}
                for path in paths:
                    end_pin_name = path[-1][0]
                    delay = sum(delay for _, _, delay in path)
                    if end_pin_name not in uniq_endpoints or delay > uniq_endpoints[end_pin_name]['delay']:
                        uniq_endpoints[end_pin_name] = {'delay': delay, 'paths': [path]}
                classified_paths[el][path_type] = \
                    [p for endpoint in uniq_endpoints.values() for p in endpoint['paths']]

    if __name__ != '__main__':
        return classified_paths
    
    for el in ["max", "min"]:
        for path_type in ["in2reg","in2out","reg2reg","reg2out"]:
            paths = classified_paths[el][path_type]
            print(f"{el} {path_type}: {len(paths)} paths")
            for path in paths:
                print("Timing Path:")
                total_delay = 0
                for name, clock_edge_from_rise, delay in path:
                    total_delay += delay
                    print(f"{name:<15} {clock_edge_from_rise.name:<8} delay: {delay:.10f} ns, total_delay: {total_delay:.10f} ns")
                print("-"*20)
    # 输出路径
    # worst_path = max(all_timing_paths, key=lambda path: sum(delay for _, _, delay in path))
    # total_delay = 0
    # for name, clock_edge_from_rise, delay in worst_path:
    #     total_delay += delay
    #     print(f"{name:<15} {clock_edge_from_rise.name:<8} delay: {delay:.10f} ns, total_delay: {total_delay:.10f} ns")
    # return
    # for timing_path_bad in all_timing_paths:
    #     print("Timing Path:")
    #     total_delay = 0
    #     for name, clock_edge_from_rise, delay in timing_path_bad:
    #         total_delay += delay
    #         print(f"{name:<15} {clock_edge_from_rise.name:<8} delay: {delay:.10f} ns, total_delay: {total_delay:.10f} ns")
    #     print("-"*20)

    # import pygraphviz as pgv
    # G = pgv.AGraph(directed=True)
    # G.graph_attr['rankdir'] = 'LR'
    # # G.graph_attr['splines'] = 'ortho'
    # prim_in = G.add_subgraph(name='cluster_inputs', label='Primary Inputs', color='blue', rank='source')
    # prim_out = G.add_subgraph(name='cluster_outputs', label='Primary Outputs', color='blue', rank='sink')
    # dut = G.add_subgraph(name='cluster_dut', label='DUT', color='black', rank= 'middle', style="invis")
    # cell_blocks = {}
    # for cell in circuit.cells:
    #     cell_block = dut.add_subgraph(name=f"cluster_{cell.name}", 
    #                                   label=f"{cell.module}\n{cell.name}",
    #                                   style='',
    #                                   color= 'red' if 'FF' in cell.module else 'black')
    #     cell_blocks[cell.name] = cell_block
    
    # for pin in circuit.primary_inputs.values():
    #     prim_in.add_node(pin.name, label=f"{pin.name}\nc={pin.capacitance[EnumClockEdge.RISING]:.6f}")

    # for pin in circuit.primary_outputs.values():
    #     prim_out.add_node(pin.name, label=f"{pin.name}\nc={pin.capacitance[EnumClockEdge.RISING]:.6f}")

    # for arc in circuit.get_all_arcs():
    #     from_pin = arc.from_pin
    #     to_pin = arc.to_pin
    #     if '/' in from_pin.name:
    #         cell_name = from_pin.name.split('/')[0]
    #         cell_blocks[cell_name].add_node(from_pin.name, label=f"{from_pin.name.split('/')[1]}\nc={from_pin.capacitance[EnumClockEdge.RISING]:.6f}\ns_f={from_pin.slew[EnumClockEdge.FALLING]:.6f}\ns_r={from_pin.slew[EnumClockEdge.RISING]:.6f}")
    #     if '/' in to_pin.name:
    #         cell_name = to_pin.name.split('/')[0]
    #         cell_blocks[cell_name].add_node(to_pin.name, label=f"{to_pin.name.split('/')[1]}\nc={to_pin.capacitance[EnumClockEdge.RISING]:.6f}\ns_f={to_pin.slew[EnumClockEdge.FALLING]:.6f}\ns_r={to_pin.slew[EnumClockEdge.RISING]:.6f}")
    #     G.add_edge(from_pin.name, to_pin.name, label=f"d_f={arc.delay[EnumClockEdge.FALLING]:.6f}\nd_r={arc.delay[EnumClockEdge.RISING]:.6f}\ns_f={arc.slew[EnumClockEdge.FALLING]:.6f}\ns_r={arc.slew[EnumClockEdge.RISING]:.6f}",
    #                color = 'red' if arc.timing_sense == EnumTimingSense.POS_UNATE else ('blue' if arc.timing_sense == EnumTimingSense.NEG_UNATE else 'black'))
    # G.write('circuit.dot')

    # P = pgv.AGraph(directed=True)
    # # P.graph_attr['rankdir'] = 'LR'
    # for idx, timing_path in enumerate(all_timing_paths):
    #     path_subgraph = P.add_subgraph(name=f'cluster_path_{idx}', label=f'Timing Path {idx}', color='green')
    #     total_delay = 0.0
    #     for name, clock_edge, delay in timing_path:
    #         total_delay += delay
    #         path_subgraph.add_node(f"{name}_{idx}", label=f"{name}\n{clock_edge.name}\ndelay={delay:.6f} ns\ntotal={total_delay:.6f} ns")
    #     for i in range(len(timing_path)-1):
    #         from_name, _, _ = timing_path[i]
    #         to_name, _, _ = timing_path[i+1]
    #         path_subgraph.add_edge(f"{from_name}_{idx}", f"{to_name}_{idx}")
    # P.write('timing_paths.dot')

if __name__ == '__main__':
    main()