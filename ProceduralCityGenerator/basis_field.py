import math
from ProceduralCityGenerator.tensor import Tensor
from mathutils import Vector


# The BasisField subclasses define specific tensor field patterns/designs.
#
# Can be sampled to retrieve the tensor at a specified point of the domain.
# 'get_weighted_tensor' returns the tensor weighted with the fields decay constant.
class BasisField:
    def __init__(self, center: Vector, size, decay):
        self.center = center.copy()
        self.size = size
        self.decay = decay

    def get_weighted_tensor(self, point: Vector, smooth=False):
        return self.get_tensor(point).scale(self.get_tensor_weight(point, smooth))

    def get_tensor(self, point: Vector):
        return Tensor.zero()

    def get_tensor_weight(self, point: Vector, smooth: bool):
        norm_distance_to_center = Vector((point.x - self.center.x, point.y - self.center.y)).length / self.size
        if smooth:
            # return norm_distance_to_center ** -self.decay
            return math.exp(-self.decay * norm_distance_to_center ** 2)
        if self.decay == 0 and norm_distance_to_center >= 1:
            return 0
        return max(0, (1 - norm_distance_to_center)) ** self.decay


class GridBasisField(BasisField):
    def __init__(self, center: Vector, size, decay, theta):
        super().__init__(center, size, decay)
        self.theta = theta

    def get_tensor(self, point: Vector):
        return Tensor(1, [math.cos(2 * self.theta), math.sin(2 * self.theta)])


class RadialBasisField(BasisField):
    def __init__(self, center: Vector, size, decay):
        super().__init__(center, size, decay)

    def get_tensor(self, point: Vector):
        t = Vector((point.x - self.center.x, point.y - self.center.y))
        t1 = t.y ** 2 - t.x ** 2
        t2 = -2 * t.x * t.y
        return Tensor(1, [t1, t2])
