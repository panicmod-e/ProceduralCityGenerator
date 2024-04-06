import bpy
import bmesh
# import math
# import numpy as np
from mathutils import Vector
from time import time
# from . tensor import Tensor
from . streamlines import StreamlineGenerator
from . tensor_field import TensorField
# from . basis_field import BasisField, GridBasisField, RadialBasisField
# from . grid_storage import GridStorage
from . integrator import RK4Integrator
from . streamline_parameters import StreamlineParameters
from . graph import Graph


bl_info = {
    "name": "Grid Generator Spike",
    "blender": (3, 6, 0),
    "category": "Object"
}


###############################################################
#
# Integrates implemented road graph generation with Blender.
# Currently used for testing and visualization purposes only.
#
###############################################################


class GridGenBasePanel():
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "grid gen"


# Creates panel in the 3D Viewport sidebar (open with 'N' by default).
# Includes button to execute main function and test generation of road graph based on tensor field
# defined manually below.
class GridGenGridPanel(GridGenBasePanel, bpy.types.Panel):
    bl_label = "Grid Generator"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.operator("operator.grid_gen_generate")


class GridGenGenerateGrid(bpy.types.Operator):
    bl_idname = "operator.grid_gen_generate"
    bl_label = "Generate"

    def execute(self, context):
        main()

        return {'FINISHED'}


classes = [
    GridGenGridPanel,
    GridGenGenerateGrid
]


def main():
    print("-- starting generation --")

    # Create new global TensorField
    field = TensorField()

    # Create new StreamlineParameters. Values used here are derived from testing and seem like a good baseline
    parameters = StreamlineParameters(
        dsep=100,
        dtest=30,
        dstep=1,
        dcirclejoin=5,
        dlookahead=200,
        joinangle=0.1,
        path_iterations=1500,
        seed_tries=500,
        simplify_tolerance=0.01,
        collide_early=0,
    )

    # Create new RK4Integrator with tensor field and parameters as input.
    integrator = RK4Integrator(
        field,
        parameters
    )

    # Create new StreamlineGenerator with integrator, parameters, and origin + world dimensions as input variables.
    # Current testing shows that integer values based on common screen sizes work well.
    generator = StreamlineGenerator(
        integrator=integrator,
        origin=Vector((519, 249)),
        world_dimensions=Vector((1452, 1279)),
        parameters=parameters,
    )

    # Add two grid and one radial basis field to the global field.
    field.add_grid(Vector((1381, 788)), 1500, 35, 1.983775)
    field.add_grid(Vector((1181, 988)), 1500, 35, -1.283775)
    field.add_radial(Vector((800, 888)), 750, 55)

    # Generate all streamlines.
    t0 = time()
    generator.create_all_streamlines()
    print(f"done generating in {time() - t0:.2f}s")

    # Generate graph from generated streamlines.
    t0 = time()
    graph = Graph(generator)
    print(f"generated graph in {time() - t0:.2f}s")

    # Visualize graph in Blender
    t0 = time()
    place_graph(graph)
    place_nodes(graph)
    print(f"placed graph in {time() - t0:.2f}s")

    # Visualize simple and complex streamlines in Blender
    place_stuff(generator, simple=True, offset=Vector((1500., 0.0)), id="grid_simple")
    place_stuff(generator, simple=False, offset=Vector((3000., 0.0)), id="grid_complex")


# Helper method to place cubes at node points of the generated graph.
def place_nodes(graph: Graph):
    try:
        nodes = bpy.data.collections["nodes"]
        bpy.ops.object.select_all(action='DESELECT')
        for obj in nodes.objects:
            obj.select_set(True)
        bpy.ops.object.delete()
    except Exception:
        nodes = bpy.data.collections.new("nodes")
        bpy.context.scene.collection.children.link(nodes)

    cube_mesh = bpy.data.meshes.new('Basic_Cube')
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.5)
    bm.to_mesh(cube_mesh)
    bm.free()
    for node in graph.nodes:
        n = bpy.data.objects.new("Node", cube_mesh)
        nodes.objects.link(n)
        n.location = node.co.to_3d()


# Helper method to turn streamline sections of the graph into curves to visualize in Blender.
def place_graph(graph: Graph):
    try:
        grid = bpy.data.collections["grid"]
        bpy.ops.object.select_all(action='DESELECT')
        for child in grid.children:
            for obj in child.objects:
                obj.select_set(True)
        for obj in grid.objects:
            obj.select_set(True)
        bpy.ops.object.delete()
        for child in grid.children:
            bpy.data.collections.remove(child)
    except Exception:
        grid = bpy.data.collections.new("grid")
        bpy.context.scene.collection.children.link(grid)

    for streamline in graph.streamline_sections:
        sl = bpy.data.collections.new("streamline")
        grid.children.link(sl)
        for section in streamline:
            curve = bpy.data.curves.new("section", 'CURVE')
            curve.splines.new('BEZIER')
            curve.splines.active.bezier_points.add(len(section) - 1)
            obj = bpy.data.objects.new("section", curve)
            sl.objects.link(obj)
            for i in range(len(section)):
                curve.splines.active.bezier_points[i].co = section[i].to_3d()
                curve.splines.active.bezier_points[i].handle_right_type = 'VECTOR'
                curve.splines.active.bezier_points[i].handle_left_type = 'VECTOR'


# Helper method to place single vertices at all streamline points.
# Can visualize either simple or complex streamlines, with optional offset for placement.
# Deletes previously placed objects, it is faster to simply restart Blender, however.
def place_stuff(generator: StreamlineGenerator, simple=False, offset=Vector((0.0, 0.0)), id="grid"):
    t0 = time()
    streamlines = generator.all_streamlines_simple if simple else generator.all_streamlines

    try:
        col = bpy.data.collections[id]
        bpy.ops.object.select_all(action='DESELECT')
        for child in col.children:
            for obj in child.objects:
                obj.select_set(True)
        for obj in col.objects:
            obj.select_set(True)
        bpy.ops.object.delete()
        for child in col.children:
            bpy.data.collections.remove(child)
    except Exception:
        col = bpy.data.collections.new(id)
        bpy.context.scene.collection.children.link(col)

    for i in range(len(streamlines)):
        c = bpy.data.collections.new(id + "_streamline_" + str(i + 1))
        col.children.link(c)
    vertices = [(0, 0, 0)]
    edges = []
    faces = []
    mesh = bpy.data.meshes.new("streamline_coord_obj")
    mesh.from_pydata(vertices, edges, faces)
    mesh.update()
    count = 1
    for streamline in streamlines:
        col = bpy.data.collections[id + "_streamline_" + str(count)]
        for point in streamline:
            object_name = id + "_streamline_" + str(count) + "_marker"
            new_object = bpy.data.objects.new(object_name, mesh)
            new_object.location = (point + offset).to_3d()
            col.objects.link(new_object)
        count += 1

    print(f"done placing in {time() - t0:2f}s")


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == '__main__':
    main()
