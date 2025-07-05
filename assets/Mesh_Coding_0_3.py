bl_info = {
    "name": "Mesh Coding",
    "author": "Infame",
    "version": (0, 3),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Tool / Infame Rig Tools",
    "description": "Convert mesh to JSON and assign to bone. Integrates with Infame Rig Tools if available.",
    "category": "Development"
}

import bpy
import json
from bpy.props import StringProperty
from bpy.types import Operator, Panel

class MESHCODING_OT_export_to_json(Operator):
    bl_idname = "meshcoding.export_to_json"
    bl_label = "Export Mesh to JSON"
    bl_description = "Save selected mesh as JSON (vertices/edges)"

    filepath: StringProperty(subtype='FILE_PATH')

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Select a MESH object")
            return {'CANCELLED'}

        mesh_data = {
            "vertices": [list(v.co) for v in obj.data.vertices],
            "edges": [list(e.vertices) for e in obj.data.edges]
        }

        with open(self.filepath, 'w') as f:
            json.dump(mesh_data, f, indent=2)

        self.report({'INFO'}, f"Saved: {self.filepath}")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class MESHCODING_OT_import_to_bone(Operator):
    bl_idname = "meshcoding.import_to_bone"
    bl_label = "Shape to Bone"
    bl_description = "Add a custom shape key from a .JSON file"

    filepath: StringProperty(subtype='FILE_PATH')

    def execute(self, context):
        bone = context.active_pose_bone
        if not bone:
            self.report({'ERROR'}, "Select a bone in POSE mode")
            return {'CANCELLED'}

        try:
            with open(self.filepath, 'r') as f:
                mesh_data = json.load(f)

            mesh = bpy.data.meshes.new("imported_shape")
            mesh.from_pydata(mesh_data["vertices"], mesh_data["edges"], [])

            shape_obj = bpy.data.objects.new("shape_" + bone.name, mesh)
            bpy.context.collection.objects.link(shape_obj)
            bone.custom_shape = shape_obj

            self.report({'INFO'}, f"Shape assigned to {bone.name}")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class VIEW3D_PT_mesh_coding(Panel):
    bl_label = "Mesh Coding"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout
        layout.operator("meshcoding.export_to_json", text="Mesh to JSON", icon='FILE_TEXT')

        obj = context.object
        if obj and obj.type == 'ARMATURE' and context.mode == 'POSE' and obj.pose.bones:
            layout.operator("meshcoding.import_to_bone", text="Shape to Bone", icon='BONE_DATA')

def draw_json_to_bone_button(self, context):
    obj = context.object
    if not (obj and obj.type == 'ARMATURE' and context.mode == 'POSE' and obj.pose.bones):
        return

    layout = self.layout
    box = layout.box()
    box.label(text="Shapes Importer", icon="SHAPEKEY_DATA")
    op = box.operator(
        "meshcoding.import_to_bone",
        text="Shape to Bone",
        icon="BONE_DATA"
    )
    op.bl_description = "Add a custom shape key from a .JSON file"

classes = (
    MESHCODING_OT_export_to_json,
    MESHCODING_OT_import_to_bone,
    VIEW3D_PT_mesh_coding,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    if hasattr(bpy.types, "INFAME_PT_rig_tools"):
        bpy.types.INFAME_PT_rig_tools.append(draw_json_to_bone_button)

def unregister():
    if hasattr(bpy.types, "INFAME_PT_rig_tools"):
        try:
            bpy.types.INFAME_PT_rig_tools.remove(draw_json_to_bone_button)
        except:
            pass

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
    