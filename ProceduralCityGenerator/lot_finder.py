import math
from mathutils import Vector
from ProceduralCityGenerator.graph import Graph, DirectedEdge


class Lot():
    def __init__(self, vertices: list[Vector]):
        self.vertices = vertices


class LotFinder():
    def __init__(self, graph: Graph):
        self.graph = graph
        self._lots = []

    @property
    def lots(self):
        if self._lots:
            return self._lots
        else:
            self.find_lots()
            return self._lots

    def find_lots(self):
        nodes = self.graph.nodes
        for node in nodes:
            neighbors = node.neighbors
            for neighbor in neighbors:
                if not neighbor.visited:
                    vertices = self.find_adjacent_lot(neighbor)
                    self._lots.append(vertices)

    def find_adjacent_lot(self, start_neighbor: DirectedEdge):
        visited_neighbors = []
        vertices = []
        neighbor = start_neighbor
        while neighbor is not None and not neighbor.visited:
            vertices.append(neighbor.start_node.co)
            for vertex in neighbor.connection:
                vertices.append(vertex)
            neighbor.visited = True
            visited_neighbors.append(neighbor)
            neighbor = self.get_clockwise_neighbor_long(neighbor)
        return vertices

    def find_adjacent_lot_alt(self, start_neighbor: DirectedEdge):
        vertices = []
        neighbor = start_neighbor
        while neighbor is not None and not neighbor.visited:
            for vertex in neighbor.connection:
                vertices.append(vertex)
            vertices.append(neighbor.end_node.co)
            neighbor.visited = True
            neighbor = self.get_clockwise_neighbor_long(neighbor)
        return vertices

    def get_clockwise_neighbor(self, edge: DirectedEdge):
        # neighbors = [*edge.end_node.neighbors, *edge.end_node.border_neighbors]
        neighbors = edge.end_node.neighbors
        if neighbors and len(neighbors) == 1:
            return neighbors[0]
        neighbors = [e for e in neighbors if e.end_node is not edge.start_node]
        if neighbors:
            neighbors.sort(key=lambda n: self.get_signed_angle(edge.direction_backwards, n.direction), reverse=True)
            return neighbors[0]
        return None

    def get_clockwise_neighbor_long(self, edge: DirectedEdge):
        # neighbors = [*edge.end_node.neighbors, *edge.end_node.border_neighbors]
        neighbors = edge.end_node.neighbors
        if neighbors and len(neighbors) == 1:
            return neighbors[0]
        # neighbors = [e for e in neighbors if e.end_node is not edge.start_node]
        if neighbors:
            next_neighbor = neighbors[0]
            next_angle = edge.direction_backwards.angle_signed(next_neighbor.direction, 0)
            for i in range(1, len(neighbors)):
                n = neighbors[i]
                n_angle = edge.direction_backwards.angle_signed(n.direction, 0)
                if ((next_angle < 0 and n_angle < 0) or (next_angle >= 0 and n_angle >= 0)):
                    if (n_angle > next_angle):
                        next_angle = n_angle
                        next_neighbor = n
                if (next_angle >= 0 and n_angle < 0):
                    next_angle = n_angle
                    next_neighbor = n
            return next_neighbor
        return None

    def get_signed_angle(self, vector: Vector, other: Vector):
        angle = vector.angle_signed(other, -math.pi * 4)
        angle = angle if angle <= 0 else angle - math.pi * 2
        return angle
