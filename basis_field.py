import math
from tensor import Tensor
from mathutils import Vector


class BasisField:
    def __init__(self, center, size, decay):
        self.center = center.copy()
        self.size = size
        self.decay = decay

    def get_weighted_tensor(self, point, smooth=False):
        return self.get_tensor(point).scale(self.get_tensor_weight(point, smooth))

    def get_tensor(self, point):
        return Tensor.zero()

    def get_tensor_weight(self, point, smooth):
        norm_distance_to_center = Vector((point.x - self.center, point.y - self.center)).length / self.size
        if smooth:
            return norm_distance_to_center ** -self.decay
        if self.decay == 0 and norm_distance_to_center >= 1:
            return 0
        return math.max(0, (1 - norm_distance_to_center)) ** self.decay


class GridBasisField(BasisField):
    def __init__(self, center, size, decay, theta):
        super().__init__(center, size, decay)
        self.theta = theta

    def get_tensor(self, point):
        return Tensor(1, [math.cos(2 * self.theta), math.sin(2 * self.theta)])


class RadialBasisField(BasisField):
    def __init__(self, center, size, decay):
        super().__init__(center, size, decay)

    def get_tensor(self, point):
        t = Vector((point.x - self.center, point.y - self.center))
        t1 = t.y ** 2 - t.x ** 2
        t2 = -2 * t.x * t.y
        return Tensor(1, [t1, t2])
