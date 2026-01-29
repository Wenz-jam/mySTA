class Arc:
    def __init__(self, from_pin, to_pin):
        self.from_pin = from_pin
        self.to_pin = to_pin
        self.slew = 0.0
        self.delay = 0.0
        
        # 双向连接
        from_pin.arcs.append(self)
        to_pin.arcs.append(self)
    
    def __repr__(self):
        return f"Arc({self.from_pin.name} -> {self.to_pin.name})"
    
    @property
    def key(self):
        """Arc的唯一标识符"""
        return f"{self.from_pin.name}:{self.to_pin.name}"

class ArcFactory:
    """Arc对象工厂，管理Arc的创建和查询"""
    def __init__(self):
        self._arcs = {}
    
    def create_arc(self, from_pin, to_pin):
        arc_key = f"{from_pin.name}:{to_pin.name}"
        
        if arc_key in self._arcs:
            return self._arcs[arc_key]
        
        arc = Arc(from_pin, to_pin)
        self._arcs[arc_key] = arc
        return arc
    
    def get_arc(self, key):
        return self._arcs.get(key)
    
    def get_all_arcs(self):
        return list(self._arcs.values())
