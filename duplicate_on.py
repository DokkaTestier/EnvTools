import bpy
import random
import math
import mathutils

# =========================
# Helpers
# =========================

def make_collection(base_name, scene):
    """Create a uniquely named collection linked to the scene root."""
    name = base_name
    i = 1
    while name in bpy.data.collections:
        name = f"{base_name}_{i:03d}"
        i += 1
    coll = bpy.data.collections.new(name)
    scene.collection.children.link(coll)
    return coll


def apply_random_transform(obj, scale_min, scale_max, rot_min, rot_max):
    """Apply random uniform scale and random rotation on all axes."""
    rand_scale = random.uniform(scale_min, scale_max)
    obj.scale *= rand_scale

    if rot_min > 0.0 or rot_max > 0.0:
        rand_rot = mathutils.Euler((
            math.radians(random.uniform(rot_min * 360.0, rot_max * 360.0)),
            math.radians(random.uniform(rot_min * 360.0, rot_max * 360.0)),
            math.radians(random.uniform(rot_min * 360.0, rot_max * 360.0))
        ))
        obj.rotation_euler.rotate(rand_rot)


def point_inside_mesh(point, obj):
    """
    Return True if world-space point is inside the mesh obj.
    Uses ray casting along +Z and counts surface intersections.
    An odd hit count means the point is inside.
    """
    mat_inv = obj.matrix_world.inverted()
    local_pt = mat_inv @ point
    direction = mathutils.Vector((0.0, 0.0, 1.0))

    hits = 0
    origin = local_pt.copy()
    for _ in range(64):  # max intersections guard
        hit, loc, normal, face_idx = obj.ray_cast(origin, direction)
        if not hit:
            break
        hits += 1
        origin = loc + direction * 1e-5

    return (hits % 2) == 1


# =========================
# Shared duplication logic (Faces / Vertices)
# =========================

def duplicate_on_geometry(context, mode="FACES"):
    active = context.active_object
    targets = [obj for obj in context.selected_objects if obj != active]

    if not active or not targets:
        return {'CANCELLED'}

    scene = context.scene
    scale_min      = scene.face_scale_min
    scale_max      = scene.face_scale_max
    rot_min        = scene.face_rot_min
    rot_max        = scene.face_rot_max
    keep_origin    = scene.duplicate_keep_origin
    random_sel     = scene.duplicate_random_selection
    random_range   = scene.duplicate_random_range

    new_collection = make_collection("Duplicates", scene)

    for target in targets:
        if target.type != 'MESH':
            continue

        elements = (
            target.data.polygons if mode == "FACES"
            else target.data.vertices if mode == "VERTICES"
            else None
        )
        if elements is None:
            continue

        for elem in elements:
            if random_sel and random.random() > (random_range / 100.0):
                continue

            new_obj = active.copy()

            if mode == "FACES":
                new_obj.location = target.matrix_world @ elem.center
                new_obj.rotation_euler = (
                    active.rotation_euler.copy() if keep_origin
                    else elem.normal.to_track_quat('Z', 'Y').to_euler()
                )
            else:  # VERTICES
                new_obj.location = target.matrix_world @ elem.co
                if keep_origin:
                    new_obj.rotation_euler = active.rotation_euler.copy()
                else:
                    new_obj.rotation_euler = (
                        elem.normal.to_track_quat('Z', 'Y').to_euler()
                        if hasattr(elem, "normal")
                        else active.rotation_euler.copy()
                    )

            apply_random_transform(new_obj, scale_min, scale_max, rot_min, rot_max)
            new_collection.objects.link(new_obj)

    return {'FINISHED'}


# =========================
# Duplicate on Faces
# =========================
class OBJECT_OT_DuplicateOnFaces(bpy.types.Operator):
    bl_idname = "object.duplicate_on_faces"
    bl_label = "Duplicate on Faces"
    bl_description = "Duplicate selected objects on the faces of the active object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return duplicate_on_geometry(context, mode="FACES")


# =========================
# Duplicate on Vertices
# =========================
class OBJECT_OT_DuplicateOnVertices(bpy.types.Operator):
    bl_idname = "object.duplicate_on_vertices"
    bl_label = "Duplicate on Vertices"
    bl_description = "Duplicate selected objects on the vertices of the active object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return duplicate_on_geometry(context, mode="VERTICES")


# =========================
# Duplicate on Volume
# =========================
class OBJECT_OT_DuplicateOnVolume(bpy.types.Operator):
    bl_idname = "object.duplicate_on_volume"
    bl_label = "Duplicate on Volume"
    bl_description = (
        "Scatter selected objects randomly inside the volume of the active mesh "
        "using raycasting. Shares the Random Scale/Rotation sliders."
    )
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        active  = context.active_object
        sources = [obj for obj in context.selected_objects if obj != active]

        if not active:
            self.report({'ERROR'}, "No active object — this will be used as the volume")
            return {'CANCELLED'}
        if active.type != 'MESH':
            self.report({'ERROR'}, "Active object must be a mesh")
            return {'CANCELLED'}
        if not sources:
            self.report({'ERROR'}, "Select at least one other object to scatter inside the volume")
            return {'CANCELLED'}

        scene      = context.scene
        count      = scene.duplicate_volume_count
        scale_min  = scene.face_scale_min
        scale_max  = scene.face_scale_max
        rot_min    = scene.face_rot_min
        rot_max    = scene.face_rot_max

        # World-space bounding box
        corners = [active.matrix_world @ mathutils.Vector(c) for c in active.bound_box]
        min_x = min(c.x for c in corners);  max_x = max(c.x for c in corners)
        min_y = min(c.y for c in corners);  max_y = max(c.y for c in corners)
        min_z = min(c.z for c in corners);  max_z = max(c.z for c in corners)

        new_collection = make_collection(f"{active.name}_Volume", scene)

        placed       = 0
        max_attempts = count * 20
        attempts     = 0

        while placed < count and attempts < max_attempts:
            attempts += 1

            pt = mathutils.Vector((
                random.uniform(min_x, max_x),
                random.uniform(min_y, max_y),
                random.uniform(min_z, max_z),
            ))

            if not point_inside_mesh(pt, active):
                continue

            src     = random.choice(sources)
            new_obj = src.copy()
            new_obj.location      = pt
            new_obj.rotation_euler = src.rotation_euler.copy()

            apply_random_transform(new_obj, scale_min, scale_max, rot_min, rot_max)
            new_collection.objects.link(new_obj)
            placed += 1

        if placed < count:
            self.report(
                {'WARNING'},
                f"Only placed {placed}/{count} — mesh may be too concave or thin."
            )
        else:
            self.report({'INFO'}, f"{placed} objects scattered inside '{active.name}'")

        return {'FINISHED'}


# =========================
# Duplicate X Times
# =========================
class OBJECT_OT_DuplicateXTimes(bpy.types.Operator):
    bl_idname = "object.duplicate_x_times"
    bl_label = "Duplicate X Times"
    bl_description = "Duplicate the active object N times and place all copies in a new collection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        active = context.active_object
        if not active:
            self.report({'ERROR'}, "No active object")
            return {'CANCELLED'}

        count          = context.scene.duplicate_x_times_count
        new_collection = make_collection(f"{active.name}_Duplicates", context.scene)

        for _ in range(count):
            new_obj               = active.copy()
            if active.data:
                new_obj.data      = active.data.copy()
            new_obj.location      = active.location.copy()
            new_obj.rotation_euler = active.rotation_euler.copy()
            new_obj.scale         = active.scale.copy()
            new_collection.objects.link(new_obj)

        self.report({'INFO'}, f"{count} duplicates created in '{new_collection.name}'")
        return {'FINISHED'}


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
        scene  = context.scene

        # --- Main scatter buttons ---
        layout.operator("object.duplicate_on_faces",    text="Duplicate on Faces",    icon='MOD_PARTICLES')
        layout.operator("object.duplicate_on_vertices", text="Duplicate on Vertices", icon='VERTEXSEL')

        # Volume — has its own count
        layout.separator()
        layout.label(text="Duplicate on Volume:")
        layout.prop(scene, "duplicate_volume_count")
        layout.operator("object.duplicate_on_volume", text="Duplicate on Volume", icon='MESH_ICOSPHERE')

        # --- Options for Faces / Vertices ---
        layout.separator()
        layout.prop(scene, "duplicate_keep_origin")
        layout.prop(scene, "duplicate_random_selection")
        if scene.duplicate_random_selection:
            layout.prop(scene, "duplicate_random_range")

        # --- Shared scale / rotation (Faces, Vertices AND Volume) ---
        layout.separator()
        layout.label(text="Random Scale:")
        layout.prop(scene, "face_scale_min")
        layout.prop(scene, "face_scale_max")

        layout.label(text="Random Rotation (0–1 = 0–360°):")
        layout.prop(scene, "face_rot_min")
        layout.prop(scene, "face_rot_max")

        # --- Duplicate X Times ---
        layout.separator()
        layout.label(text="Duplicate X Times:")
        layout.prop(scene, "duplicate_x_times_count")
        layout.operator("object.duplicate_x_times", text="Duplicate X Times", icon='COPYDOWN')
