class Lut:
    def __init__(self, lut_group):
        if lut_group is None:
            self.index_1 = [1e8]
            self.index_2 = [1e8]
            self.lut_values = [[0.0]]
            return
        self.index_1 = lut_group.get_array('index_1')[0]
        self.index_2 = lut_group.get_array('index_2')[0]
        self.lut_values = lut_group.get_array('values')
    
    def get_value(self, x, y):
        i = 0
        for idx, index in enumerate(self.index_1):
            if x <= index:
                i = idx
                break
        j = 0
        for idx, index in enumerate(self.index_2):
            if y <= index:
                j = idx
                break
        return self.lut_values[i][j]

class Arc:
    def __init__(self, from_pin, to_pin, cell_rise: Lut, cell_fall: Lut, rise_transition: Lut, fall_transition: Lut):
        self.from_pin = from_pin
        self.to_pin = to_pin
        self.cell_rise = cell_rise
        self.cell_fall = cell_fall
        self.rise_transition = rise_transition
        self.fall_transition = fall_transition
        self.slew = 0.0
        self.delay = 0.0

        # 双向连接
        from_pin.fanout.append(self)
        to_pin.fanin.append(self)

    def __repr__(self):
        return f"Arc({self.from_pin.name} -> {self.to_pin.name})"

    def get_delay(self, input_slew, output_capacitance):
        # 简单的延迟计算模型
        self.delay = max(self.cell_rise.get_value(input_slew, output_capacitance),
                            self.cell_fall.get_value(input_slew, output_capacitance))
        return self.delay

    def get_slew(self, input_slew, output_capacitance):
        # 简单的slew计算模型
        self.slew = max(self.rise_transition.get_value(input_slew, output_capacitance),
                            self.fall_transition.get_value(input_slew, output_capacitance))
        return self.slew
    
    @property
    def key(self):
        """Arc的唯一标识符"""
        return f"{self.from_pin.name}:{self.to_pin.name}"

class ArcFactory:
    """Arc对象工厂，管理Arc的创建和查询"""
    def __init__(self):
        self._arcs = {}
    
    def create_arc(self, from_pin, to_pin, cell_rise: Lut = None, cell_fall: Lut = None, rise_transition: Lut = None, fall_transition: Lut = None):
        arc_key = f"{from_pin.name}:{to_pin.name}"
        
        if arc_key in self._arcs:
            return self._arcs[arc_key]
        
        arc = Arc(from_pin, to_pin, cell_rise, cell_fall, rise_transition, fall_transition)
        self._arcs[arc_key] = arc
        return arc
    
    def get_arc(self, key):
        return self._arcs.get(key)
    
    def get_all_arcs(self):
        return list(self._arcs.values())
