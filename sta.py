from read_liberty import *
from CircuitBuilder import CircuitBuilder, build_circuit
from VerilogParser import VerilogParser
from Pin import EnumPinType, Pin
from Arc import Arc

# 主程序
import pygraphviz as pgv

def dfs(circuit : CircuitBuilder, visit):
    stack = [pin for pin in circuit.primary_inputs.values()]
    stack_pointer = len(stack) - 1
    while stack:
        assert stack_pointer >= 0
        pin = stack.pop(stack_pointer)
        stack_pointer -= 1
        if pin.type == EnumPinType.PRIMARY_INPUT:
            assert pin.net is not None
            for sink in pin.net.sinks:
                if(sink not in stack):
                    stack.append(sink)
                    stack_pointer += 1
        elif pin.type == EnumPinType.INPUT:
            # assert pin.arcs is not None
            # 时序路径可以到触发器停止
            if len(pin.fanout) > 0:
                for arc in pin.fanout:
                    to_pin = arc.to_pin
                    assert to_pin not in stack
                    stack.append(to_pin)
                    stack_pointer += 1
        elif pin.type == EnumPinType.OUTPUT:
            assert pin.net is not None
            for sink in pin.net.sinks:
                assert sink not in stack
                stack.append(sink)
                stack_pointer += 1
        visit(pin)

if __name__ == "__main__":
    # 假设已经从文件读取了这些数据
    # library = ...  # Liberty库数据
    # wires = [...]  # 网线列表
    # inputs = [...]  # 主输入列表
    # outputs = [...]  # 主输出列表
    # instances = {...}  # 实例字典
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

    G = pgv.AGraph(directed=True)
    G.graph_attr['rankdir'] = 'LR'
    # G.graph_attr['splines'] = 'ortho'
    prim_in = G.add_subgraph(name='cluster_inputs', label='Primary Inputs', color='blue', rank='source')
    prim_out = G.add_subgraph(name='cluster_outputs', label='Primary Outputs', color='blue', rank='sink')
    dut = G.add_subgraph(name='cluster_dut', label='DUT', color='black', rank= 'middle', style="invis")
    cell_blocks = {}
    for cell in circuit.cells:
        cell_block = dut.add_subgraph(name=f"cluster_{cell.name}", label=cell.name, style='')
        cell_blocks[cell.name] = cell_block

    def visit(pin : Pin):
        if pin.type == EnumPinType.PRIMARY_INPUT:
            prim_in.add_node(pin.name, shape='box', color = '#4CAF50')
        elif pin.type == EnumPinType.PRIMARY_OUTPUT:
            prim_out.add_node(pin.name, shape='box', color = "#8FFFEA")
        else:
            cell_name = pin.name.split('/')[0]
            cell_blocks[cell_name].add_node(pin.name, label = pin.name.split('/')[1], ordering = 'out' if pin.type == EnumPinType.OUTPUT else 'in')
        if pin.type in [EnumPinType.INPUT, EnumPinType.PRIMARY_OUTPUT]:
            G.add_edge(pin.net.source.name, pin.name, color = 'green')
        elif pin.type in [EnumPinType.OUTPUT]:
            for arc in pin.fanin:
                G.add_edge(arc.from_pin.name, arc.to_pin.name, color = 'red')
    dfs(circuit, visit)
    G.write("circuit_graph.dot")
    
    # update capacity
    # for net in all_nets:
    #     source = net.source
    #     sinks = net.sinks
    #     assert isinstance(source, Pin)
    #     assert isinstance(sinks, list)
    #     source.capacitance = sum(sink.capacitance for sink in sinks)

    # G.write('circuit_graph.dot')
    # # 生成详细电路图
    # print("\nGenerating detailed circuit diagram...")
    # circuit.visualize('circuit_detailed.png')
    
    # # 生成简化电路图
    # print("\nGenerating simplified circuit diagram...")
    # circuit.visualize('circuit_simple.png', simple=True)
    
    # # 导出DOT文件
    # circuit.visualize('circuit.dot', simple=False)  # visualizer会自动处理

    # print("\nAll visualizations generated!")
