import unittest
import math
from ProceduralCityGenerator.basis_field import GridBasisField, RadialBasisField, BasisField
from ProceduralCityGenerator.tensor import Tensor
from mathutils import Vector


class TestBasisField(unittest.TestCase):

    def test_grid_init(self):
        center = Vector((2.0, 2.0))
        size = 250
        decay = 10
        theta = math.pi / 4
        field = GridBasisField(center, size, decay, theta)
        self.assertEqual(field.center, center)
        self.assertEqual(field.size, size)
        self.assertEqual(field.decay, decay)
        self.assertEqual(field.theta, theta)

    def test_radial_init(self):
        center = Vector((2.0, 2.0))
        size = 250
        decay = 10
        field = RadialBasisField(center, size, decay)
        self.assertEqual(field.center, center)
        self.assertEqual(field.size, size)
        self.assertEqual(field.decay, decay)

    def test_tensor_weight(self):
        center = Vector((2.0, 2.0))
        size = 250
        decay = 10
        point = Vector((150.0, 20.0))
        field = BasisField(center, size, decay)
        distance = (point - center).length
        weight = (1 - (distance / size)) ** decay
        self.assertEqual(field.get_tensor_weight(point, smooth=False), weight)
        # self.assertEqual(field.get_tensor_weight(point, smooth=False), 00.00011479346465738075)

    def test_tensor_weight_smooth(self):
        center = Vector((2.0, 2.0))
        size = 250
        decay = 10
        point = Vector((150.0, 20.0))
        field = BasisField(center, size, decay)
        distance = (point - center).length
        weight = math.exp(-decay * (distance / size) ** 2)
        self.assertEqual(field.get_tensor_weight(point, smooth=True), weight)
        # self.assertEqual(field.get_tensor_weight(point, smooth=True), 0.02853910576829015)

    def test_grid_get_tensor(self):
        center = Vector((2.0, 2.0))
        size = 250
        decay = 10
        point = Vector((150.0, 20.0))
        theta = math.pi / 4
        field = GridBasisField(center, size, decay, theta)
        tensor = Tensor(1, [math.cos(math.pi / 2), math.sin(math.pi / 2)])
        self.assertEqual(field.get_tensor(point).r, tensor.r)
        self.assertEqual(field.get_tensor(point).matrix, tensor.matrix)
        self.assertEqual(
            field.get_tensor(point).get_major(),
            Vector((math.cos(math.pi / 4), math.sin(math.pi / 4)))
        )

    def test_radial_get_tensor(self):
        center = Vector((2.0, 2.0))
        size = 250
        decay = 10
        point = Vector((150.0, 20.0))
        point2 = Vector((5.0, 5.0))
        delta = point - center
        x = delta.y ** 2 - delta.x ** 2
        y = -2 * delta.x * delta.y
        field = RadialBasisField(center, size, decay)
        self.assertEqual(field.get_tensor(point).r, 1.0)
        self.assertEqual(field.get_tensor(point).matrix, [x, y])
        self.assertEqual(
            field.get_tensor(point2).get_major(),
            Vector((math.cos(7 * math.pi / 4), math.sin(7 * math.pi / 4)))
        )

    def test_grid_get_weighted_tensor(self):
        center = Vector((2.0, 2.0))
        size = 250
        decay = 10
        point = Vector((150.0, 20.0))
        theta = math.pi / 4
        field = GridBasisField(center, size, decay, theta)
        weight = (1 - (point - center).length / size) ** decay
        tensor = Tensor(1, [math.cos(math.pi / 2), math.sin(math.pi / 2)]).scale(weight)
        self.assertEqual(field.get_weighted_tensor(point).r, tensor.r)
        self.assertEqual(field.get_weighted_tensor(point).matrix, tensor.matrix)

    def test_grid_get_weighted_tensor_smooth(self):
        center = Vector((2.0, 2.0))
        size = 250
        decay = 10
        point = Vector((150.0, 20.0))
        theta = math.pi / 4
        field = GridBasisField(center, size, decay, theta)
        weight = math.exp(-decay * ((point - center).length / size) ** 2)
        tensor = Tensor(1, [math.cos(math.pi / 2), math.sin(math.pi / 2)]).scale(weight)
        self.assertEqual(field.get_weighted_tensor(point, smooth=True).r, tensor.r)
        self.assertEqual(field.get_weighted_tensor(point, smooth=True).matrix, tensor.matrix)


if __name__ == "__main__":
    unittest.main()
