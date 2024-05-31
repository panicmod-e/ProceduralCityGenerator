import math
from mathutils import Vector


# Cartesian grid data structure based on the open source implementation of ProbableTrain.
# Used to find nearby points and check separation distance, by dividing domain into grid
# of cells containing points.
#
# - Note: would like to replace this with a proper spatial index that could then be used
#   for improved intersection detection as well (Quadtree, [Hilbert] R-Tree, PH-Tree).
class GridStorage:
    def __init__(self, world_dimensions: Vector, origin: Vector, dsep):
        # Grid assumes origin point (0.0, 0.0).
        # dsep represents separation distance between samples.
        self.world_dimensions: Vector = world_dimensions
        self.origin: Vector = origin
        self.dsep = dsep
        self.dsep_sq = self.dsep ** 2
        self.grid_dimensions = Vector((world_dimensions.x / dsep, world_dimensions.y / dsep))
        self.grid = []
        for x in range(0, math.ceil(self.grid_dimensions.x)):
            self.grid.append([])
            for y in range(0, math.ceil(self.grid_dimensions.y)):
                self.grid[x].append([])

    def add_all(self, grid_storage):
        for row in grid_storage.grid:
            for cell in row:
                for sample in cell:
                    self.add_sample(sample)

    def add_polyline(self, line):
        for v in line:
            self.add_sample(v)

    def add_sample(self, v, coords=None):
        if coords is None:
            coords = self.get_sample_coords(v)
        self.grid[int(coords.x)][int(coords.y)].append(v)

    def is_valid_sample(self, v, d_sq=None) -> bool:
        if d_sq is None:
            d_sq = self.dsep_sq
        coords = self.get_sample_coords(v)

        for x in range(-1, 2):
            for y in range(-1, 2):
                cell = Vector((coords.x + x, coords.y + y))
                if not self.vector_out_of_bounds(cell, self.grid_dimensions):
                    if not self.vector_far_from_vectors(v, self.grid[int(cell.x)][int(cell.y)], d_sq):
                        return False
        return True

    # called every integration step
    def vector_far_from_vectors(self, v, vectors, d_sq) -> bool:
        for sample in vectors:
            if sample != v:
                distance_sq = (sample.x - v.x) ** 2 + (sample.y - v.y) ** 2
                if distance_sq < d_sq:
                    return False
        return True

    def get_nearby_points(self, v, distance):
        radius = math.ceil((distance / self.dsep) - 0.5)
        coords = self.get_sample_coords(v)
        out = []
        for x in range(-1 * radius, 1 * radius + 1):
            for y in range(-1 * radius, 1 * radius + 1):
                cell = Vector((coords.x + x, coords.y + y))
                if not self.vector_out_of_bounds(cell, self.grid_dimensions):
                    for v2 in self.grid[int(cell.x)][int(cell.y)]:
                        out.append(v2)
        return out

    def world_to_grid(self, v) -> Vector:
        return v - self.origin

    def grid_to_world(self, v) -> Vector:
        return v + self.origin

    def vector_out_of_bounds(self, grid_v: Vector, bounds: Vector):
        return grid_v.x < 0 or grid_v.y < 0 or grid_v.x >= bounds.x or grid_v.y >= bounds.y

    # called every integration step
    def get_sample_coords(self, world_v: Vector) -> Vector:
        v = self.world_to_grid(world_v)
        if self.vector_out_of_bounds(v, self.world_dimensions):
            return Vector((0.0, 0.0))
        return Vector((math.floor(v.x / self.dsep), math.floor(v.y / self.dsep)))
