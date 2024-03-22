import bpy
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


class GridGenBasePanel():
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "grid gen"


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
    # rng = np.random.default_rng()
    # theta = rng.random() * (2 * math.pi)
    # size = 100
    # decay = 20

    print("-- starting generation --")

    field = TensorField()

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

    integrator = RK4Integrator(
        field,
        parameters
    )

    generator = StreamlineGenerator(
        integrator=integrator,
        origin=Vector((519, 249)),
        world_dimensions=Vector((1452, 1279)),
        parameters=parameters,
    )
    field.add_grid(Vector((1381, 788)), 1500, 35, 1.983775)
    field.add_grid(Vector((1181, 988)), 1500, 35, -1.283775)
    field.add_radial(Vector((800, 888)), 750, 55)

    # generator = StreamlineGenerator(
    #     integrator=integrator,
    #     origin=Vector((100.0, 100.0)),
    #     world_dimensions=Vector((500, 500)),
    #     parameters=parameters
    # )
    # field.add_grid(Vector((300, 300)), 500, 35, 1.432)

    t0 = time()
    generator.create_all_streamlines()
    print(f"done generating in {time() - t0:.2f}s")

    t0 = time()
    graph = Graph(generator)
    print(f"generated graph in {time() - t0:.2f}s")
    t0 = time()
    place_graph(graph)
    print(f"placed graph in {time() - t0:.2f}s")

    place_stuff(generator, simple=True, offset=Vector((1500., 0.0)), id="grid_simple")
    # place_stuff(generator, simple=False)


def place_graph(graph: Graph):
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


def place_stuff(generator: StreamlineGenerator, simple=False, offset=Vector((0.0, 0.0)), id="grid"):
    t0 = time()
    streamlines = generator.all_streamlines_simple if simple else generator.all_streamlines

    try:
        col = bpy.data.collections[id]
        bpy.ops.object.select_all(action='DESELECT')
        for child in col.children:
            for obj in child.objects:
                obj.select_set(True)
            bpy.ops.object.delete()
            bpy.data.collections.remove(child)
        for obj in col.objects:
            obj.select_set(True)
        bpy.ops.object.delete()
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
