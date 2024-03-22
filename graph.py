import math
from mathutils import Vector
from mathutils import geometry
from collections import deque
# from . grid_storage import GridStorage
# from . integrator import FieldIntegrator
# from . streamline_parameters import StreamlineParameters
# from . simplify import simplify
from . streamlines import StreamlineGenerator


class Node():
    def __init__(self, co: Vector):
        self.co = co
        self.neighbors = {}


class Graph():
    def __init__(self, streamlines: StreamlineGenerator, complex=False):
        self.streamlines = streamlines
        self.all_streamlines = streamlines.all_streamlines if complex else streamlines.all_streamlines_simple
        streamline_sections = deque([])
        for i in range(len(self.all_streamlines)):
            streamline_sections.append(deque([]))
        self.streamline_sections = streamline_sections
        self.generate_streamline_sections()

    def generate_graph(self):
        self.generate_streamline_sections()

    def generate_streamline_sections(self):
        for i in range(len(self.all_streamlines)):
            streamline = self.all_streamlines[i]
            section = deque([streamline[0]])
            if not (self.streamline_is_circle(streamline) or self.point_on_world_border(streamline[0])):
                direction = streamline[0] - streamline[1]
                direction.normalize()
                segment_end = streamline[0] + (direction * self.streamlines.parameters.dstep * 1.5)
                segment_start = streamline[0]
                intersections = self.find_intersections(segment_start, segment_end, streamline, -1)
                if intersections:
                    section.appendleft(intersections[0])
            for j in range(len(streamline) - 1):
                segment_start = streamline[j]
                segment_end = streamline[j + 1]
                intersections = self.find_intersections(segment_start, segment_end, streamline, j)
                if intersections:
                    for intersection in intersections:
                        section.append(intersection)
                        self.streamline_sections[i].append(section)
                        section = deque([intersection])
                    section.append(segment_end)
                else:
                    section.append(segment_end)
            if self.streamline_is_circle(self.all_streamlines[i]) and self.streamline_sections[i]:
                section.pop()
                self.streamline_sections[i][0].extendleft(reversed(section))
            else:
                if not self.point_on_world_border(streamline[-1]):
                    direction = streamline[-1] - streamline[-2]
                    direction.normalize()
                    segment_end = streamline[-1] + (direction * self.streamlines.parameters.dstep * 1.5)
                    segment_start = streamline[-1]
                    intersections = self.find_intersections(segment_start, segment_end, streamline, len(streamline) - 2)
                    if intersections:
                        section.append(intersections[0])
                self.streamline_sections[i].append(section)

    def find_intersections(
            self,
            segment_start: Vector,
            segment_end: Vector,
            streamline: deque[Vector],
            index,
    ) -> Vector:
        intersections = deque([])
        for s in self.all_streamlines:
            if s is streamline and self.streamline_is_circle(s):
                continue
            for i in range(len(s) - 1):
                if s is streamline and i in range(index - 1, index + 2):
                    continue
                other_start = s[i]
                other_end = s[i + 1]
                intersection = geometry.intersect_line_line_2d(segment_start, segment_end, other_start, other_end)
                if intersection is not None:
                    intersections.append(intersection)
            if not self.streamline_is_circle(s):
                if not self.point_on_world_border(s[0]):
                    intersection = self.find_endpoint_intersections(s[0], s[1], segment_start, segment_end)
                    if intersection is not None:
                        intersections.append(intersection)
                if not self.point_on_world_border(s[-1]):
                    intersection = self.find_endpoint_intersections(s[-1], s[-2], segment_start, segment_end)
                    if intersection is not None:
                        intersections.append(intersection)
        if len(intersections) > 1:
            intersections = sorted(
                intersections,
                key=lambda p: math.sqrt((p.x - segment_start.x) ** 2 + (p.y - segment_start.y) ** 2)
            )
        return intersections

    def generate_nodes(self):
        pass

    def point_on_world_border(self, point: Vector):
        world_dimensions = self.streamlines.world_dimensions
        origin = self.streamlines.origin
        epsilon = self.streamlines.parameters.dstep / 2
        return any([
            abs(point.x - (origin.x + world_dimensions.x)) <= epsilon,
            abs(point.x - origin.x) <= epsilon,
            abs(point.y - (origin.y + world_dimensions.y)) <= epsilon,
            abs(point.y - origin.y) <= epsilon
        ])

    def find_endpoint_intersections(
            self,
            endpoint: Vector,
            previous_point: Vector,
            segment_start: Vector,
            segment_end: Vector
    ) -> Vector | None:
        direction = endpoint - previous_point
        direction.normalize()
        endpoint_extension = endpoint + (direction * self.streamlines.parameters.dstep * 1.5)
        if any([endpoint is segment_start, endpoint is segment_end]):
            return None
        return geometry.intersect_line_line_2d(segment_start, segment_end, endpoint_extension, endpoint)

    def streamline_is_circle(self, streamline):
        return streamline[0] == streamline[-1]
