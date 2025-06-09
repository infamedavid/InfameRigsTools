bl_info = {
    "name": "Infame Rigs Tools",
    "author": "infame",
    "version": (0, 3, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Infame Rig Tools",
    "description": "Tools for rigging, with driver inversion and curve conversion.",
    "category": "Rigging",
}

import bpy

# ---- Property Group ----

class InfameRigToolsProperties(bpy.types.PropertyGroup):
    # --- Properties for Renaming ---
    object_name: bpy.props.StringProperty(
        name="Object",
        description="Name of the object",
        default=""
    )
    bone_name: bpy.props.StringProperty(
        name="Bone Name",
        description="Name of the bone (if object is an armature)",
        default=""
    )
    
    # --- UI Toggles ---
    show_renaming_tools: bpy.props.BoolProperty(
        name="Renaming Tools",
        description="Show/hide renaming tools",
        default=True
    )
    show_viewport_display: bpy.props.BoolProperty(
        name="Viewport Display",
        description="Show/hide viewport display options",
        default=True
    )
    show_driver_tools: bpy.props.BoolProperty(
        name="Driver Tools",
        description="Show/hide driver tools",
        default=True
    )
    
    # --- Properties for Drivers ---
    context_menu_enabled: bpy.props.BoolProperty(
        name="Context Menu Tools",
        description="Enable Invert Driver options in property context menu",
        default=True
    )

# ---- Operadores de Rigging ----

class INFAME_OT_sync_names(bpy.types.Operator):
    bl_idname = "infame.sync_names"
    bl_label = "Sync from Selection"
    bl_description = "Sync object and bone name from current selection"

    def execute(self, context):
        props = context.scene.infame_rig_tools
        obj = context.active_object
        if obj:
            props.object_name = obj.name
            if obj.type == 'ARMATURE' and context.mode in {'POSE', 'EDIT_ARMATURE'}:
                bone = obj.data.edit_bones.active if context.mode == 'EDIT_ARMATURE' else context.active_pose_bone
                if bone:
                    props.bone_name = bone.name
        return {'FINISHED'}

class INFAME_OT_rename_object(bpy.types.Operator):
    bl_idname = "infame.rename_object"
    bl_label = "Rename Object"
    bl_description = "Rename the selected object"

    def execute(self, context):
        props = context.scene.infame_rig_tools
        obj = context.active_object
        if obj and props.object_name:
            obj.name = props.object_name
        return {'FINISHED'}

class INFAME_OT_rename_bone(bpy.types.Operator):
    bl_idname = "infame.rename_bone"
    bl_label = "Rename Bone"
    bl_description = "Rename the selected bone (Pose/Edit mode)"

    def execute(self, context):
        props = context.scene.infame_rig_tools
        obj = context.active_object
        if obj and obj.type == 'ARMATURE' and context.mode in {'POSE', 'EDIT_ARMATURE'}:
            bone = obj.data.edit_bones.active if context.mode == 'EDIT_ARMATURE' else context.active_pose_bone
            if bone and props.bone_name:
                bone.name = props.bone_name
        return {'FINISHED'}

class INFAME_OT_toggle_in_front(bpy.types.Operator):
    bl_idname = "infame.toggle_in_front"
    bl_label = "Toggle In Front"
    bl_description = "Toggle 'In Front' display for armature objects"

    def execute(self, context):
        obj = context.active_object
        if obj and obj.type == 'ARMATURE':
            obj.show_in_front = not obj.show_in_front
        return {'FINISHED'}

class INFAME_OT_set_display_type(bpy.types.Operator):
    bl_idname = "infame.set_display_type"
    bl_label = "Set Display Type"
    bl_description = "Set display type for armature objects"
    type: bpy.props.EnumProperty(items=[('WIRE', "Wire", ""), ('SOLID', "Solid", "")])

    def execute(self, context):
        obj = context.active_object
        if obj and obj.type == 'ARMATURE':
            obj.display_type = self.type
        return {'FINISHED'}

class INFAME_OT_toggle_wire_overlay(bpy.types.Operator):
    bl_idname = "infame.toggle_wire_overlay"
    bl_label = "Toggle Wire Overlay"
    bl_description = "Toggle 'Wireframe Overlay' for mesh objects"

    def execute(self, context):
        obj = context.active_object
        if obj and obj.type == 'MESH':
            obj.show_wire = not obj.show_wire
        return {'FINISHED'}

class INFAME_OT_set_armature_display(bpy.types.Operator):
    bl_idname = "infame.set_armature_display"
    bl_label = "Set Armature Display"
    bl_description = "Set armature viewport display type"
    type: bpy.props.EnumProperty(items=[('OCTAHEDRAL', "Oct", ""), ('STICK', "Stick", ""), ('BBONE', "B-Bone", ""), ('ENVELOPE', "Nvlp", ""), ('WIRE', "Wire", "")])

    def execute(self, context):
        obj = context.active_object
        if obj and obj.type == 'ARMATURE':
            obj.data.display_type = self.type
        return {'FINISHED'}

# ---- Operadores de Drivers ----

def get_driver_fcurve_from_context(context):
    """Helper function to get the driver F-Curve from the UI context."""
    obj = context.active_object
    if not obj:
        return None, "No active object"

    button_pointer = context.button_pointer
    button_prop = context.button_prop

    if not button_pointer or not button_prop:
        return None, "No UI button context available"

    try:
        path = button_pointer.path_from_id(button_prop.identifier)
    except Exception:
        return None, "Unable to generate path from context"

    fcurve = None
    if obj.animation_data:
        for fc in obj.animation_data.drivers:
            if fc.data_path == path:
                fcurve = fc
                break
    
    if not fcurve:
        return None, "No driver found on this property"
        
    return fcurve, ""

class INFAME_OT_invert_current_driver(bpy.types.Operator):
    bl_idname = "infame.invert_current_driver"
    bl_label = "Invert Current Driver"
    bl_options = {'REGISTER', 'UNDO'}

    mode: bpy.props.EnumProperty(
        items=[
            ('CURVE_ZERO', "Curve from Zero", "Invert driver curve from x=0"),
            ('CURVE_AVG', "Curve Average", "Invert driver curve around average x"),
        ],
        name="Invert Mode",
        default='CURVE_ZERO'
    )

    def execute(self, context):
        fcurve, error_msg = get_driver_fcurve_from_context(context)
        if error_msg:
            self.report({'WARNING'}, error_msg)
            return {'CANCELLED'}

        if not fcurve.keyframe_points:
            self.report({'WARNING'}, "Driver has no keyframes to invert")
            return {'CANCELLED'}

        if self.mode == 'CURVE_ZERO':
            for kp in fcurve.keyframe_points:
                kp.co[0] *= -1
                kp.handle_left[0] *= -1
                kp.handle_right[0] *= -1

        elif self.mode == 'CURVE_AVG':
            xs = [kp.co[0] for kp in fcurve.keyframe_points]
            if not xs:
                return {'CANCELLED'}
            avg_x = sum(xs) / len(xs)
            for kp in fcurve.keyframe_points:
                kp.co[0] = 2 * avg_x - kp.co[0]
                kp.handle_left[0] = 2 * avg_x - kp.handle_left[0]
                kp.handle_right[0] = 2 * avg_x - kp.handle_right[0]
        
        fcurve.update()
        return {'FINISHED'}

class INFAME_OT_convert_driver_curve(bpy.types.Operator):
    """Convert Driver curve interpolation type"""
    bl_idname = "infame.convert_driver_curve"
    bl_label = "Convert Driver Curve Type"
    bl_options = {'REGISTER', 'UNDO'}

    mode: bpy.props.EnumProperty(
        items=[
            ('LINEAR', "Linear", "Set keyframe interpolation to Linear"),
            ('CONSTANT', "Constant", "Set keyframe interpolation to Constant"),
        ],
        name="Conversion Mode"
    )

    def execute(self, context):
        fcurve, error_msg = get_driver_fcurve_from_context(context)
        if error_msg:
            self.report({'WARNING'}, error_msg)
            return {'CANCELLED'}

        if not fcurve.keyframe_points:
            self.report({'WARNING'}, "Driver has no keyframes to convert")
            return {'CANCELLED'}

        for kp in fcurve.keyframe_points:
            if self.mode == 'LINEAR':
                kp.interpolation = 'LINEAR'
            elif self.mode == 'CONSTANT':
                kp.interpolation = 'CONSTANT'
        
        fcurve.update()
        return {'FINISHED'}

# ---- Menú contextual ----

def draw_driver_context_menu(self, context):
    if not context.scene.infame_rig_tools.context_menu_enabled:
        return
    
    if not context.button_pointer or not context.button_prop:
        return

    layout = self.layout
    layout.separator()
    
    # Invert operators
    op = layout.operator("infame.invert_current_driver", text="Invert Driver (from Zero)")
    op.mode = 'CURVE_ZERO'
    op = layout.operator("infame.invert_current_driver", text="Invert Driver (Average)")
    op.mode = 'CURVE_AVG'
    
    layout.separator()
    
    # Convert operators
    op = layout.operator("infame.convert_driver_curve", text="Convert to Linear")
    op.mode = 'LINEAR'
    op = layout.operator("infame.convert_driver_curve", text="Convert to Constant")
    op.mode = 'CONSTANT'

# ---- Panel ----

class INFAME_PT_rig_tools(bpy.types.Panel):
    bl_label = "Infame Rig Tools"
    bl_idname = "INFAME_PT_rig_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Infame Rig Tools"

    def draw(self, context):
        layout = self.layout
        props = context.scene.infame_rig_tools
        obj = context.active_object

        # --- Renaming Section ---
        row = layout.row(align=True)
        row.prop(props, "show_renaming_tools", text="Renaming Tools", icon="TRIA_DOWN" if props.show_renaming_tools else "TRIA_RIGHT", emboss=False)
        if props.show_renaming_tools:
            box = layout.box()
            box.operator("infame.sync_names", icon="FILE_REFRESH")
            col = box.column(align=True)
            col.prop(props, "object_name")
            col.operator("infame.rename_object", icon="OUTLINER_OB_EMPTY", text="Rename Object")
            
            if obj and obj.type == 'ARMATURE' and context.mode in {'POSE', 'EDIT_ARMATURE'}:
                col.separator()
                col.prop(props, "bone_name")
                col.operator("infame.rename_bone", icon="BONE_DATA", text="Rename Bone")
        
        layout.separator()

        # --- Viewport Display Section ---
        row = layout.row(align=True)
        row.prop(props, "show_viewport_display", text="Viewport Display", icon="TRIA_DOWN" if props.show_viewport_display else "TRIA_RIGHT", emboss=False)
        if props.show_viewport_display:
            box = layout.box()
            if obj:
                if obj.type == 'ARMATURE':
                    box.operator("infame.toggle_in_front", icon="GHOST_ENABLED")
                    row = box.row(align=True)
                    row.label(text="Display As:")
                    op = row.operator("infame.set_display_type", text="Wire")
                    op.type = 'WIRE'
                    op = row.operator("infame.set_display_type", text="Solid")
                    op.type = 'SOLID'
                    
                    row = box.row(align=True)
                    row.label(text="Rig Shape:")
                    for dtype, label in [('OCTAHEDRAL', 'Oct'), ('STICK', 'Stick'), ('BBONE', 'B-Bone'), ('ENVELOPE', 'Nvlp'), ('WIRE', 'Wire')]:
                        op = row.operator("infame.set_armature_display", text=label)
                        op.type = dtype
                        
                elif obj.type == 'MESH':
                    box.operator("infame.toggle_wire_overlay", icon="MOD_WIREFRAME")
                else:
                    box.label(text="Select Armature or Mesh")
            else:
                box.label(text="Select an object")
                
        layout.separator()

        # --- Driver Tools Section ---
        row = layout.row(align=True)
        row.prop(props, "show_driver_tools", text="Driver Tools", icon="TRIA_DOWN" if props.show_driver_tools else "TRIA_RIGHT", emboss=False)
        if props.show_driver_tools:
            box = layout.box()
            box.prop(props, "context_menu_enabled")


# ---- Registro ----

classes = (
    InfameRigToolsProperties,
    INFAME_OT_sync_names,
    INFAME_OT_rename_object,
    INFAME_OT_rename_bone,
    INFAME_OT_toggle_in_front,
    INFAME_OT_set_display_type,
    INFAME_OT_toggle_wire_overlay,
    INFAME_OT_set_armature_display,
    INFAME_OT_invert_current_driver,
    INFAME_OT_convert_driver_curve, # <- Clase nueva registrada
    INFAME_PT_rig_tools,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.infame_rig_tools = bpy.props.PointerProperty(type=InfameRigToolsProperties)
    bpy.types.UI_MT_button_context_menu.append(draw_driver_context_menu)

def unregister():
    bpy.types.UI_MT_button_context_menu.remove(draw_driver_context_menu)
    del bpy.types.Scene.infame_rig_tools
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()