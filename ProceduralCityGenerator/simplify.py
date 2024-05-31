from mathutils import Vector
from collections import deque


# This file offers a custom implementation of the Douglas-Peucker polyline simplification
# algorithm to work with mathutils Vectors. The implementation is based on the simplify.js
# JavaScript library.
def get_square_segment_distance(p: Vector, p1: Vector, p2: Vector):
    x = p1.x
    y = p1.y
    dx = p2.x - x
    dy = p2.y - y

    if dx != 0 or dy != 0:
        t = ((p.x - x) * dx + (p.y - y) * dy) / (dx * dx + dy * dy)
        if t > 1:
            x = p2.x
            y = p2.y
        elif t > 0:
            x += dx * t
            y += dy * t

    dx = p.x - x
    dy = p.y - y
    return dx * dx + dy * dy


def simplify_dp_step(points: deque[Vector], first: int, last: int, sq_tolerance: float, simplified: deque[Vector]):
    max_sq_dist = sq_tolerance
    index = None

    for i in range(first + 1, last):
        sq_dist = get_square_segment_distance(points[i], points[first], points[last])
        if sq_dist > max_sq_dist:
            index = i
            max_sq_dist = sq_dist

    if max_sq_dist > sq_tolerance:
        if index - first > 1:
            simplify_dp_step(points, first, index, sq_tolerance, simplified)
        simplified.append(points[index])
        if last - index > 1:
            simplify_dp_step(points, index, last, sq_tolerance, simplified)


def simplify_douglas_peucker(points: deque[Vector], sq_tolerance: float) -> deque[Vector]:
    last = len(points) - 1
    simplified = deque([points[0]])
    simplify_dp_step(points, 0, last, sq_tolerance, simplified)
    simplified.append(points[last])
    return simplified


def simplify(points: deque[Vector], tolerance=1.0) -> deque[Vector]:
    if len(points) <= 2:
        return points
    sq_tolerance = tolerance * tolerance

    return simplify_douglas_peucker(points, sq_tolerance)
