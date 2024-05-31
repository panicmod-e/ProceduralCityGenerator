import unittest
import math
from mathutils import Vector
from ProceduralCityGenerator.tensor import Tensor
from ProceduralCityGenerator.tensor_field import TensorField
from ProceduralCityGenerator.basis_field import GridBasisField, RadialBasisField


class TestTensorField(unittest.TestCase):

    def test_tensor_field_init(self):
        tensor_field = TensorField()
        self.assertEqual(tensor_field.basis_fields, [])
        self.assertFalse(tensor_field.smooth)

    def test_tensor_field_add(self):
        center = Vector((2.0, 2.0))
        size = 250
        decay = 10
        theta = math.pi / 4
        field = GridBasisField(center, size, decay, theta)
        tensor_field = TensorField()
        self.assertEqual(tensor_field.basis_fields, [])
        tensor_field.add_field(field)
        self.assertEqual(len(tensor_field.basis_fields), 1)
        self.assertEqual(tensor_field.basis_fields, [field])

    def test_tensor_field_remove(self):
        center = Vector((2.0, 2.0))
        size = 250
        decay = 10
        theta = math.pi / 4
        field = GridBasisField(center, size, decay, theta)
        tensor_field = TensorField()
        tensor_field.basis_fields = [field]
        tensor_field.remove_field(field)
        self.assertEqual(tensor_field.basis_fields, [])

    def test_sample_point_empty(self):
        tensor_field = TensorField()
        tensor = tensor_field.sample_point(Vector((0.0, 0.0)))
        self.assertEqual(tensor.r, 1.0)
        self.assertEqual(tensor.matrix, [0.0, 0.0])

    def test_sample_point_single(self):
        tensor_field = TensorField()
        size = 250
        decay = 10
        theta = math.pi / 4
        center = Vector((0.0, 0.0))
        tensor_field.add_grid(center, size, decay, theta)
        point = Vector((1.0, 1.0))
        tensor = tensor_field.sample_point(point)
        weight = (1 - point.length / size) ** decay
        matrix = [math.cos(math.pi / 2) * weight, math.sin(math.pi / 2) * weight]
        self.assertEqual(tensor.r, 2.0)
        self.assertEqual(tensor.matrix, matrix)
        self.assertEqual(tensor.theta, theta)

    def test_sample_point_multi(self):
        tensor_field = TensorField()
        size = 250
        decay = 10
        theta = math.pi / 4
        center_grid = Vector((0.0, 0.0))
        center_radial_1 = Vector((50.0, 10.0))
        center_radial_2 = Vector((100.0, 300.0))
        point = Vector((40.0, 40.0))
        grid = GridBasisField(center_grid, size, decay, theta)
        radial_1 = RadialBasisField(center_radial_1, size, decay)
        radial_2 = RadialBasisField(center_radial_2, size, decay)
        tensor_field.add_grid(center_grid, size, decay, theta)
        tensor_field.add_radial(center_radial_1, size, decay)
        tensor_field.add_radial(center_radial_2, size, decay)
        tensor = Tensor.zero()
        tensor.add(grid.get_weighted_tensor(point))
        tensor.add(radial_1.get_weighted_tensor(point))
        tensor.add(radial_2.get_weighted_tensor(point))
        sample = tensor_field.sample_point(point)
        self.assertEqual(sample.r, tensor.r)
        self.assertEqual(sample.matrix, tensor.matrix)
        self.assertEqual(sample.theta, tensor.theta)
        self.assertEqual(sample.get_major(), tensor.get_major())


if __name__ == "__main__":
    unittest.main()
