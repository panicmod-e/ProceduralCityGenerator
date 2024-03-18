import math
import numpy as np
from mathutils import Vector
from collections import deque
from . grid_storage import GridStorage
from . integrator import FieldIntegrator
from . streamline_parameters import StreamlineParameters
from . simplify import simplify


class StreamlineIntegration:
    def __init__(
            self,
            seed: Vector,
            original_direction: Vector,
            streamline: deque[Vector],
            previous_direction: Vector,
            previous_point: Vector,
            valid: bool):
        self.seed = seed
        self.original_direction = original_direction
        self.streamline = streamline
        self.previous_direction = previous_direction
        self.previous_point = previous_point
        self.valid = valid


class StreamlineGenerator:
    def __init__(
            self,
            integrator: FieldIntegrator,
            origin: Vector,
            world_dimensions: Vector,
            parameters: StreamlineParameters):

        self.SEED_AT_ENDPOINTS = False
        self.NEAR_EDGE = 3

        self.clear_streamlines()

        self.candidate_seeds_major: deque[Vector] = deque([])
        self.candidate_seeds_minor: deque[Vector] = deque([])
        self.streamlines_done = True
        self.last_streamline_major = True
        self.integrator = integrator
        self.origin = origin
        self.world_dimensions = world_dimensions
        self.parameters = parameters
        # parameters.dstep = min(parameters.dstep, parameters.dsep)
        parameters.dtest = min(parameters.dtest, parameters.dsep)
        self.dcollideself_sq = (parameters.dcirclejoin / 2) ** 2
        self.n_streamline_step = math.floor(parameters.dcirclejoin / parameters.dstep)
        self.n_streamline_look_back = 2 * self.n_streamline_step
        self.major_grid = GridStorage(self.world_dimensions, self.origin, parameters.dsep)
        self.minor_grid = GridStorage(self.world_dimensions, self.origin, parameters.dsep)
        self.parameters_sq = self.parameters.copy_sq()

    def clear_streamlines(self):
        self.all_streamlines = deque([])
        self.streamlines_major = deque([])
        self.streamlines_minor = deque([])
        self.all_streamlines_simple = deque([])

    def streamlines(self, major: bool):
        return self.streamlines_major if major else self.streamlines_minor

    def grid(self, major: bool):
        return self.major_grid if major else self.minor_grid

    def simplify_streamline(self, streamline: deque[Vector]):
        return simplify(streamline, self.parameters.simplify_tolerance)

    def join_dangling_streamlines(self):
        for major in [True, False]:
            for streamline in self.streamlines(major):
                # ignore circles
                if streamline[0] == streamline[-1]:
                    continue

                new_start = self.get_best_next_point(streamline[0], streamline[4])
                if new_start is not None:
                    for p in self.points_between(streamline[0], new_start, self.parameters.dstep):
                        streamline.appendleft(p)
                        self.grid(major).add_sample(p)

                new_end = self.get_best_next_point(streamline[-1], streamline[-4])
                if new_end is not None:
                    for p in self.points_between(streamline[-1], new_end, self.parameters.dstep):
                        streamline.append(p)
                        self.grid(major).add_sample(p)

        self.all_streamlines_simple = deque([])
        for s in self.all_streamlines:
            self.all_streamlines_simple.append(self.simplify_streamline(s))

    def points_between(self, v1: Vector, v2: Vector, dstep):
        d = math.sqrt((v1.x - v2.x) ** 2 + (v1.y - v2.y) ** 2)
        n_points = math.floor(d / dstep)
        if n_points == 0:
            return []

        step_vector = v2 - v1

        out = []

        i = 1
        next = v1 + (step_vector * (i / n_points))
        for i in range(1, n_points + 1):
            # test for degenerate point
            if self.integrator.integrate(next, True).length_squared > 0.001:
                out.append(next)
            else:
                return out
            next = v1 + (step_vector * (i / n_points))

        return out

    def get_best_next_point(self, point: Vector, previous_point: Vector):
        nearby_points = self.major_grid.get_nearby_points(point, self.parameters.dlookahead)
        nearby_points.extend(self.minor_grid.get_nearby_points(point, self.parameters.dlookahead))
        direction = point - previous_point

        closest_sample = None
        closest_distance = math.inf

        for sample in nearby_points:
            if sample != point and sample != previous_point:
                difference_vector = sample - point
                if difference_vector.dot(direction) < 0:
                    # backwards
                    continue

                distance_to_sample = (point.x - sample.x) ** 2 + (point.y - sample.y) ** 2
                if distance_to_sample < 2 * self.parameters_sq.dstep:
                    closest_sample = sample
                    break

                angle_between = direction.angle(difference_vector)
                if angle_between < self.parameters.joinangle and distance_to_sample < closest_distance:
                    closest_distance = distance_to_sample
                    closest_sample = sample

        if closest_sample is not None:
            direction.normalize()
            closest_sample = closest_sample + direction * (self.parameters.simplify_tolerance * 4)

        return closest_sample

    def add_existing_streamlines(self, s: 'StreamlineGenerator'):
        self.major_grid.extend(s.major_grid)
        self.minor_grid.extend(s.minor_grid)

    def set_grid(self, s: 'StreamlineGenerator'):
        self.major_grid = s.major_grid
        self.minor_grid = s.minor_grid

    def update(self):
        if not self.streamlines_done:
            self.last_streamline_major = not self.last_streamline_major
            if not self.create_streamline(self.last_streamline_major):
                self.streamlines_done = True
                self.resolve()
            return True
        return False

    def create_all_streamlines(self):
        self.streamlines_done = False
        major = True
        while self.create_streamline(major):
            major = not major
        self.join_dangling_streamlines()

    def create_streamline(self, major: bool):
        seed = self.get_seed(major)
        if seed is None:
            return False
        streamline = self.integrate_streamline(seed, major)
        if self.valid_streamline(streamline):
            self.grid(major).add_polyline(streamline)
            self.streamlines(major).append(streamline)
            self.all_streamlines.append(streamline)

            self.all_streamlines_simple.append(self.simplify_streamline(streamline))

            if not streamline[0] == streamline[-1]:
                self.candidate_seeds(not major).append(streamline[0])
                self.candidate_seeds(not major).append(streamline[-1])

        return True

    def valid_streamline(self, s: deque[Vector]):
        return len(s) > 5

    def sample_point(self):
        rng = np.random.default_rng()
        return Vector((
            rng.random() * self.world_dimensions.x + self.origin.x,
            rng.random() * self.world_dimensions.y + self.origin.y)
        )

    def get_seed(self, major: bool):
        if self.SEED_AT_ENDPOINTS and len(self.candidate_seeds(major)) > 0:
            while len(self.candidate_seeds(major)) > 0:
                seed = self.candidate_seeds(major).pop()
                if self.is_valid_sample(major, seed, self.parameters_sq.dsep):
                    return seed

        seed = self.sample_point()
        i = 0
        while not self.is_valid_sample(major, seed, self.parameters_sq.dsep):
            if i >= self.parameters.seed_tries:
                return None
            seed = self.sample_point()
            i += 1
        return seed

    def is_valid_sample(self, major: bool, point: Vector, d_sq, both_grids=False):
        grid_valid = self.grid(major).is_valid_sample(point, d_sq)
        if both_grids:
            grid_valid = grid_valid and self.grid(not major).is_valid_sample(point, d_sq)
        return grid_valid

    def candidate_seeds(self, major: bool):
        return self.candidate_seeds_major if major else self.candidate_seeds_minor

    def point_in_bounds(self, v: Vector):
        # return v.x >= self.origin.x
        #   and v.y >= self.origin.y
        #   and v.x < self.world_dimensions.x + self.origin.x
        #   and v.y < self.world_dimensions.y + self.origin.y
        return (
            self.origin.x <= v.x < self.world_dimensions.x + self.origin.x
            and self.origin.y <= v.y < self.world_dimensions.y + self.origin.y
        )

    def streamline_turned(self, seed: Vector, original_direction: Vector, point: Vector, direction: Vector):
        if original_direction.dot(direction) < 0:
            perpendicular_vector = Vector((original_direction.y, -original_direction.x))
            is_left = (point - seed).dot(perpendicular_vector) < 0
            direction_up = direction.dot(perpendicular_vector) > 0
            return is_left == direction_up
        return False

    def streamline_integration_step(self, parameters: StreamlineIntegration, major: bool, collide_both: bool):
        if parameters.valid:
            parameters.streamline.append(parameters.previous_point)
            next_direction: Vector = self.integrator.integrate(parameters.previous_point, major)

            if next_direction.length_squared < 0.01:
                parameters.valid = False
                return

            if next_direction.dot(parameters.previous_direction) < 0:
                next_direction = next_direction * -1

            next_point = parameters.previous_point + next_direction

            if (
                self.point_in_bounds(next_point)
                and self.is_valid_sample(major, next_point, self.parameters_sq.dtest, collide_both)
                and not self.streamline_turned(
                    parameters.seed,
                    parameters.original_direction,
                    next_point,
                    next_direction)
            ):
                parameters.previous_point = next_point
                parameters.previous_direction = next_direction
            else:
                parameters.streamline.append(next_point)
                parameters.valid = False

    def integrate_streamline(self, seed: Vector, major: bool) -> deque[Vector]:
        count = 0
        points_escaped = False
        rng = np.random.default_rng()
        collide_both = rng.random() < self.parameters.collide_early

        d = self.integrator.integrate(seed, major)
        forward_parameters: StreamlineIntegration = StreamlineIntegration(
            seed=seed,
            original_direction=d,
            streamline=deque([seed]),
            previous_direction=d,
            previous_point=seed + d,
            valid=True)
        forward_parameters.valid = self.point_in_bounds(forward_parameters.previous_point)

        negative_d = d * -1
        backwards_parameters: StreamlineIntegration = StreamlineIntegration(
            seed=seed,
            original_direction=negative_d,
            streamline=deque([]),
            previous_direction=negative_d,
            previous_point=seed + negative_d,
            valid=True)
        backwards_parameters.valid = self.point_in_bounds(backwards_parameters.previous_point)

        while count < self.parameters.path_iterations and (forward_parameters.valid or backwards_parameters.valid):
            self.streamline_integration_step(forward_parameters, major, collide_both)
            self.streamline_integration_step(backwards_parameters, major, collide_both)

            sq_distance_between_points = (
                (forward_parameters.previous_point.x - backwards_parameters.previous_point.x) ** 2
                + (forward_parameters.previous_point.y - backwards_parameters.previous_point.y) ** 2
            )

            if not points_escaped and sq_distance_between_points > self.parameters_sq.dcirclejoin:
                points_escaped = True

            if points_escaped and sq_distance_between_points <= self.parameters_sq.dcirclejoin:
                forward_parameters.streamline.append(forward_parameters.previous_point)
                forward_parameters.streamline.append(backwards_parameters.previous_point)
                backwards_parameters.streamline.append(backwards_parameters.previous_point)
                break

            count += 1

        backwards_parameters.streamline.reverse()
        backwards_parameters.streamline.extend(forward_parameters.streamline)
        return backwards_parameters.streamline
