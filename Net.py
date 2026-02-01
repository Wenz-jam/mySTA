class Net:
    def __init__(self, name):
        self.name = name
        self.source = None
        self.sinks = []
        self.capacitance = 0.0
    
    def __repr__(self):
        return f"Net({self.name}, source={self.source}, sinks={len(self.sinks)})"
    
    def set_source(self, pin):
        self.source = pin
        pin.net = self
    
    def add_sink(self, pin):
        self.sinks.append(pin)
        pin.net = self
    
    def is_connected(self):
        """检查Net是否已连接"""
        return self.source is not None or len(self.sinks) > 0

class NetFactory:
    """Net对象工厂，管理Net的创建和查询"""
    def __init__(self):
        self._nets = {}
    
    def create_net(self, name):
        if name in self._nets:
            return self._nets[name]
        
        net = Net(name)
        self._nets[name] = net
        return net
    
    def get_net(self, name):
        return self._nets.get(name)
    
    def get_all_nets(self) -> list[Net]:
        return list(self._nets.values())
