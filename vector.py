import math


############################################################
#
# unused, for reference only, use mathutils.Vector instead
#
############################################################


class Vector():
    def __init__(self, x, y):
        self.x = x
        self.y = y

    @classmethod
    def zero(cls):
        return Vector(0, 0)

    @classmethod
    def from_scalar(cls, s):
        return Vector(s, s)

    @classmethod
    def angle_between(cls, v1: 'Vector', v2: 'Vector'):
        angle_between = v1.angle() - v2.angle()
        if angle_between > math.pi:
            angle_between -= 2 * math.pi
        elif angle_between <= -math.pi:
            angle_between += 2 * math.pi
        return angle_between

    @classmethod
    def is_left(cls, line_point: 'Vector', line_direction: 'Vector', point: 'Vector'):
        perpendicular_vector = Vector(line_direction.y, -line_direction.x)
        return point.clone().sub(line_point).dot(perpendicular_vector) < 0

    def add(self, v: 'Vector'):
        self.x += v.x
        self.y += v.y
        return self

    def angle(self):
        return math.atan2(self.y, self.x)

    def clone(self):
        return Vector(self.x, self.y)

    def copy(self, v: 'Vector'):
        self.x = v.x
        self.y = v.y
        return self

    def cross(self, v: 'Vector'):
        return self.x * v.y - self.y * v.x

    def distance_to(self, v: 'Vector'):
        return math.sqrt(self.distance_to_squared(v))

    def distance_to_squared(self, v: 'Vector'):
        dx = self.x - v.x
        dy = self.y - v.y
        return dx ** 2 + dy ** 2

    def divide(self, v: 'Vector'):
        if v.x == 0 or v.y == 0:
            return self

        self.x /= v.x
        self.y /= v.y
        return self

    def divide_scalar(self, s):
        if s == 0:
            return self
        return self.multiply_scalar(1 / s)

    def dot(self, v: 'Vector'):
        return self.x * v.x + self.y * v.y

    def equals(self, v: 'Vector'):
        return self.x == v.x and self.y == v.y

    def length(self):
        return math.sqrt(self.length_squared)

    def length_squared(self):
        return self.x ** 2 + self.y ** 2

    def multiply(self, v: 'Vector'):
        self.x *= v.x
        self.y *= v.y
        return self

    def multiply_scalar(self, s):
        self.x *= s
        self.y *= s
        return self

    def negate(self):
        return self.multiply_scalar(-1)

    def normalize(self):
        length = self.length()
        if length == 0:
            return self
        return self.divide_scalar(length)

    # angle in radians
    def rotate_around(self, center: 'Vector', angle):
        cos = math.cos(angle)
        sin = math.sin(angle)
        x = self.x - center.x
        y = self.y - center.y
        self.x = x * cos - y * sin + center.x
        self.y = x * sin + y * cos + center.y
        return self

    def set(self, v: 'Vector'):
        self.x = v.x
        self.y = v.y
        return self

    def set_x(self, x):
        self.x = x
        return self

    def set_y(self, y):
        self.y = y
        return self

    def set_length(self, length):
        return self.normalize().multiply_scalar(length)

    def sub(self, v: 'Vector'):
        self.x -= v.x
        self.y -= v.y
        return self
