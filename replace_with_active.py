import bpy

class OBJECT_OT_ReplaceWithActive(bpy.types.Operator):
    bl_idname = "object.replace_with_active"
    bl_label = "Replace with Active"
    bl_description = "Replace selected objects with the active object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        active = context.active_object
        selected = [obj for obj in context.selected_objects if obj != active]

        if not active:
            self.report({'ERROR'}, "No active object")
            return {'CANCELLED'}

        if not selected:
            self.report({'ERROR'}, "No objects selected to replace")
            return {'CANCELLED'}

        # ✅ Apply Scale if enabled
        if context.scene.replace_apply_scale:
            bpy.ops.object.transform_apply(
                location=False, rotation=False, scale=True
            )

        for obj in selected:
            new_obj = active.copy()
            new_obj.location = obj.location
            new_obj.rotation_euler = obj.rotation_euler
            new_obj.scale = obj.scale
            context.collection.objects.link(new_obj)
            bpy.data.objects.remove(obj, do_unlink=True)

        return {'FINISHED'}


class VIEW3D_PT_ReplaceWithActivePanel(bpy.types.Panel):
    bl_label = "Replace with Active"
    bl_idname = "VIEW3D_PT_replace_with_active"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "EnvTools"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.label(text="Replace selected objects with active")
        layout.operator("object.replace_with_active", text="Replace", icon='OBJECT_DATA')
        layout.prop(scene, "replace_apply_scale")
