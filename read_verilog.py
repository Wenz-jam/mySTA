import pyverilog
from pyverilog.vparser.parser import parse
from pyverilog.vparser.ast import *

verilog_file = "/home/wenz/git/mySTA/example/gcd.netlist.v"
# verilog_file = "/home/wenz/git/mySTA/example/ysyx_23060004.netlist.v"
# verilg_file = "/home/wenz/git/mySTA/example/test.v"
verilog_file = "/home/wenz/git/mySTA/example/simple.v"

ast, directives = parse([verilog_file])
ast.show()

# if isinstance(ast, Source):
#     for description in ast.children():
#         if isinstance(description, Description):
#             for module in description.children():
#                 if isinstance(module, ModuleDef):
#                     for port in module.portlist.ports:
#                         if isinstance(port, Port):
#                             print(port.name, port.width, port.dimensions, port.type)

# def print_children(node, level=0):
#     indent = "  " * level
#     print(f"{indent}{node.__class__.__name__}, {getattr(node,'name', None)}, {type(node)}")
#     for child in node.children():
#         print_children(child, level + 1)

# print_children(ast)
modules = []
ports = {}
inputs = {}
outputs = {}
wires = {}
instances = {}

def calc_width(node):
    assert isinstance(node, (Port, Input, Output, Wire))
    if node.width is None:
        return 1
    msb = node.width.msb.value
    lsb = node.width.lsb.value
    if msb < lsb:
        print(f"Warning: node {node.name} has reversed width msb < lsb")
    return abs(int(msb) - int(lsb)) + 1

def handle_port(node : Port):
    assert isinstance(node, Port)
    port_name = node.name
    port_width = calc_width(node)
    ports[port_name] = {'direction': None, 'width': port_width}

def handle_input(node : Input):
    assert isinstance(node, Input)
    port_name = node.name
    port_width = calc_width(node)
    if port_name in ports:
        ports.pop(port_name)
    inputs[port_name] = {'direction': 'input', 'width': port_width}

def handle_output(node : Output):
    assert isinstance(node, Output)
    port_name = node.name
    port_width = calc_width(node)
    if port_name in ports:
        ports.pop(port_name)
    outputs[port_name] = {'direction': 'output', 'width': port_width}

def handle_wire(node : Wire):
    assert isinstance(node, Wire)
    wire_name = node.name
    wire_width = calc_width(node)
    wires[wire_name] = {'width': wire_width}

def handle_instance(node : Instance):
    assert isinstance(node, Instance)
    instance_name = node.name
    module_name = node.module
    port_list = [(port.portname, port.argname.name) for port in node.portlist]
    instances[instance_name] = {'module': module_name, 'portlist': port_list}

handlers = {
    Port: handle_port,
    Input: handle_input,
    Output: handle_output,
    Wire: handle_wire,
    Instance: handle_instance,
}

def parse_ast(node):
    """
    递归遍历 AST 节点，并调用相应的处理函数
    没有处理函数, 默认继续遍历子节点
    若处理函数无返回, 结束遍历该节点及其子节点
    处理函数返回任意值, 推荐true, 继续遍历子节点
    """
    node_type = type(node)
    handler = handlers.get(node_type, None)
    if handler:
        ret = handler(node)
        if(ret is None):
            return
    for child in node.children():
        parse_ast(child)

parse_ast(ast)
if(len(ports) > 0):
    print("Warning: some ports are not defined as input or output:")
    for port_name, port_info in ports.items():
        print(f"  Port: {port_name}, width: {port_info['width']}")
# print(f"Inputs: {len(inputs)}")
# for input_name, input_info in inputs.items():
#     print(f"  Input: {input_name}, width: {input_info['width']}")
# print(f"Outputs: {len(outputs)}")
# for output_name, output_info in outputs.items():
#     print(f"  Output: {output_name}, width: {output_info['width']}")
# print(f"Wires: {len(wires)}")
# for wire_name, wire_info in wires.items():
#     print(f"  Wire: {wire_name}, width: {wire_info['width']}")
print(f"Instances: {len(instances)}")
for instance_name, instance_info in instances.items():
    print(f"  Instance: {instance_name}, module: {instance_info['module']}, portlist: {instance_info['portlist']}")