import numpy as np

class Interpolator:
    def __init__(self, index_1, index_2, values):
        self.index_1 = index_1  # Y轴索引
        self.index_2 = index_2  # X轴索引
        self.values = values    # 数据表格
    
    def interpolate(self, x, y):
        raise NotImplementedError("This method should be implemented by subclasses")

class RegularGridInterpolator(Interpolator):
    def __init__(self, index_1:np.ndarray, index_2:np.ndarray, values:np.ndarray):
        self.search_index_1 = index_1.copy()
        self.search_index_1[0] = -np.inf
        self.search_index_1[-1] = np.inf
        self.search_index_2 = index_2.copy()
        self.search_index_2[0] = -np.inf
        self.search_index_2[-1] = np.inf
        self.search_values = values.copy()
        super().__init__(index_1, index_2, values)
    
    def interpolate(self, x0, y0):
        for i in range(len(self.search_index_1) - 1):
            if self.search_index_1[i] <= x0 < self.search_index_1[i + 1]:
                break
        for j in range(len(self.search_index_2) - 1):
            if self.search_index_2[j] <= y0 < self.search_index_2[j + 1]:
                break
        x1, x2 = self.index_1[i], self.index_1[i + 1]
        y1, y2 = self.index_2[j], self.index_2[j + 1]

        X01 = (x0 - x1) / (x2 - x1)
        X20 = (x2 - x0) / (x2 - x1)
        Y01 = (y0 - y1) / (y2 - y1)
        Y20 = (y2 - y0) / (y2 - y1)

        T11 = self.values[i][j]
        T12 = self.values[i][j + 1]
        T21 = self.values[i + 1][j]
        T22 = self.values[i + 1][j + 1]

        x2x1 = x2-x1
        y2y1 = y2-y1
        x2x = x2-x0
        y2y = y2-y0
        yy1 = y0-y1
        xx1 = x0-x1

        # print(f"Interpolating at x={x0}, y={y0} using grid cell defined by indices ({i}, {j})")
        # print(f"Grid corners: ({x1}, {y1}), ({x1}, {y2}), ({x2}, {y1}), ({x2}, {y2})")
        # print(f"Relative positions: X01={X01}, X20={X20}, Y01={Y01}, Y20={Y20}")
        # print(f"Grid values: T11={T11}, T12={T12}, T21={T21}, T22={T22}")
        # print()

        return 1.0 / (x2x1 * y2y1) * \
                sum([T11 * x2x * y2y , 
                    T21 * xx1 * y2y , 
                    T12 * x2x * yy1 , 
                    T22 * xx1 * yy1])

        return sum([T11 * X20 * Y20,
                T21 * X01 * Y20,
                T12 * X20 * Y01,
                T22 * X01 * Y01])


class CloughTocher2DInterpolator(Interpolator):
    def __init__(self, index_1, index_2, values):
        super().__init__(index_1, index_2, values)
        # 这里可以实现Clough-Tocher插值的初始化逻辑
    
    def interpolate(self, x, y):
        # 这里实现Clough-Tocher插值算法
        raise NotImplementedError("Clough-Tocher interpolation not implemented yet")

class LinearNDInterpolator(Interpolator):
    def __init__(self, index_1, index_2, values):
        super().__init__(index_1, index_2, values)
        # 这里可以实现线性ND插值的初始化逻辑
    
    def interpolate(self, x, y):
        # 这里实现线性ND插值算法
        raise NotImplementedError("Linear ND interpolation not implemented yet")