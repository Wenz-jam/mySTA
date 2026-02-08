from pyverilog.vparser.parser import parse
from pyverilog.vparser.ast import *
from typing import Dict, List, Tuple, Optional, Any

class VerilogModule:
    """表示一个Verilog模块的类"""
    
    def __init__(self, name: str):
        self.name = name
        self.ports: Dict[str, Dict] = {}      # 端口：{direction: str, width: int}
        self.inputs: Dict[str, Dict] = {}     # 输入端口
        self.outputs: Dict[str, Dict] = {}    # 输出端口
        self.wires: Dict[str, Dict] = {}      # 线网：{width: int}
        self.instances: Dict[str, Dict] = {}  # 实例：{module: str, portlist: List[Tuple]}
        
    def add_port(self, name: str, direction: Optional[str], width: int):
        """添加端口"""
        if direction is None:
            self.ports[name] = {'direction': None, 'width': width}
        elif direction == 'input':
            self.inputs[name] = {'direction': 'input', 'width': width}
            # 如果之前在ports中，移除它
            if name in self.ports:
                del self.ports[name]
        elif direction == 'output':
            self.outputs[name] = {'direction': 'output', 'width': width}
            if name in self.ports:
                del self.ports[name]
    
    def add_wire(self, name: str, width: int):
        """添加线网"""
        self.wires[name] = {'width': width}
    
    def add_instance(self, name: str, module: str, portlist: List[Tuple[str, str]]):
        """添加实例"""
        self.instances[name] = {'module': module, 'portlist': portlist}
    
    def summary(self) -> Dict[str, Any]:
        """返回模块的统计信息"""
        return {
            'name': self.name,
            'total_ports': len(self.inputs) + len(self.outputs) + len(self.ports),
            'inputs': len(self.inputs),
            'outputs': len(self.outputs),
            'wires': len(self.wires),
            'instances': len(self.instances),
            'undefined_ports': len(self.ports)
        }
    
    def print_summary(self):
        """打印模块摘要"""
        print(f"\n=== Module: {self.name} ===")
        print(f"Inputs: {len(self.inputs)}")
        print(f"Outputs: {len(self.outputs)}")
        print(f"Wires: {len(self.wires)}")
        print(f"Instances: {len(self.instances)}")
        
        if len(self.ports) > 0:
            print(f"\nWarning: {len(self.ports)} ports are not defined as input or output:")
            for port_name, port_info in self.ports.items():
                print(f"  Port: {port_name}, width: {port_info['width']}")

class VerilogParser:
    """Verilog解析器"""
    
    def __init__(self):
        self.modules: Dict[str, VerilogModule] = {}
        self.current_module: Optional[VerilogModule] = None
        self._setup_handlers()
    
    def _setup_handlers(self):
        """设置AST节点处理器"""
        self.handlers = {
            ModuleDef: self._handle_module,
            Port: self._handle_port,
            Input: self._handle_input,
            Output: self._handle_output,
            Wire: self._handle_wire,
            Instance: self._handle_instance,
        }
    
    @staticmethod
    def _calc_width(node) -> int:
        """计算节点的宽度"""
        assert isinstance(node, (Port, Input, Output, Wire))
        
        if node.width is None:
            return 1
        
        msb = node.width.msb.value
        lsb = node.width.lsb.value
        
        if msb < lsb:
            print(f"Warning: node {node.name} has reversed width msb < lsb")
        
        return abs(int(msb) - int(lsb)) + 1
    
    def _handle_module(self, node: ModuleDef) -> bool:
        """处理模块定义"""
        module_name = node.name
        self.current_module = VerilogModule(module_name)
        self.modules[module_name] = self.current_module
        return True  # 继续遍历子节点
    
    def _handle_port(self, node: Port) -> None:
        """处理端口声明"""
        if not self.current_module:
            return
        
        port_name = node.name
        port_width = self._calc_width(node)
        self.current_module.add_port(port_name, None, port_width)
    
    def _handle_input(self, node: Input) -> None:
        """处理输入声明"""
        if not self.current_module:
            return
        
        port_name = node.name
        port_width = self._calc_width(node)
        self.current_module.add_port(port_name, 'input', port_width)
    
    def _handle_output(self, node: Output) -> None:
        """处理输出声明"""
        if not self.current_module:
            return
        
        port_name = node.name
        port_width = self._calc_width(node)
        self.current_module.add_port(port_name, 'output', port_width)
    
    def _handle_wire(self, node: Wire) -> None:
        """处理线网声明"""
        if not self.current_module:
            return
        
        wire_name = node.name
        wire_width = self._calc_width(node)
        self.current_module.add_wire(wire_name, wire_width)
    
    def _handle_instance(self, node: Instance) -> None:
        """处理实例化"""
        if not self.current_module:
            return
        
        instance_name = node.name
        module_name = node.module
        portlist = [(port.portname, port.argname.name) for port in node.portlist]
        self.current_module.add_instance(instance_name, module_name, portlist)
    
    def _parse_ast(self, node):
        """递归遍历AST"""
        node_type = type(node)
        handler = self.handlers.get(node_type)
        
        if handler:
            # 如果处理器返回True，继续遍历子节点
            # 如果返回None/False，停止遍历该节点的子节点
            result = handler(node)
            if result is not True:
                return
        
        # 如果没有处理器或处理器返回True，继续遍历子节点
        for child in node.children():
            self._parse_ast(child)
    
    def parse_file(self, verilog_file: str) -> Dict[str, VerilogModule]:
        """解析Verilog文件"""
        outputdir = f"/tmp/sta/{verilog_file.split('/')[-1].replace(".v","")}"
        ast, directives = parse([verilog_file], outputdir=outputdir)
        self._parse_ast(ast)
        return self.modules
    
    def get_module(self, name: str) -> Optional[VerilogModule]:
        """获取指定名称的模块"""
        return self.modules.get(name)
    
    def get_all_modules(self) -> List[str]:
        """获取所有模块名称"""
        return list(self.modules.keys())