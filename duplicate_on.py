import bpy
import random
import math
import mathutils

# =========================
# Shared duplication logic
# =========================
def duplicate_on_geometry(context, mode="FACES"):
    active = context.active_object
    targets = [obj for obj in context.selected_objects if obj != active]

    if not active:
        return {'CANCELLED'}

    if not targets:
        return {'CANCELLED'}

    scene = context.scene
    scale_min = scene.face_scale_min
    scale_max = scene.face_scale_max
    rot_min = scene.face_rot_min
    rot_max = scene.face_rot_max
    keep_origin = scene.duplicate_keep_origin
    random_selection = scene.duplicate_random_selection
    random_range = scene.duplicate_random_range

    # 📌 Create a new collection for this batch
    base_name = "Duplicates"
    new_coll_name = base_name
    i = 1
    while new_coll_name in bpy.data.collections:
        new_coll_name = f"{base_name}_{i:03d}"
        i += 1
    new_collection = bpy.data.collections.new(new_coll_name)
    context.scene.collection.children.link(new_collection)

    for target in targets:
        if not target.type == 'MESH':
            continue
        mesh = target.data

        if mode == "FACES":
            elements = mesh.polygons
        elif mode == "VERTICES":
            elements = mesh.vertices
        else:
            continue

        for elem in elements:

            # Random selection (skip some faces/verts)
            if random_selection and random.random() > (random_range / 100.0):
                continue

            new_obj = active.copy()

            if mode == "FACES":
                new_obj.location = target.matrix_world @ elem.center
                if not keep_origin:
                    new_obj.rotation_euler = elem.normal.to_track_quat('Z', 'Y').to_euler()
                else:
                    new_obj.rotation_euler = active.rotation_euler.copy()

            elif mode == "VERTICES":
                new_obj.location = target.matrix_world @ elem.co
                if not keep_origin:
                    if hasattr(elem, "normal"):
                        new_obj.rotation_euler = elem.normal.to_track_quat('Z', 'Y').to_euler()
                    else:
                        new_obj.rotation_euler = active.rotation_euler.copy()
                else:
                    new_obj.rotation_euler = active.rotation_euler.copy()

            # Random scale (uniform)
            random_scale = random.uniform(scale_min, scale_max)
            new_obj.scale *= random_scale

            # Random rotation (applied to ALL axes)
            if rot_min > 0.0 or rot_max > 0.0:
                rand_rot = mathutils.Euler((
                    math.radians(random.uniform(rot_min * 360.0, rot_max * 360.0)),
                    math.radians(random.uniform(rot_min * 360.0, rot_max * 360.0)),
                    math.radians(random.uniform(rot_min * 360.0, rot_max * 360.0))
                ))
                new_obj.rotation_euler.rotate(rand_rot)

            new_collection.objects.link(new_obj)

    return {'FINISHED'}


# =========================
# Duplicate on Faces
# =========================
class OBJECT_OT_DuplicateOnFaces(bpy.types.Operator):
    bl_idname = "object.duplicate_on_faces"
    bl_label = "Duplicate on Faces"
    bl_description = "Duplicate the active object on the faces of the target with random scale and rotation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return duplicate_on_geometry(context, mode="FACES")


# =========================
# Duplicate on Vertices
# =========================
class OBJECT_OT_DuplicateOnVertices(bpy.types.Operator):
    bl_idname = "object.duplicate_on_vertices"
    bl_label = "Duplicate on Vertices"
    bl_description = "Duplicate the active object on the vertices of the target with random scale and rotation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return duplicate_on_geometry(context, mode="VERTICES")


# =========================
# UI Panel
# =========================
class VIEW3D_PT_DuplicateOnPanel(bpy.types.Panel):
    bl_label = "Duplicate On"
    bl_idname = "VIEW3D_PT_duplicate_on"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "EnvTools"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.operator("object.duplicate_on_faces", text="Duplicate on Faces", icon='MOD_PARTICLES')
        layout.operator("object.duplicate_on_vertices", text="Duplicate on Vertices", icon='VERTEXSEL')
        layout.separator()

        layout.prop(scene, "duplicate_keep_origin")

        layout.prop(scene, "duplicate_random_selection")
        if scene.duplicate_random_selection:
            layout.prop(scene, "duplicate_random_range")

        layout.label(text="Random Scale:")
        layout.prop(scene, "face_scale_min")
        layout.prop(scene, "face_scale_max")

        layout.label(text="Random Rotation (0–1 = 0–360°):")
        layout.prop(scene, "face_rot_min")
        layout.prop(scene, "face_rot_max")
