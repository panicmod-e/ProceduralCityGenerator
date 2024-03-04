import math
from mathutils import Vector


class Tensor:

    def __init__(self, r, matrix):
        self.old_theta = False
        self.r = r
        self.matrix = matrix
        self.theta = self.calculate_theta()

    @classmethod
    def from_angle(cls, angle):
        return Tensor(1, [math.cos(angle * 4, math.sin(angle * 4))])

    @classmethod
    def from_vector(cls, vector):
        t1 = vector.x ** 2 - vector.y ** 2
        t2 = 2 * vector.x * vector.y
        t3 = t1 ** 2 - t2 ** 2
        t4 = 2 * t1 * t2
        return Tensor(1, [t3, t4])

    @classmethod
    def zero(cls):
        return Tensor(0, [0, 0])

    def get_theta(self):
        if self.old_theta:
            self.theta = self.calculate_theta()
            self.old_theta = False
        return self.theta

    def add(self, tensor, smooth=False):
        self.matrix = [v * self.r + tensor.matrix[i] for i, v in list(enumerate(self.matrix))]

        if smooth:
            self.r = math.hypot(*self.matrix)
            self.matrix = [v / self.r for v in self.matrix]
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
        self.theta = new_theta
        return self

    def get_major(self):
        if self.r == 0:
            return Vector((0.0, 0.0))
        return Vector((math.cos(self.theta), math.sin(self.theta)))

    def get_minor(self):
        if self.r == 0:
            return Vector((0.0, 0.0))
        return Vector((math.sin(self.theta), math.cos(self.theta)))

    def calculate_theta(self):
        if self.r == 0:
            return 0
        return math.atan2(self.matrix[1] / self.r, self.matrix[0] / self.r) / 2
