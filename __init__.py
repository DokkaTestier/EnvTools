bl_info = {
    "name": "EnvTools",
    "author": "Tu Nombre",
    "version": (1, 0),
    "blender": (2, 93, 0),
    "location": "View3D > Tool",
    "description": "Herramientas para entornos: reemplazar objetos y duplicar",
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

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
