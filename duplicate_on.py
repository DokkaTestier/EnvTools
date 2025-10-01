import bpy
import random
import math
import mathutils

class OBJECT_OT_DuplicateOnFaces(bpy.types.Operator):
    bl_idname = "object.duplicate_on_faces"
    bl_label = "Duplicate on Faces"
    bl_description = "Duplicate the active object on the faces of the target with random scale and rotation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        active = context.active_object
        targets = [obj for obj in context.selected_objects if obj != active]

        if not targets:
            self.report({'WARNING'}, "No target object selected")
            return {'CANCELLED'}

        scene = context.scene
        scale_min = scene.face_scale_min
        scale_max = scene.face_scale_max
        rot_min = scene.face_rot_min
        rot_max = scene.face_rot_max
        keep_origin = scene.duplicate_keep_origin
        random_selection = scene.duplicate_random_selection
        random_range = scene.duplicate_random_range

        rot_x = scene.rot_axis_x
        rot_y = scene.rot_axis_y
        rot_z = scene.rot_axis_z

        for target in targets:
            if not target.type == 'MESH':
                continue
            mesh = target.data
            for face in mesh.polygons:

                # Apply random face selection probability
                if random_selection:
                    if random.random() > (random_range / 100.0):
                        continue  # Skip this face

                new_obj = active.copy()
                new_obj.location = target.matrix_world @ face.center

                # Orientation base
                if not keep_origin:
                    new_obj.rotation_euler = face.normal.to_track_quat('Z', 'Y').to_euler()
                else:
                    new_obj.rotation_euler = active.rotation_euler.copy()

                # Random uniform scale
                random_scale = random.uniform(scale_min, scale_max)
                new_obj.scale *= random_scale

                # Random rotation on selected axes
                if rot_min > 0.0 or rot_max > 0.0:
                    rand_rot = [0.0, 0.0, 0.0]

                    if rot_x:
                        rand_rot[0] = math.radians(random.uniform(rot_min * 360.0, rot_max * 360.0))
                    if rot_y:
                        rand_rot[1] = math.radians(random.uniform(rot_min * 360.0, rot_max * 360.0))
                    if rot_z:
                        rand_rot[2] = math.radians(random.uniform(rot_min * 360.0, rot_max * 360.0))

                    new_obj.rotation_euler.rotate(mathutils.Euler(rand_rot))

                context.collection.objects.link(new_obj)

        return {'FINISHED'}


class VIEW3D_PT_DuplicateOnFacesPanel(bpy.types.Panel):
    bl_label = "Duplicate On"
    bl_idname = "VIEW3D_PT_duplicate_on"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "EnvTools"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.operator("object.duplicate_on_faces", text="Duplicate on Faces", icon='MOD_PARTICLES')
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

        row = layout.row(align=True)
        row.prop(scene, "rot_axis_x")
        row.prop(scene, "rot_axis_y")
        row.prop(scene, "rot_axis_z")
