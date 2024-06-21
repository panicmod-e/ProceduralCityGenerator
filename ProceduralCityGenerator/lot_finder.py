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
            neighbor = self.get_clockwise_neighbor(neighbor)
        return vertices

    def get_clockwise_neighbor(self, edge: DirectedEdge):
        neighbors = [*edge.end_node.neighbors, *edge.end_node.border_neighbors]
        if neighbors and len(neighbors) == 1:
            return neighbors[0]
        neighbors = [e for e in neighbors if e.end_node is not edge.start_node]
        if neighbors:
            neighbors.sort(key=lambda n: self.get_signed_angle(edge.direction_backwards, n.direction), reverse=True)
            return neighbors[0]
        return None

    def get_signed_angle(self, vector: Vector, other: Vector):
        angle = vector.angle_signed(other, -math.pi * 4)
        angle = angle if angle <= 0 else angle - math.pi * 2
        return angle
