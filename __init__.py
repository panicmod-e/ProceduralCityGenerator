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

    t0 = time()

    field = TensorField()

    parameters = StreamlineParameters(
        dsep=100,
        dtest=30,
        dstep=1,
        dcirclejoin=5,
        dlookahead=200,
        joinangle=0.1,
        path_iterations=50,
        seed_tries=25,
        simplify_tolerance=0.5,
        collide_early=0
    )

    integrator = RK4Integrator(
        field,
        parameters
    )

    generator = StreamlineGenerator(
        integrator,
        Vector((519, 249)),
        Vector((1452, 1279)),
        parameters
    )

    print("world - dim", generator.world_dimensions)
    print("grid - dim", generator.major_grid.grid_dimensions)

    # field.add_radial(Vector((836, 846)), 268, 46)
    field.add_grid(Vector((776, 387)), 1371, 15, 1.483775)
    # field.add_radial(Vector((25, 25)), 5, 5)
    # field.add_radial(Vector((25, 80)), size, decay)

    generator.create_all_streamlines()

    place_stuff(generator)
    print(f"done {time() - t0:.2f}s")


def place_stuff(generator: StreamlineGenerator):
    try:
        col = bpy.data.collections["grid"]
        bpy.ops.object.select_all(action='DESELECT')
        for obj in col.objects:
            obj.select_set(True)
        bpy.ops.object.delete()
    except Exception:
        col = bpy.data.collections.new("grid")
        bpy.context.scene.collection.children.link(col)

    vertices = [(0, 0, 0)]
    edges = []
    faces = []
    mesh = bpy.data.meshes.new("streamline_coord_obj")
    mesh.from_pydata(vertices, edges, faces)
    mesh.update()
    count = 0
    for streamline in generator.all_streamlines:
        for point in streamline:
            object_name = "streamline_marker_" + str(count)
            new_object = bpy.data.objects.new(object_name, mesh)
            new_object.location = point.to_3d()
            col.objects.link(new_object)


def register():
    for cls in classes:
        print(cls)
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == '__main__':
    main()
