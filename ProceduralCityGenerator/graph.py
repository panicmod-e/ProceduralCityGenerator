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

        self.edges = []
        self.border_edges = []

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

    def add_neighbor(self, neighbor: 'DirectedEdge'):
        self.neighbors.append(neighbor)

    def add_border_neighbor(self, neighbor: 'DirectedEdge'):
        self.border_neighbors.append(neighbor)

    def add_edge(self, edge: 'UndirectedEdge'):
        self.edges.append(edge)

    def add_border_edge(self, edge: 'UndirectedEdge'):
        self.border_edges.append(edge)


class Edge():
    def __init__(self, start_node: Node, end_node: Node, connection: deque[Vector], visited=False):
        self.start_node = start_node
        self.end_node = end_node
        self.connection = connection
        self.visited = visited


class UndirectedEdge(Edge):
    def __init__(self, start_node: Node, end_node: Node, connection: deque[Vector], visited=False):
        super().__init__(start_node, end_node, connection, visited)
        self.directed_edges = []
        self._direction = None
        self._direction_backwards = None

    def set_directed_edges(self, edges: list['DirectedEdge']):
        self.directed_edges = edges

    @property
    def direction(self):
        if self._direction is None:
            self._direction = self.connection[1] - self.connection[0]
        return self._direction

    @property
    def direction_backwards(self):
        if self._direction_backwards is None:
            self.direction_backwards = self.connection[-2] - self.connection[-1]
        return self._direction_backwards


class DirectedEdge(Edge):
    def __init__(self, start_node: Node, end_node: Node, connection: deque[Vector], visited=False):
        super().__init__(start_node, end_node, connection, visited)
        self.undirected_edge = None
        self._direction = None
        self._direction_backwards = None

    def set_undirected_edge(self, edge: UndirectedEdge):
        self.undirected_edge = edge

    @property
    def direction(self):
        if self._direction is None:
            next_point = self.connection[0] if self.connection else self.end_node.co
            self._direction = next_point - self.start_node.co
        return self._direction

    @property
    def direction_backwards(self):
        if self._direction_backwards is None:
            next_point = self.connection[-1] if self.connection else self.start_node.co
            self._direction_backwards = next_point - self.end_node.co
        return self._direction_backwards


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
        self.directed_edges: list[DirectedEdge] = []
        self.directed_border_edges: list[DirectedEdge] = []
        self.edges: list[UndirectedEdge] = []
        self.border_edges: list[UndirectedEdge] = []
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

                start_neighbor = DirectedEdge(start_node, end_node, connection)
                end_neighbor = DirectedEdge(end_node, start_node, connection_reversed)
                self.directed_edges.append(start_neighbor)
                self.directed_edges.append(end_neighbor)

                start_node.add_neighbor(start_neighbor)
                end_node.add_neighbor(end_neighbor)

                edge = UndirectedEdge(start_node, end_node, section)
                self.edges.append(edge)
                start_node.add_edge(edge)
                end_node.add_edge(edge)

                start_neighbor.set_undirected_edge(edge)
                end_neighbor.set_undirected_edge(edge)
                edge.set_directed_edges([start_neighbor, end_neighbor])

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
        top_left = Node(origin + Vector((0.0, dimensions.y)), origin, dimensions, dstep)
        top_right = Node(origin + dimensions, origin, dimensions, dstep)
        bottom_left = Node(origin, origin, dimensions, dstep)
        bottom_right = Node(origin + Vector((dimensions.x, 0.0)), origin, dimensions, dstep)
        self.nodes.append(top_left)
        self.nodes.append(top_right)
        self.nodes.append(bottom_left)
        self.nodes.append(bottom_right)
        limit = dimensions + origin
        for node in self.nodes:
            if abs(node.co.x - (origin.x)) <= epsilon or node.co.x < origin.x:
                left_nodes.append(node)
            if abs(node.co.y - (origin.y)) <= epsilon or node.co.y < origin.y:
                bottom_nodes.append(node)
            if abs(node.co.x - (origin.x + dimensions.x)) <= epsilon or node.co.x > limit.x:
                right_nodes.append(node)
            if abs(node.co.y - (origin.y + dimensions.y)) <= epsilon or node.co.y > limit.y:
                top_nodes.append(node)
        left_nodes.sort(key=lambda n: n.co.y)
        bottom_nodes.sort(key=lambda n: n.co.x, reverse=True)
        right_nodes.sort(key=lambda n: n.co.y, reverse=True)
        top_nodes.sort(key=lambda n: n.co.x)

        for border in [left_nodes, bottom_nodes, right_nodes, top_nodes]:
            self.add_neighboring_node_connections(border)

    def add_neighboring_node_connections(self, nodes: list[Node]):
        if len(nodes) < 2:
            return
        for i in range(len(nodes) - 1):
            node = nodes[i]
            other_node = nodes[i + 1]
            start_neighbor = DirectedEdge(node, other_node, deque([]))
            end_neighbor = DirectedEdge(other_node, node, deque([]), visited=True)
            self.directed_border_edges.append(start_neighbor)
            self.directed_border_edges.append(end_neighbor)
            edge = UndirectedEdge(node, other_node, deque([node.co, other_node.co]))
            self.border_edges.append(edge)
            start_neighbor.set_undirected_edge(edge)
            end_neighbor.set_undirected_edge(edge)
            edge.set_directed_edges([start_neighbor, end_neighbor])
            node.add_border_neighbor(start_neighbor)
            other_node.add_border_neighbor(end_neighbor)
            node.add_border_edge(edge)
            other_node.add_border_edge(edge)

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
