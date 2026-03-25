import bpy
import random
import colorsys
import bmesh


# =========================
# Helpers
# =========================

def _get_active_mat_index(obj):
    return obj.active_material_index


def _unique_color():
    """
    Generate a vivid, visually distinct random RGB color (HSV-based).
    Saturation and value are kept high so ID colors are easy to tell apart.
    """
    h = random.random()
    s = random.uniform(0.6, 1.0)
    v = random.uniform(0.6, 1.0)
    return colorsys.hsv_to_rgb(h, s, v)


def _find_existing_id_material(r, g, b, tolerance=0.01):
    """
    Return an existing ID material whose base color is within `tolerance`
    of (r, g, b), or None if none found.
    """
    for mat in bpy.data.materials:
        if not mat.name.startswith("ID_"):
            continue
        if mat.use_nodes:
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            if bsdf is None:
                continue
            mc = bsdf.inputs["Base Color"].default_value
            if (abs(mc[0] - r) < tolerance and
                    abs(mc[1] - g) < tolerance and
                    abs(mc[2] - b) < tolerance):
                return mat
        else:
            mc = mat.diffuse_color
            if (abs(mc[0] - r) < tolerance and
                    abs(mc[1] - g) < tolerance and
                    abs(mc[2] - b) < tolerance):
                return mat
    return None


def _next_id_name():
    """Return the next available ID_### name."""
    existing = {mat.name for mat in bpy.data.materials if mat.name.startswith("ID_")}
    i = 1
    while True:
        name = f"ID_{i:03d}"
        if name not in existing:
            return name
        i += 1


def _make_id_material(r, g, b):
    """Create a new flat-shaded ID material with the given RGB color."""
    mat = bpy.data.materials.new(name=_next_id_name())
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (300, 0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)
    bsdf.inputs["Roughness"].default_value = 1.0
    # "Specular" was renamed to "Specular IOR Level" in Blender 4.x
    specular_key = (
        "Specular IOR Level"
        if "Specular IOR Level" in bsdf.inputs
        else "Specular"
    )
    bsdf.inputs[specular_key].default_value = 0.0

    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    # Also set viewport color so it's visible in Material Preview / Solid
    mat.diffuse_color = (r, g, b, 1.0)

    return mat


def _get_or_create_id_material():
    """
    Return an existing ID material if one with the same color already exists,
    otherwise create a brand-new one with a unique vivid color.
    Colors already used in the current call are tracked via the caller.
    """
    max_tries = 64
    for _ in range(max_tries):
        r, g, b = _unique_color()
        existing = _find_existing_id_material(r, g, b)
        if existing:
            return existing
        return _make_id_material(r, g, b)
    return _make_id_material(*_unique_color())


# =========================
# Operators
# =========================

class OBJECT_OT_id_add_slot(bpy.types.Operator):
    bl_idname = "object.id_add_slot"
    bl_label = "Add Material Slot"
    bl_description = "Add a new material slot to the active object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.material_slot_add()
        return {'FINISHED'}


class OBJECT_OT_id_remove_slot(bpy.types.Operator):
    bl_idname = "object.id_remove_slot"
    bl_label = "Remove Material Slot"
    bl_description = "Remove the active material slot from the active object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.material_slot_remove()
        return {'FINISHED'}


class OBJECT_OT_id_slot_move_up(bpy.types.Operator):
    bl_idname = "object.id_slot_move_up"
    bl_label = "Move Slot Up"
    bl_description = "Move the active material slot up"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.material_slot_move(direction='UP')
        return {'FINISHED'}


class OBJECT_OT_id_slot_move_down(bpy.types.Operator):
    bl_idname = "object.id_slot_move_down"
    bl_label = "Move Slot Down"
    bl_description = "Move the active material slot down"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.material_slot_move(direction='DOWN')
        return {'FINISHED'}


class OBJECT_OT_id_assign(bpy.types.Operator):
    bl_idname = "object.id_assign"
    bl_label = "Assign"
    bl_description = "Assign the active material to the selected faces (Edit Mode only)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        bpy.ops.object.material_slot_assign()
        return {'FINISHED'}


class OBJECT_OT_id_select(bpy.types.Operator):
    bl_idname = "object.id_select"
    bl_label = "Select"
    bl_description = "Select faces assigned to the active material slot (Edit Mode only)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        bpy.ops.object.material_slot_select()
        return {'FINISHED'}


class OBJECT_OT_id_deselect(bpy.types.Operator):
    bl_idname = "object.id_deselect"
    bl_label = "Deselect"
    bl_description = "Deselect faces assigned to the active material slot (Edit Mode only)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        bpy.ops.object.material_slot_deselect()
        return {'FINISHED'}


class OBJECT_OT_id_select_by_material(bpy.types.Operator):
    bl_idname = "object.id_select_by_material"
    bl_label = "Select by Material"
    bl_description = (
        "Select all objects in the scene that share the same material "
        "as the active material slot (Object Mode only)"
    )
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (
            context.mode == 'OBJECT' and
            obj is not None and
            len(obj.material_slots) > 0
        )

    def execute(self, context):
        obj = context.active_object
        if obj.active_material_index >= len(obj.material_slots):
            self.report({'WARNING'}, "No active material slot")
            return {'CANCELLED'}

        target_mat = obj.material_slots[obj.active_material_index].material
        if target_mat is None:
            self.report({'WARNING'}, "Active material slot is empty")
            return {'CANCELLED'}

        count = 0
        for o in context.view_layer.objects:
            if o.type != 'MESH':
                continue
            for slot in o.material_slots:
                if slot.material == target_mat:
                    o.select_set(True)
                    count += 1
                    break

        self.report({'INFO'}, f"{count} object(s) selected with material '{target_mat.name}'")
        return {'FINISHED'}


# =========================
# Generate ID
# =========================

class OBJECT_OT_generate_id(bpy.types.Operator):
    bl_idname = "object.generate_id"
    bl_label = "Generate ID"
    bl_description = (
        "Object Mode: assign one random ID material per selected object.\n"
        "Edit Mode: use Select Linked to identify sub-meshes inside the active "
        "object and assign one ID material per linked island."
    )
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mode = context.mode

        if mode == 'OBJECT':
            self._generate_object_mode(context)
        elif mode == 'EDIT_MESH':
            self._generate_edit_mode(context)
        else:
            self.report({'WARNING'}, "Use this in Object Mode or Edit Mode (Mesh)")
            return {'CANCELLED'}

        return {'FINISHED'}

    # ----------------------------------------------------------
    # Object mode: one material per selected object
    # ----------------------------------------------------------
    def _generate_object_mode(self, context):
        targets = [o for o in context.selected_objects if o.type == 'MESH']
        if not targets:
            self.report({'WARNING'}, "No mesh objects selected")
            return

        used_colors = []   # track (r,g,b) already assigned this run

        for obj in targets:
            mat = self._unique_mat(used_colors)
            r, g, b = mat.diffuse_color[:3]
            used_colors.append((r, g, b))

            # Clear all existing slots and assign the single material
            obj.data.materials.clear()
            obj.data.materials.append(mat)

            # Assign to every face
            for poly in obj.data.polygons:
                poly.material_index = 0

        self.report({'INFO'}, f"ID materials assigned to {len(targets)} object(s)")

    # ----------------------------------------------------------
    # Edit mode: one material per linked island
    # ----------------------------------------------------------
    def _generate_edit_mode(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "Active object must be a mesh")
            return

        # We need to work in Object mode to manipulate material slots cleanly,
        # then go back to Edit mode.
        bpy.ops.object.mode_set(mode='OBJECT')

        mesh = obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.faces.ensure_lookup_table()
        bm.verts.ensure_lookup_table()

        # --- Find linked islands via BFS on face adjacency ---
        visited   = set()
        islands   = []

        for start_face in bm.faces:
            if start_face.index in visited:
                continue
            island = set()
            queue  = [start_face]
            while queue:
                f = queue.pop()
                if f.index in visited:
                    continue
                visited.add(f.index)
                island.add(f.index)
                # Expand to faces sharing an edge
                for edge in f.edges:
                    for linked_face in edge.link_faces:
                        if linked_face.index not in visited:
                            queue.append(linked_face)
            islands.append(island)

        bm.free()

        used_colors = []
        # Remove all existing material slots
        obj.data.materials.clear()

        # Assign one material per island
        island_materials = []
        for _ in islands:
            mat = self._unique_mat(used_colors)
            r, g, b = mat.diffuse_color[:3]
            used_colors.append((r, g, b))
            obj.data.materials.append(mat)
            island_materials.append(mat)

        # Set material_index on each face
        for slot_idx, island in enumerate(islands):
            for face_idx in island:
                mesh.polygons[face_idx].material_index = slot_idx

        bpy.ops.object.mode_set(mode='EDIT')
        self.report({'INFO'}, f"{len(islands)} linked island(s) identified and colored")

    # ----------------------------------------------------------
    # Helper: get / create a material with a color not yet used
    # ----------------------------------------------------------
    def _unique_mat(self, used_colors, max_tries=128):
        for _ in range(max_tries):
            r, g, b = _unique_color()

            # Check against colors already assigned this run
            too_close = any(
                abs(r - uc[0]) < 0.15 and
                abs(g - uc[1]) < 0.15 and
                abs(b - uc[2]) < 0.15
                for uc in used_colors
            )
            if too_close:
                continue

            # Reuse an existing ID material with this color if one exists
            existing = _find_existing_id_material(r, g, b)
            if existing:
                return existing

            return _make_id_material(r, g, b)

        # Fallback: just make one even if color is close
        return _make_id_material(*_unique_color())


# =========================================================
# Panel
# =========================================================

class VIEW3D_PT_IDMapPanel(bpy.types.Panel):
    bl_label = "ID Map"
    bl_idname = "VIEW3D_PT_id_map"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "EnvTools"

    def draw(self, context):
        layout = self.layout
        obj    = context.active_object

        if obj is None:
            layout.label(text="No active object", icon='INFO')
            return

        # ── Material slot list + side buttons ──────────────────────────
        row = layout.row()

        # The material index list (same template Blender uses internally)
        row.template_list(
            "MATERIAL_UL_matslots",   # built-in UI list
            "",
            obj,
            "material_slots",
            obj,
            "active_material_index",
        )

        # Side column: add / remove / move
        col = row.column(align=True)
        col.operator("object.id_add_slot",      text="", icon='ADD')
        col.operator("object.id_remove_slot",   text="", icon='REMOVE')
        col.separator()
        col.operator("object.id_slot_move_up",  text="", icon='TRIA_UP')
        col.operator("object.id_slot_move_down",text="", icon='TRIA_DOWN')

        # ── Active material picker ──────────────────────────────────────
        if obj.active_material_index < len(obj.material_slots):
            slot = obj.material_slots[obj.active_material_index]
            row2 = layout.row()
            row2.template_ID(slot, "material", new="material.new")

        # ── Assign / Select / Deselect (Edit Mode only) ───────────────
        layout.separator()
        is_edit = context.mode == 'EDIT_MESH'

        row3 = layout.row(align=True)
        row3.enabled = is_edit
        row3.operator("object.id_assign",   text="Assign")
        row3.operator("object.id_select",   text="Select")
        row3.operator("object.id_deselect", text="Deselect")

        # ── Select by Material (Object Mode only) ──────────────────────
        row4 = layout.row()
        row4.enabled = not is_edit
        row4.operator("object.id_select_by_material", text="Select by Material", icon='MATERIAL')

        # ── Generate ID ────────────────────────────────────────────────
        layout.separator()
        layout.operator("object.generate_id", text="Generate ID", icon='MATERIAL')

        # Hint depending on current mode
        if is_edit:
            layout.label(text="Edit Mode: 1 color per linked island", icon='INFO')
        else:
            layout.label(text="Object Mode: 1 color per object", icon='INFO')
