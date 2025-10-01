bl_info = {
    "name": "EnvTools",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (2, 93, 0),
    "location": "View3D > Tool",
    "description": "Environment tools: replace objects and duplicate on faces",
    "category": "Object",
}

import bpy
from . import replace_with_active
from . import duplicate_on

classes = (
    replace_with_active.OBJECT_OT_ReplaceWithActive,
    duplicate_on.OBJECT_OT_DuplicateOnFaces,
    replace_with_active.VIEW3D_PT_ReplaceWithActivePanel,
    duplicate_on.VIEW3D_PT_DuplicateOnFacesPanel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # Properties for random scale
    bpy.types.Scene.face_scale_min = bpy.props.FloatProperty(
        name="Min Scale", default=1.0, min=0.0, max=10.0
    )
    bpy.types.Scene.face_scale_max = bpy.props.FloatProperty(
        name="Max Scale", default=1.0, min=0.0, max=10.0
    )

    # Random rotation (0–1 → 0–360°)
    bpy.types.Scene.face_rot_min = bpy.props.FloatProperty(
        name="Min Rotation", default=0.0, min=0.0, max=1.0,
        description="Minimum random rotation (1.0 = 360°)"
    )
    bpy.types.Scene.face_rot_max = bpy.props.FloatProperty(
        name="Max Rotation", default=0.0, min=0.0, max=1.0,
        description="Maximum random rotation (1.0 = 360°)"
    )

    # Rotation axis toggles
    bpy.types.Scene.rot_axis_x = bpy.props.BoolProperty(name="X", default=False)
    bpy.types.Scene.rot_axis_y = bpy.props.BoolProperty(name="Y", default=False)
    bpy.types.Scene.rot_axis_z = bpy.props.BoolProperty(name="Z", default=True)

    bpy.types.Scene.duplicate_keep_origin = bpy.props.BoolProperty(
        name="Keep Origin",
        default=False,
        description="Keep the original object orientation instead of aligning to face normals"
    )
    bpy.types.Scene.duplicate_random_selection = bpy.props.BoolProperty(
        name="Random Selection",
        default=False,
        description="Randomly select faces for duplication"
    )
    bpy.types.Scene.duplicate_random_range = bpy.props.FloatProperty(
        name="Random Range Selection (%)",
        default=100.0,
        min=1.0,
        max=100.0,
        subtype="PERCENTAGE"
    )

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.face_scale_min
    del bpy.types.Scene.face_scale_max
    del bpy.types.Scene.face_rot_min
    del bpy.types.Scene.face_rot_max
    del bpy.types.Scene.rot_axis_x
    del bpy.types.Scene.rot_axis_y
    del bpy.types.Scene.rot_axis_z
    del bpy.types.Scene.duplicate_keep_origin
    del bpy.types.Scene.duplicate_random_selection
    del bpy.types.Scene.duplicate_random_range

if __name__ == "__main__":
    register()
