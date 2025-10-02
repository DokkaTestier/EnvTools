import bpy

class VIEW3D_PT_UtilityPanel(bpy.types.Panel):
    bl_label = "Utility"
    bl_idname = "VIEW3D_PT_utility"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "EnvTools"

    def draw(self, context):
        layout = self.layout
        overlays = context.space_data.overlay  # For Face Orientation toggle

        # === First Row ===
        row = layout.row(align=True)
        col1 = row.column()
        col2 = row.column()

        col1.operator("view3d.snap_cursor_to_selected", text="Cursor to Selected", icon='PIVOT_CURSOR')
        col2.operator("object.origin_set", text="Origin to 3D Cursor", icon='OBJECT_ORIGIN').type = 'ORIGIN_CURSOR'

        # === Second Row ===
        row2 = layout.row(align=True)
        col1b = row2.column()
        col2b = row2.column()

        col1b.operator("mesh.quads_convert_to_tris", text="Triangulate Faces", icon='MOD_TRIANGULATE')
        col2b.operator("mesh.tris_convert_to_quads", text="Tris to Quads", icon='MESH_GRID')

        # === Third Row ===
        row3 = layout.row(align=True)
        col1c = row3.column()
        col2c = row3.column()

        col1c.prop(overlays, "show_face_orientation", text="Face Orientation")
        col2c.operator("mesh.flip_normals", text="Flip Normals", icon='NORMALS_FACE')

        # === Fourth Row ===
        row4 = layout.row(align=True)
        col1d = row4.column()
        col2d = row4.column()

        col1d.operator("mesh.set_edge_flow", text="Set Flow", icon='IPO_SINE')
        col2d.operator("mesh.loop_multi_select", text="Edge Ring", icon='EDGESEL').ring = True

        # === Fifth Row ===
        row5 = layout.row(align=True)
        col1e = row5.column()
        col2e = row5.column()

        # Select Boundary
        col1e.operator("mesh.region_to_loop", text="Select Boundary", icon='BORDER_RECTFILL')

        # Deselect Boundary (select then deselect)
        op = col2e.operator("mesh.region_to_loop", text="Deselect Boundary", icon='X')
        op.extend = False
        op.deselect = True
