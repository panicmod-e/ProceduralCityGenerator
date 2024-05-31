import math
from mathutils import Vector
from mathutils import geometry
from collections import deque
from enum import Enum
# from . grid_storage import GridStorage
# from . integrator import FieldIntegrator
# from . streamline_parameters import StreamlineParameters
# from . simplify import simplify
from ProceduralCityGenerator.streamlines import StreamlineGenerator


class NodeType(Enum):
    INNER = 1
    BORDER = 2
    DEADEND = 3


# Node of the resulting graph, that holds own coordinates and a list of neighboring nodes,
# alongside the polyline between itself and the neighbor.
class Node():
    def __init__(self, co: Vector, origin: Vector, dimensions: Vector, dstep):
        self.co = co
        self.neighbors = []
        # border_neighbors contains neighboring nodes along the border of the domain, not connected via roads.
        # Implemented to support future polygon finding along the edges of the current rectangular domain.
        self.border_neighbors = []
        self.field_origin = origin
        self.field_dimensions = dimensions
        self.epsilon = dstep / 2

    @property
    def node_type(self):
        if any([
            abs(self.co.x - (self.field_origin.x + self.field_dimensions.x)) <= self.epsilon,
            abs(self.co.x - self.field_origin.x) <= self.epsilon,
            abs(self.co.y - (self.field_origin.y + self.field_dimensions.y)) <= self.epsilon,
            abs(self.co.y - self.field_origin.y) <= self.epsilon
        ]):
            return NodeType.BORDER
        if len(self.neighbors) < 2:
            return NodeType.DEADEND
        return NodeType.INNER

    def add_neighbor(self, neighbor: 'Neighbor'):
        self.neighbors.append(neighbor)

    def add_border_neighbor(self, neighbor: 'Neighbor'):
        self.border_neighbors.append(neighbor)


# Neighbor class holding a node and the polyline leading from another node to self.
class Neighbor():
    def __init__(self, node: Node, connection: deque[Vector]):
        self.node = node
        self.connection = connection


# Builds the resulting road graph from the generated streamline polylines.
# The graph is represented as a list of Nodes, each containing a list of neighbors, with corresponding
# road segment.
# Road/streamline segments are also saved separately, but not used as is in the final graph.
#
# Intersection detection uses brute-force implementation, testing all streamline segments against each other.
# Graph generation is based on simplified streamlines by default. Using the complex streamlines as a base
# takes a very long time with the current implementation.
class Graph():
    def __init__(self, streamlines: StreamlineGenerator, complex=False):
        self.streamlines = streamlines
        self.all_streamlines = streamlines.all_streamlines if complex else streamlines.all_streamlines_simple
        streamline_sections = deque([])
        for i in range(len(self.all_streamlines)):
            streamline_sections.append(deque([]))
        self.streamline_sections = streamline_sections
        self.nodes: list[Node] = []
        self.generate_graph()

    def generate_graph(self):
        self.generate_streamline_sections()
        self.generate_nodes()
        self.add_border_connections()

    # Find intersections along each streamline and split streamline into sections at intersection points.
    # Original streamlines are preserved, turns representation of streamlines from polylines to sections
    # of polylines, starting and ending at intersection points.
    # Start and end segments of streamlines that do NOT lie at the border of the domain get extended slightly
    # to ensure T-intersections are properly found.
    #
    # Depending on the magnitute of the segment, multiple other streamlines can intersect the same segment.
    def generate_streamline_sections(self):
        for i in range(len(self.all_streamlines)):
            streamline = self.all_streamlines[i]
            section = deque([streamline[0]])
            # Extend start of streamline slightly, to check for T-intersection.
            # Also tests for intersections with itself, which can happen in the current implementation,
            # probably due to inaccuracies in the current integration around circular elements in the tensor field.
            if not (self.streamline_is_circle(streamline) or self.point_on_world_border(streamline[0])):
                direction = streamline[0] - streamline[1]
                direction.normalize()
                segment_end = streamline[0] + (direction * self.streamlines.parameters.dstep * 1.5)
                segment_start = streamline[0]
                intersections = self.find_intersections(segment_start, segment_end, streamline, -1)
                if intersections:
                    section.appendleft(intersections[0])
            # Test each segment of the streamline for intersections.
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
            # Join start and end section of circular streamlines, if they should connect.
            if self.streamline_is_circle(self.all_streamlines[i]) and self.streamline_sections[i]:
                section.pop()
                self.streamline_sections[i][0].extendleft(reversed(section))
            else:
                # Extend end of streamline slightly, to check for T-intersections.
                if not self.point_on_world_border(streamline[-1]):
                    direction = streamline[-1] - streamline[-2]
                    direction.normalize()
                    segment_end = streamline[-1] + (direction * self.streamlines.parameters.dstep * 1.5)
                    segment_start = streamline[-1]
                    intersections = self.find_intersections(segment_start, segment_end, streamline, len(streamline) - 2)
                    if intersections:
                        section.append(intersections[0])
                self.streamline_sections[i].append(section)

    # Finds intersections of given segment, denoted by segment_start and segment_end, and all other segments.
    # Skips segments on the same streamline and connected to the given segment.
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
            # Extend other streamlines start and end points slightly, if they don't end at domain borders.
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

    # Takes the generated streamline sections and turns start and end points into nodes and neighbors.
    # New nodes are saved to list of existing nodes.
    def generate_nodes(self):
        dstep = self.streamlines.parameters.dstep
        tolerance = dstep / 2
        origin = self.streamlines.origin
        dimensions = self.streamlines.world_dimensions
        for streamline in self.streamline_sections:
            for section in streamline:
                start = section[0]
                start_node = None
                end = section[-1]
                end_node = None
                # Check if any already existing nodes are close enough to the section start/end point to be
                # considered the same.
                for node in self.nodes:
                    if (
                        start_node is None
                        and math.sqrt((node.co.x - start.x) ** 2 + (node.co.y - start.y) ** 2) <= tolerance
                    ):
                        start_node = node
                    elif (
                        end_node is None
                        and math.sqrt((node.co.x - end.x) ** 2 + (node.co.y - end.y) ** 2) <= tolerance
                    ):
                        end_node = node
                    if start_node is not None and end_node is not None:
                        break
                # If no existing nodes match start/end points, create new node.
                if start_node is None:
                    start_node = Node(start, origin, dimensions, dstep)
                    self.nodes.append(start_node)
                if end_node is None:
                    end_node = Node(end, origin, dimensions, dstep)
                    self.nodes.append(end_node)
                # Adds the start/end node of the current section as a neighbor to the respective other node.
                # The polyline section between the node and the neighbor is saved as well.
                # The section leading from end node to start node is reversed to ensure that the connections are
                # consistent and the polyline points are in the correct order from node to neighbor.
                connection = section.copy()
                connection.pop()
                connection.popleft()
                connection_reversed = connection.copy()
                connection_reversed.reverse()
                start_node.add_neighbor(Neighbor(end_node, connection))
                end_node.add_neighbor(Neighbor(start_node, connection_reversed))

    # Finds all nodes and corner points along each border of the domain and adds the nearest neighbors along
    # the border as a border_neighbor to all border nodes.
    def add_border_connections(self):
        origin = self.streamlines.origin
        dimensions = self.streamlines.world_dimensions
        dstep = self.streamlines.parameters.dstep
        epsilon = dstep / 2
        left_nodes: list[Node] = []
        bottom_nodes: list[Node] = []
        right_nodes: list[Node] = []
        top_nodes: list[Node] = []
        top_left = Node(origin + Vector((dimensions.x, 0.0)), origin, dimensions, dstep)
        top_right = Node(origin + dimensions, origin, dimensions, dstep)
        bottom_left = Node(origin, origin, dimensions, dstep)
        bottom_right = Node(origin + Vector((0.0, dimensions.y)), origin, dimensions, dstep)
        for node in self.nodes:
            if abs(node.co.x - (origin.x)) <= epsilon:
                left_nodes.append(node)
            if abs(node.co.y - (origin.y)) <= epsilon:
                bottom_nodes.append(node)
            if abs(node.co.x - (origin.x + dimensions.x)) <= epsilon:
                right_nodes.append(node)
            if abs(node.co.y - (origin.y + dimensions.y)) <= epsilon:
                top_nodes.append(node)
        left_nodes.sort(key=lambda n: n.co.y)
        bottom_nodes.sort(key=lambda n: n.co.x)
        right_nodes.sort(key=lambda n: n.co.y)
        top_nodes.sort(key=lambda n: n.co.x)
        left_nodes[0].add_border_neighbor(Neighbor(bottom_left, deque([])))
        left_nodes[-1].add_border_neighbor(Neighbor(top_left, deque([])))
        bottom_nodes[0].add_border_neighbor(Neighbor(bottom_left, deque([])), )
        bottom_nodes[-1].add_border_neighbor(Neighbor(bottom_right, deque([])))
        right_nodes[0].add_border_neighbor(Neighbor(bottom_right, deque([])))
        right_nodes[-1].add_border_neighbor(Neighbor(top_right, deque([])))
        top_nodes[0].add_border_neighbor(Neighbor(top_left, deque([])))
        top_nodes[-1].add_border_neighbor(Neighbor(top_right, deque([])))
        for border in [left_nodes, bottom_nodes, right_nodes, top_nodes]:
            self.add_neighboring_node_connections(border)

    def add_neighboring_node_connections(self, nodes: list[Node]):
        for i in range(len(nodes)):
            node = nodes[i]
            for j in [i - 1, i + 1]:
                if j in range(len(nodes)):
                    neighbor = Neighbor(nodes[j], deque([]))
                    node.add_border_neighbor(neighbor)

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
