import bpy
import bmesh

# =========================
# Smart Deselect Boundary
# =========================
class MESH_OT_deselect_boundary(bpy.types.Operator):
    bl_idname = "mesh.deselect_boundary"
    bl_label = "Deselect Boundary"
    bl_description = "Select boundary loop for the current region, then deselect only the boundary"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "Active object must be a mesh")
            return {'CANCELLED'}
        if obj.mode != 'EDIT':
            self.report({'WARNING'}, "Operator requires Edit Mode")
            return {'CANCELLED'}

        bm = bmesh.from_edit_mesh(obj.data)
        any_sel = (
            any(v.select for v in bm.verts) or
            any(e.select for e in bm.edges) or
            any(f.select for f in bm.faces)
        )
        if not any_sel:
            self.report({'INFO'}, "Nothing selected — nothing to do")
            return {'CANCELLED'}

        tool_settings = context.tool_settings
        prev_mode = tuple(tool_settings.mesh_select_mode)
        try:
            tool_settings.mesh_select_mode = (False, True, False)
        except Exception:
            pass

        bm.edges.ensure_lookup_table()
        prev_selected_edges = {e.index for e in bm.edges if e.select}

        bpy.ops.mesh.region_to_loop()

        bm = bmesh.from_edit_mesh(obj.data)
        bm.edges.ensure_lookup_table()
        for e in bm.edges:
            if e.select and e.index not in prev_selected_edges:
                e.select = False

        bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)

        try:
            tool_settings.mesh_select_mode = prev_mode
        except Exception:
            pass

        return {'FINISHED'}


# =========================
# Apply All Transforms
# =========================
class OBJECT_OT_apply_all_transform(bpy.types.Operator):
    bl_idname = "object.apply_all_transform"
    bl_label = "Apply - All Transform"
    bl_description = "Apply Location, Rotation and Scale to all selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        sel = list(context.selected_objects)
        if not sel:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}

        prev_mode   = context.mode
        prev_active = context.view_layer.objects.active

        try:
            if prev_mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
        except Exception:
            pass

        for obj in sel:
            try:
                context.view_layer.objects.active = obj
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            except Exception as e:
                self.report({'WARNING'}, f"Couldn't apply transforms on {obj.name}: {e}")

        try:
            context.view_layer.objects.active = prev_active
            if prev_mode != 'OBJECT' and prev_active is not None:
                if prev_mode.startswith('EDIT'):
                    bpy.ops.object.mode_set(mode='EDIT')
        except Exception:
            pass

        return {'FINISHED'}


# =========================
# Apply All Modifiers
# =========================
class OBJECT_OT_apply_all_modifiers(bpy.types.Operator):
    bl_idname = "object.apply_all_modifiers"
    bl_label = "Apply All Modifiers"
    bl_description = "Apply all modifiers on selected mesh objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        sel = [o for o in context.selected_objects if o.type == 'MESH']
        if not sel:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}

        prev_mode   = context.mode
        prev_active = context.view_layer.objects.active

        try:
            if prev_mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
        except Exception:
            pass

        for obj in sel:
            context.view_layer.objects.active = obj
            for mod in list(obj.modifiers):
                try:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                except Exception as e:
                    self.report({'WARNING'}, f"Failed to apply {mod.name} on {obj.name}: {e}")

        try:
            context.view_layer.objects.active = prev_active
            if prev_mode != 'OBJECT' and prev_active is not None:
                if prev_mode.startswith('EDIT'):
                    bpy.ops.object.mode_set(mode='EDIT')
        except Exception:
            pass

        return {'FINISHED'}


# =========================
# Transformation Orientation shortcuts
# =========================
class VIEW3D_OT_set_orientation_global(bpy.types.Operator):
    bl_idname = "view3d.set_orientation_global"
    bl_label = "Global"
    bl_description = "Set Transformation Orientation to Global"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.transform_orientation_slots[0].type = 'GLOBAL'
        return {'FINISHED'}


class VIEW3D_OT_set_orientation_normal(bpy.types.Operator):
    bl_idname = "view3d.set_orientation_normal"
    bl_label = "Normal"
    bl_description = "Set Transformation Orientation to Normal"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.transform_orientation_slots[0].type = 'NORMAL'
        return {'FINISHED'}


class VIEW3D_OT_set_orientation_view(bpy.types.Operator):
    bl_idname = "view3d.set_orientation_view"
    bl_label = "View"
    bl_description = "Set Transformation Orientation to View"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.transform_orientation_slots[0].type = 'VIEW'
        return {'FINISHED'}


# -----------------------
# Merge Overlap
# Uses REGISTER so Blender shows the redo panel (F9 / bottom-left)
# where the user can tweak threshold, unselected and sharp edges.
# -----------------------
class OBJECT_OT_merge_overlap(bpy.types.Operator):
    bl_idname = "object.merge_overlap"
    bl_label = "Merge Overlap"
    bl_description = (
        "Select all vertices and run Merge by Distance. "
        "Adjust threshold, Unselected and Sharp Edges in the redo panel (F9)"
    )
    bl_options = {'REGISTER', 'UNDO'}

    # Expose the same parameters as mesh.remove_doubles so they appear
    # in the redo panel and can be tweaked interactively.
    threshold: bpy.props.FloatProperty(
        name="Merge Distance",
        description="Maximum distance between vertices to merge",
        default=0.0001,
        min=0.0,
        max=10.0,
        precision=4,
        unit='LENGTH',
    )
    use_unselected: bpy.props.BoolProperty(
        name="Unselected",
        description="Merge selected vertices with unselected ones",
        default=False,
    )
    use_sharp_edge_from_normals: bpy.props.BoolProperty(
        name="Sharp Edges",
        description="Calculate sharp edges using custom normal data",
        default=False,
    )

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "Active object must be a mesh")
            return {'CANCELLED'}

        was_in_object_mode = (context.mode != 'EDIT_MESH')

        if was_in_object_mode:
            bpy.ops.object.mode_set(mode='EDIT')

        # Select all vertices
        bpy.ops.mesh.select_all(action='SELECT')

        # Merge by distance with user-controllable parameters
        bpy.ops.mesh.remove_doubles(
            threshold=self.threshold,
            use_unselected=self.use_unselected,
            use_sharp_edge_from_normals=self.use_sharp_edge_from_normals,
        )

        if was_in_object_mode:
            bpy.ops.object.mode_set(mode='OBJECT')

        return {'FINISHED'}

    def invoke(self, context, event):
        # Run immediately; redo panel appears automatically thanks to REGISTER
        return self.execute(context)


# =========================
# Utility Panel
# =========================
class VIEW3D_PT_UtilityPanel(bpy.types.Panel):
    bl_label = "Utility"
    bl_idname = "VIEW3D_PT_utility"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "EnvTools"

    def draw(self, context):
        layout  = self.layout
        overlays = context.space_data.overlay

        row = layout.row(align=True)
        row.operator("view3d.snap_cursor_to_selected", text="Cursor to Selected",  icon='PIVOT_CURSOR')
        row.operator("object.origin_set",              text="Origin to 3D Cursor", icon='OBJECT_ORIGIN').type = 'ORIGIN_CURSOR'

        row2 = layout.row(align=True)
        row2.operator("mesh.quads_convert_to_tris", text="Triangulate Faces", icon='MOD_TRIANGULATE')
        row2.operator("mesh.tris_convert_to_quads",  text="Tris to Quads",    icon='MESH_GRID')

        row3 = layout.row(align=True)
        row3.prop(overlays, "show_face_orientation", text="Face Orientation")
        row3.operator("mesh.flip_normals", text="Flip Normals", icon='NORMALS_FACE')

        row4 = layout.row(align=True)
        row4.operator("mesh.set_edge_flow",      text="Set Flow",  icon='IPO_SINE')
        row4.operator("mesh.loop_multi_select",  text="Edge Ring", icon='EDGESEL').ring = True

        row5 = layout.row(align=True)
        row5.operator("mesh.region_to_loop",    text="Select Boundary",   icon='OUTLINER_OB_MESH')
        row5.operator("mesh.deselect_boundary", text="Deselect Boundary", icon='X')

        row6 = layout.row(align=True)
        row6.operator("mesh.mark_seam", text="Mark Seam",  icon='UV')
        row6.operator("mesh.mark_seam", text="Clear Seam", icon='X').clear = True

        row7 = layout.row(align=True)
        row7.operator("mesh.mark_sharp", text="Mark Sharp",  icon='SHARPCURVE')
        row7.operator("mesh.mark_sharp", text="Clear Sharp", icon='X').clear = True

        row8 = layout.row(align=True)
        row8.operator("object.shade_smooth", text="Shade Smooth", icon='SHADING_RENDERED')
        row8.operator("object.shade_flat",   text="Shade Flat",   icon='SHADING_SOLID')

        row9 = layout.row(align=True)
        row9.operator("object.randomize_transform", text="Randomize Transform",     icon='MOD_ARRAY')
        row9.operator("object.make_links_data",     text="Copy Modifier to Selected", icon='MODIFIER').type = 'MODIFIERS'

        row10 = layout.row(align=True)
        row10.operator("object.apply_all_transform",  text="Apply - All Transform", icon='FILE_TICK')
        row10.operator("object.apply_all_modifiers",  text="Apply All Modifiers",   icon='MODIFIER')

        # --- Transform Orientation ---
        layout.separator()
        layout.label(text="Transform Orientation:")
        row11 = layout.row(align=True)
        row11.operator("view3d.set_orientation_global", text="Global", icon='ORIENTATION_GLOBAL')
        row11.operator("view3d.set_orientation_normal", text="Normal", icon='ORIENTATION_NORMAL')
        row11.operator("view3d.set_orientation_view",   text="View",   icon='ORIENTATION_VIEW')

        # --- Merge Overlap ---
        layout.separator()
        layout.operator("object.merge_overlap", text="Merge Overlap", icon='AUTOMERGE_ON')
