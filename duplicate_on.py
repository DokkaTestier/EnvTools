import bpy
import random
import mathutils

class OBJECT_OT_DuplicateOnFaces(bpy.types.Operator):
    bl_idname = "object.duplicate_on_faces"
    bl_label = "Duplicar en Caras"
    bl_description = "Duplica el objeto activo sobre las caras del objeto objetivo"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        active = context.active_object
        targets = [obj for obj in context.selected_objects if obj != active]

        if not targets:
            self.report({'WARNING'}, "No hay objeto objetivo seleccionado")
            return {'CANCELLED'}

        for target in targets:
            if not target.type == 'MESH':
                continue
            mesh = target.data
            for face in mesh.polygons:
                new_obj = active.copy()
                new_obj.location = target.matrix_world @ face.center
                new_obj.rotation_euler = face.normal.to_track_quat('Z', 'Y').to_euler()
                context.collection.objects.link(new_obj)

        return {'FINISHED'}


class VIEW3D_PT_DuplicateOnFacesPanel(bpy.types.Panel):
    bl_label = "Duplicar en Caras"
    bl_idname = "VIEW3D_PT_duplicate_on_faces"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "EnvTools"

    def draw(self, context):
        layout = self.layout
        layout.operator("object.duplicate_on_faces", icon='MOD_PARTICLES')
