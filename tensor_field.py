from tensor import Tensor
from basis_field import GridBasisField, RadialBasisField


class TensorField:
    def __init__(self):
        self.basis_fields = []
        self.smooth = False

    def add_grid(self, center, size, decay, theta):
        grid = GridBasisField(center, size, decay, theta)
        self.add_field(grid)

    def add_radial(self, center, size, decay):
        radial = RadialBasisField(center, size, decay)
        self.add_field(radial)

    def add_field(self, field):
        self.basis_fields.append(field)

    def remove_field(self, field):
        self.basis_fields.remove(field)

    def reset(self):
        self.basis_fields = []

    def get_center_points(self):
        return [field.center for field in self.basis_fields]

    def get_basis_fields(self):
        return self.basis_fields

    def sample_point(self, point):
        # check if point is valid in case of water etc. here

        if not self.basis_fields:
            return Tensor(1, [0, 0])

        tensor_acc = Tensor.zero()
        for field in self.basis_fields:
            tensor_acc.add(field.get_weighted_tensor(point, self.smooth), self.smooth)

        # rotational noise for parks added here if applicable

        # global noise added here if applicable

        return tensor_acc
