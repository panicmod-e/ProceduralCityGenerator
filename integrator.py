from . tensor_field import TensorField
from mathutils import Vector
from . streamline_parameters import StreamlineParameters


# Integrators are used for iterative approximate discretization/integration of stream-
# lines.
class FieldIntegrator:
    def __init__(self, field: TensorField):
        self.field = field

    def integrate(self, point: Vector, major: bool):
        pass

    def sample_field_vector(self, point: Vector, major: bool) -> Vector:
        tensor = self.field.sample_point(point)
        if major:
            return tensor.get_major()
        return tensor.get_minor()


class EulerIntegrator(FieldIntegrator):
    def __init__(self, field: TensorField, parameters: StreamlineParameters):
        super().__init__(field)
        self.parameters = parameters

    def integrate(self, point: Vector, major: bool) -> Vector:
        return self.sample_field_vector(point, major).xy * self.parameters.dstep


# The classic Runge-Kutta method, RK4.
class RK4Integrator(FieldIntegrator):
    def __init__(self, field: TensorField, parameters: StreamlineParameters):
        super().__init__(field)
        self.parameters = parameters

    def integrate(self, point: Vector, major: bool) -> Vector:
        k1 = self.sample_field_vector(point, major)
        k23 = self.sample_field_vector(
            point + Vector((self.parameters.dstep / 2, self.parameters.dstep / 2)), major)
        k4 = self.sample_field_vector(
            point + Vector((self.parameters.dstep, self.parameters.dstep)), major)
        return (k1 + (k23 * 4) + k4) * (self.parameters.dstep / 6)
