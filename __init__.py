bl_info = {
    "name": "EnvTools",
    "author": "brandon buchan",
    "version": (1, 3),
    "blender": (2, 93, 0),
    "location": "View3D > Tool",
    "description": "Environment tools: replace objects, duplicate on faces/vertices/volume, utility shortcuts, ID map",
    "category": "Object",
}

import bpy
from . import replace_with_active
from . import duplicate_on
from . import utility_panel
from . import id_map

classes = (
    # Replace with Active
    replace_with_active.OBJECT_OT_ReplaceWithActive,
    replace_with_active.VIEW3D_PT_ReplaceWithActivePanel,
    # Duplicate On
    duplicate_on.OBJECT_OT_DuplicateOnFaces,
    duplicate_on.OBJECT_OT_DuplicateOnVertices,
    duplicate_on.OBJECT_OT_DuplicateOnVolume,
    duplicate_on.OBJECT_OT_DuplicateXTimes,
    duplicate_on.VIEW3D_PT_DuplicateOnPanel,
    # Utility
    utility_panel.MESH_OT_deselect_boundary,
    utility_panel.OBJECT_OT_apply_all_transform,
    utility_panel.OBJECT_OT_apply_all_modifiers,
    utility_panel.VIEW3D_OT_set_orientation_global,
    utility_panel.VIEW3D_OT_set_orientation_normal,
    utility_panel.VIEW3D_OT_set_orientation_view,
    utility_panel.OBJECT_OT_merge_overlap,
    utility_panel.VIEW3D_PT_UtilityPanel,
    # ID Map
    id_map.OBJECT_OT_id_add_slot,
    id_map.OBJECT_OT_id_remove_slot,
    id_map.OBJECT_OT_id_slot_move_up,
    id_map.OBJECT_OT_id_slot_move_down,
    id_map.OBJECT_OT_id_assign,
    id_map.OBJECT_OT_id_select,
    id_map.OBJECT_OT_id_deselect,
    id_map.OBJECT_OT_id_select_by_material,
    id_map.OBJECT_OT_generate_id,
    id_map.OBJECT_OT_generate_id_by_uv_islands,
    id_map.VIEW3D_PT_IDMapPanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # --- Duplicate On: Faces / Vertices shared props ---
    bpy.types.Scene.face_scale_min = bpy.props.FloatProperty(
        name="Min Scale", default=1.0, min=0.0, max=10.0
    )
    bpy.types.Scene.face_scale_max = bpy.props.FloatProperty(
        name="Max Scale", default=1.0, min=0.0, max=10.0
    )
    bpy.types.Scene.face_rot_min = bpy.props.FloatProperty(
        name="Min Rotation", default=0.0, min=0.0, max=1.0,
        description="Minimum random rotation (1.0 = 360°)"
    )
    bpy.types.Scene.face_rot_max = bpy.props.FloatProperty(
        name="Max Rotation", default=0.0, min=0.0, max=1.0,
        description="Maximum random rotation (1.0 = 360°)"
    )
    bpy.types.Scene.rot_axis_x = bpy.props.BoolProperty(name="X", default=False)
    bpy.types.Scene.rot_axis_y = bpy.props.BoolProperty(name="Y", default=False)
    bpy.types.Scene.rot_axis_z = bpy.props.BoolProperty(name="Z", default=True)

    bpy.types.Scene.duplicate_keep_origin = bpy.props.BoolProperty(
        name="Keep Origin",
        default=False,
        description="Keep the original object orientation instead of aligning to face normals"
    )
    bpy.types.Scene.duplicate_linked = bpy.props.BoolProperty(
        name="Linked",
        default=False,
        description="Linked: duplicates share mesh data (Alt+D). Unchecked: independent copy (Shift+D)"
    )
    bpy.types.Scene.duplicate_random_selection = bpy.props.BoolProperty(
        name="Random Selection",
        default=False,
        description="Randomly select faces/vertices for duplication"
    )
    bpy.types.Scene.duplicate_random_range = bpy.props.FloatProperty(
        name="Random Range Selection (%)",
        default=100.0, min=1.0, max=100.0,
        subtype="PERCENTAGE"
    )

    # --- Duplicate on Volume ---
    bpy.types.Scene.duplicate_volume_count = bpy.props.IntProperty(
        name="Count",
        default=10, min=1, max=99999,
        description="Number of objects to scatter inside the volume"
    )

    # --- Duplicate X Times ---
    bpy.types.Scene.duplicate_x_times_count = bpy.props.IntProperty(
        name="Count",
        default=1, min=1, max=9999,
        description="Number of duplicates to create"
    )

    # --- Replace with Active ---
    bpy.types.Scene.replace_apply_scale = bpy.props.BoolProperty(
        name="Use Replaced Object Scale",
        default=False,
        description="ON: each replacement inherits the scale of the object it replaces. OFF: keeps the active object's own scale"
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    for prop in [
        "face_scale_min", "face_scale_max",
        "face_rot_min", "face_rot_max",
        "rot_axis_x", "rot_axis_y", "rot_axis_z",
        "duplicate_keep_origin",
        "duplicate_linked",
        "duplicate_random_selection", "duplicate_random_range",
        "duplicate_volume_count",
        "duplicate_x_times_count",
        "replace_apply_scale",
    ]:
        if hasattr(bpy.types.Scene, prop):
            delattr(bpy.types.Scene, prop)


if __name__ == "__main__":
    register()
