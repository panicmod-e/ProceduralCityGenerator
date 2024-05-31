import math
from mathutils import Vector


# Tensor implementation using polar coordinates 'theta' and 'r' and a 2x2 matrix repre-
# sented as a 2-element list consisiting of [cos(2 * theta), sin(2 * theta)], following
# the definition of presented by Chen et al. (2008) and Zhang et al. (2007).
class Tensor:

    def __init__(self, r, matrix):
        self.old_theta = False
        self.r = r
        self.matrix = matrix
        self._theta = self.calculate_theta()

    @classmethod
    def zero(cls) -> 'Tensor':
        return Tensor(0, [0, 0])

    @property
    def theta(self):
        if self.old_theta:
            self._theta = self.calculate_theta()
            self.old_theta = False
        return self._theta

    def add(self, tensor: 'Tensor', smooth=False):
        self.matrix = [v * self.r + tensor.matrix[i] * tensor.r for i, v in enumerate(self.matrix)]

        if smooth:
            self.r = math.hypot(*self.matrix)
            # self.matrix = [v / self.r for v in self.matrix]
        else:
            self.r = 2

        self.old_theta = True
        return self

    def scale(self, s):
        self.r *= s
        self.old_theta = True
        return self

    def rotate(self, theta):
        if theta == 0:
            return self

        new_theta = self.theta + theta
        if new_theta < math.pi:
            new_theta += math.pi

        if new_theta >= math.pi:
            new_theta -= math.pi

        self.matrix[0] = math.cos(2 * new_theta) * self.r
        self.matrix[1] = math.sin(2 * new_theta) * self.r
        self._theta = new_theta
        return self

    # returns major eigenvector of the tensor
    def get_major(self) -> Vector:
        if self.r == 0:
            return Vector((0.0, 0.0))
        return Vector((math.cos(self.theta), math.sin(self.theta)))

    # returns minor eigenvector of the tensor
    def get_minor(self) -> Vector:
        if self.r == 0:
            return Vector((0.0, 0.0))
        angle = self.theta + math.pi / 2
        return Vector((math.cos(angle), math.sin(angle)))

    def calculate_theta(self):
        if self.r == 0:
            return 0
        return math.atan2(self.matrix[1] / self.r, self.matrix[0] / self.r) / 2
