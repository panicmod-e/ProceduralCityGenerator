import unittest
import math
from mathutils import Vector
from ProceduralCityGenerator.tensor import Tensor


class TestTensor(unittest.TestCase):

    def test_tensor_zero(self):
        tensor = Tensor.zero()
        self.assertEqual(tensor.r, 0)
        self.assertEqual(tensor.matrix, [0, 0])
        self.assertEqual(tensor.theta, 0)

    def test_tensor_new(self):
        theta = math.pi / 4
        tensor = Tensor(1, [math.cos(2 * theta), math.sin(2 * theta)])
        self.assertEqual(tensor.theta, theta)

    def test_tensor_get_major(self):
        theta = math.pi / 4
        tensor = Tensor(1, [math.cos(2 * theta), math.sin(2 * theta)])
        vector = Vector((math.cos(theta), math.sin(theta)))
        self.assertEqual(tensor.get_major(), vector)

    def test_tensor_get_minor(self):
        theta = math.pi / 4
        tensor = Tensor(1, [math.cos(2 * theta), math.sin(2 * theta)])
        vector = Vector((math.cos(theta + math.pi / 2), math.sin(theta + math.pi / 2)))
        self.assertEqual(tensor.get_minor(), vector)

    def test_tensor_scale(self):
        t = Tensor(1, [0.0, 1.0])
        t.scale(2.0)
        self.assertEqual(t.r, 2.0)

    def test_tensor_rotate(self):
        pass

    def test_tensor_add(self):
        v_1 = Vector((1.0, 1.0))
        v_2 = Vector((1.0, 0.0))
        theta_1 = math.atan2(v_1.y, v_1.x)
        theta_2 = math.atan2(v_2.y, v_2.x)

        t_1 = Tensor(1, [math.cos(2 * theta_1), math.sin(2 * theta_1)])
        t_2 = Tensor(1, [math.cos(2 * theta_2), math.sin(2 * theta_2)])

        t_1.add(t_2)

        self.assertEqual(t_1.r, 2.0)
        self.assertEqual(
            t_1.matrix,
            [math.cos(2 * theta_1) + math.cos(2 * theta_2), math.sin(2 * theta_1) + math.sin(2 * theta_2)])
        self.assertEqual(t_1.theta, math.pi / 8)
        self.assertEqual(t_1.get_major(), Vector((math.cos(math.pi / 8), math.sin(math.pi / 8))))

    def test_tensor_add_smooth(self):
        v_1 = Vector((1.0, 1.0))
        v_2 = Vector((1.0, 0.0))
        theta_1 = math.atan2(v_1.y, v_1.x)
        theta_2 = math.atan2(v_2.y, v_2.x)

        t_1 = Tensor(1, [math.cos(2 * theta_1), math.sin(2 * theta_1)])
        t_2 = Tensor(1, [math.cos(2 * theta_2), math.sin(2 * theta_2)])

        t_1.add(t_2, smooth=True)

        x = math.cos(2 * theta_1) + math.cos(2 * theta_2)
        y = math.sin(2 * theta_1) + math.sin(2 * theta_2)
        r = math.sqrt(x * x + y * y)
        matrix = [x, y]

        self.assertEqual(t_1.r, r)
        self.assertEqual(t_1.matrix, matrix)
        self.assertEqual(t_1.theta, math.pi / 8)
        self.assertEqual(t_1.get_major(), Vector((math.cos(math.pi / 8), math.sin(math.pi / 8))))


if __name__ == "__main__":
    unittest.main()
