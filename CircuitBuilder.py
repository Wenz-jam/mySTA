from collections import defaultdict

from Arc import ArcFactory, PassThroughLut, EnumTimingSense, ZeroLut
from Cell import Cell
from Net import NetFactory
from Pin import EnumPinType, PinFactory


class CircuitBuilder:
    """电路构建器，协调Pin、Net、Arc的创建"""
    def __init__(self, library):
        self.library = library
        self.pin_factory = PinFactory()
        self.net_factory = NetFactory()
        self.arc_factory = ArcFactory()
        self.cells: list[Cell] = []
        self.zeroLut = ZeroLut()
        self.passThroughLut = PassThroughLut()
        
        # 存储主输入输出
        self.primary_inputs = {}
        self.primary_outputs = {}
    
    def build_from_verilog(self, wires, inputs, outputs, instances):
        """从Verilog信息构建完整电路"""
        # 步骤1: 创建所有Net
        self._create_nets(wires)
        
        # 步骤2: 创建主输入输出并连接到Net
        self._create_primary_ios(inputs, outputs)
        
        # 步骤3: 创建所有Cell实例
        self._create_cells(instances)
        
        # 步骤4: 分三步为每个Cell创建Pin、连接Net、创建Arc
        self._process_cells()

        for net in self.net_factory.get_all_nets():
            from_pin = net.source
            if from_pin is None:
                continue
            for to_pin in net.sinks:
                # 目前认为互联线直通, 无负载无延迟
                self.arc_factory.create_arc(EnumTimingSense.POS_UNATE, from_pin, to_pin, self.zeroLut, self.zeroLut, self.passThroughLut, self.passThroughLut)
        
        return self
    
    def _create_nets(self, wires):
        """创建所有Net"""
        for wire_name in wires:
            self.net_factory.create_net(wire_name)
    
    def _create_primary_ios(self, inputs, outputs):
        """创建主输入输出并连接"""
        # 创建主输入
        for input_name in inputs:
            pin = self.pin_factory.create_pin(input_name, EnumPinType.PRIMARY_INPUT)
            net = self.net_factory.get_net(input_name)
            if net:
                pin.connect_to_net(net)
            self.primary_inputs[input_name] = pin
        
        # 创建主输出
        for output_name in outputs:
            pin = self.pin_factory.create_pin(output_name, EnumPinType.PRIMARY_OUTPUT)
            net = self.net_factory.get_net(output_name)
            if net:
                pin.connect_to_net(net)
            self.primary_outputs[output_name] = pin
    
    def _create_cells(self, instances):
        """创建所有Cell对象"""
        for instance_name, instance in instances.items():
            cell = Cell(instance_name, instance, self.library)
            self.cells.append(cell)
    
    def _process_cells(self):
        """处理所有Cell：分三步创建Pin、连接Net、创建Arc"""
        # 第一步：为所有Cell创建Pin
        for cell in self.cells:
            cell.create_pins(self.pin_factory)
        
        # 第二步：将所有Pin连接到Net
        for cell in self.cells:
            cell.connect_pins_to_nets(self.net_factory)
        
        # 第三步：为所有Cell创建Arc
        for cell in self.cells:
            cell.create_arcs(self.arc_factory)
    
    def get_statistics(self):
        """获取电路统计信息"""
        return {
            'pins': len(self.pin_factory._pins),
            'nets': len(self.net_factory._nets),
            'arcs': len(self.arc_factory._arcs),
            'cells': len(self.cells),
            'primary_inputs': len(self.primary_inputs),
            'primary_outputs': len(self.primary_outputs)
        }
    
    def validate(self):
        """验证电路连接的完整性"""
        errors = []
        
        # 检查所有Net是否至少有一个连接
        for net_name, net in self.net_factory._nets.items():
            if not net.is_connected():
                errors.append(f"Net {net_name} is not connected")
        
        # 检查所有Arc的pin是否都存在
        for arc_key, arc in self.arc_factory._arcs.items():
            if arc.from_pin not in self.pin_factory._pins.values():
                errors.append(f"Arc {arc_key} has invalid from_pin")
            if arc.to_pin not in self.pin_factory._pins.values():
                errors.append(f"Arc {arc_key} has invalid to_pin")
        
        return errors

    def print_connectivity(self):
        """打印电路的连接性信息（调试用）"""
        print("\n=== Circuit Connectivity ===")
        
        # 打印主输入输出
        print(f"Primary Inputs: {list(self.primary_inputs.keys())}")
        print(f"Primary Outputs: {list(self.primary_outputs.keys())}")
        
        # 打印每个Net的连接
        print("\nNet Connections:")
        for net_name, net in self.net_factory._nets.items():
            source_name = net.source.name if net.source else "None"
            sink_names = [s.name for s in net.sinks]
            print(f"  {net_name}: {source_name} -> {sink_names}")
        
        # 打印每个Cell的Arc
        print("\nCell Internal Arcs:")
        cell_arcs = defaultdict(list)
        for arc_key, arc in self.arc_factory._arcs.items():
            # 提取Cell名称
            if '/' in arc.from_pin.name:
                cell_name = arc.from_pin.name.split('/')[0]
                cell_arcs[cell_name].append(arc_key)
        
        for cell_name, arcs in cell_arcs.items():
            print(f"  {cell_name}: {arcs}")
        
        # 统计信息
        stats = self.get_statistics()
        print("\nStatistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

def build_circuit(library, wires, inputs, outputs, instances):
    """构建电路的入口函数"""
    circuit = CircuitBuilder(library).build_from_verilog(wires, inputs, outputs, instances)
    
    # 验证电路
    errors = circuit.validate()
    if errors:
        print("Circuit validation errors:")
        for error in errors:
            print(f"  - {error}")
    
    # 打印统计信息
    # stats = circuit.get_statistics()
    # print("\nCircuit Statistics:")
    # for key, value in stats.items():
    #     print(f"  {key}: {value}")
    
    return circuit
