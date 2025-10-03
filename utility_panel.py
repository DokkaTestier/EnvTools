import bpy
import bmesh

# -----------------------
# Smart Deselect Boundary
# -----------------------
class MESH_OT_deselect_boundary(bpy.types.Operator):
    bl_idname = "mesh.deselect_boundary"
    bl_label = "Deselect Boundary"
    bl_description = "Select boundary loop for the current region, then deselect only the boundary (keeps previous selection)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "Active object must be a mesh")
            return {'CANCELLED'}

        # Must be in Edit Mode
        if obj.mode != 'EDIT':
            self.report({'WARNING'}, "Operator requires Edit Mode")
            return {'CANCELLED'}

        # Access bmesh and check there is something selected
        bm = bmesh.from_edit_mesh(obj.data)
        any_sel = any(v.select for v in bm.verts) or any(e.select for e in bm.edges) or any(f.select for f in bm.faces)
        if not any_sel:
            self.report({'INFO'}, "Nothing selected — nothing to do")
            return {'CANCELLED'}

        # Save current mesh select mode and set to edge select
        tool_settings = context.tool_settings
        prev_mode = tuple(tool_settings.mesh_select_mode)
        try:
            tool_settings.mesh_select_mode = (False, True, False)
        except Exception:
            # ignore if cannot set (very old/new api)
            pass

        # Save previously selected edges indices
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        prev_selected_edges = {e.index for e in bm.edges if e.select}

        # Run region_to_loop to select the boundary
        bpy.ops.mesh.region_to_loop()

        # Update bmesh and deselect only the newly selected edges (the boundary)
        bm = bmesh.from_edit_mesh(obj.data)
        bm.edges.ensure_lookup_table()
        for e in bm.edges:
            if e.select and e.index not in prev_selected_edges:
                e.select = False

        bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)

        # Restore previous mesh select mode
        try:
            tool_settings.mesh_select_mode = prev_mode
        except Exception:
            pass

        return {'FINISHED'}


# -----------------------
# Apply All Transforms operator
# -----------------------
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

        prev_mode = context.mode
        prev_active = context.view_layer.objects.active

        # Ensure we're in OBJECT mode
        try:
            if prev_mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
        except Exception:
            pass

        for obj in sel:
            # Make object active and apply transforms
            try:
                context.view_layer.objects.active = obj
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            except Exception as e:
                self.report({'WARNING'}, f"Couldn't apply transforms on {obj.name}: {str(e)}")

        # Restore previous active and mode
        try:
            context.view_layer.objects.active = prev_active
            if prev_mode != 'OBJECT' and prev_active is not None:
                # restore edit mode if it was in edit mode before
                if prev_mode.startswith('EDIT'):
                    bpy.ops.object.mode_set(mode='EDIT')
        except Exception:
            pass

        return {'FINISHED'}


# -----------------------
# Apply All Modifiers operator
# -----------------------
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

        prev_mode = context.mode
        prev_active = context.view_layer.objects.active

        # Ensure OBJECT mode
        try:
            if prev_mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
        except Exception:
            pass

        for obj in sel:
            context.view_layer.objects.active = obj
            # Make a copy of list because applying modifies it
            mods = list(obj.modifiers)
            for mod in mods:
                try:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                except Exception as e:
                    # Continue on failure but inform user
                    self.report({'WARNING'}, f"Failed to apply {mod.name} on {obj.name}: {e}")

        # Restore previous active and mode
        try:
            context.view_layer.objects.active = prev_active
            if prev_mode != 'OBJECT' and prev_active is not None:
                if prev_mode.startswith('EDIT'):
                    bpy.ops.object.mode_set(mode='EDIT')
        except Exception:
            pass

        return {'FINISHED'}


# -----------------------
# Utility Panel (all buttons)
# -----------------------
class VIEW3D_PT_UtilityPanel(bpy.types.Panel):
    bl_label = "Utility"
    bl_idname = "VIEW3D_PT_utility"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "EnvTools"

    def draw(self, context):
        layout = self.layout
        overlays = context.space_data.overlay  # For Face Orientation toggle

        # === Row 1 ===
        row = layout.row(align=True)
        col1 = row.column()
        col2 = row.column()
        col1.operator("view3d.snap_cursor_to_selected", text="Cursor to Selected", icon='PIVOT_CURSOR')
        col2.operator("object.origin_set", text="Origin to 3D Cursor", icon='OBJECT_ORIGIN').type = 'ORIGIN_CURSOR'

        # === Row 2 ===
        row2 = layout.row(align=True)
        col1b = row2.column()
        col2b = row2.column()
        col1b.operator("mesh.quads_convert_to_tris", text="Triangulate Faces", icon='MOD_TRIANGULATE')
        col2b.operator("mesh.tris_convert_to_quads", text="Tris to Quads", icon='MESH_GRID')

        # === Row 3 ===
        row3 = layout.row(align=True)
        col1c = row3.column()
        col2c = row3.column()
        col1c.prop(overlays, "show_face_orientation", text="Face Orientation")
        col2c.operator("mesh.flip_normals", text="Flip Normals", icon='NORMALS_FACE')

        # === Row 4 ===
        row4 = layout.row(align=True)
        col1d = row4.column()
        col2d = row4.column()
        col1d.operator("mesh.set_edge_flow", text="Set Flow", icon='IPO_SINE')
        col2d.operator("mesh.loop_multi_select", text="Edge Ring", icon='EDGESEL').ring = True

        # === Row 5 ===
        row5 = layout.row(align=True)
        col1e = row5.column()
        col2e = row5.column()
        col1e.operator("mesh.region_to_loop", text="Select Boundary", icon='OUTLINER_OB_MESH')
        col2e.operator("mesh.deselect_boundary", text="Deselect Boundary", icon='X')

        # === Row 6 ===
        row6 = layout.row(align=True)
        col1f = row6.column()
        col2f = row6.column()
        col1f.operator("mesh.mark_seam", text="Mark Seam", icon='UV')
        col2f.operator("mesh.mark_seam", text="Clear Seam", icon='X').clear = True

        # === Row 7 ===
        row7 = layout.row(align=True)
        col1g = row7.column()
        col2g = row7.column()
        col1g.operator("mesh.mark_sharp", text="Mark Sharp", icon='SHARPCURVE')
        col2g.operator("mesh.mark_sharp", text="Clear Sharp", icon='X').clear = True

        # === Row 8 ===
        row8 = layout.row(align=True)
        col1h = row8.column()
        col2h = row8.column()
        col1h.operator("object.shade_smooth", text="Shade Smooth", icon='SHADING_RENDERED')
        col2h.operator("object.shade_flat", text="Shade Flat", icon='SHADING_SOLID')

        # === Row 9 ===
        row9 = layout.row(align=True)
        col1i = row9.column()
        col2i = row9.column()
        col1i.operator("object.randomize_transform", text="Randomize Transform", icon='MOD_ARRAY')
        col2i.operator("object.make_links_data", text="Copy Modifier to Selected", icon='MODIFIER').type = 'MODIFIERS'

        # === Row 10 (new) ===
        row10 = layout.row(align=True)
        col1j = row10.column()
        col2j = row10.column()
        col1j.operator("object.apply_all_transform", text="Apply - All Transform", icon='FILE_TICK')
        col2j.operator("object.apply_all_modifiers", text="Apply All Modifiers", icon='MODIFIER')
