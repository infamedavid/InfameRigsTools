bl_info = {
    "name": "Infame Rigs Tools",
    "author": "infame",
    "version": (0, 3, 4),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Infame Rig Tools",
    "description": "Tools for rigging.",
    "category": "Rigging",
}

import bpy
import blf 

# ---- Property Group ----

class InfameRigToolsProperties(bpy.types.PropertyGroup):
   
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
    # CAMBIO: Se añade un booleano para el nuevo panel de Parenting.
    show_parenting_tools: bpy.props.BoolProperty(
        name="Parenting",
        description="Show/hide parenting tools",
        default=True
    )


# ---- Operadores de Rigging ----

class INFAME_OT_sync_names(bpy.types.Operator):
    bl_idname = "infame.sync_names"; bl_label = "Sync from Selection"; bl_description = "Sync object and bone name from current selection"
    def execute(self, context):
        props = context.scene.infame_rig_tools; obj = context.active_object
        if obj:
            props.object_name = obj.name
            if obj.type == 'ARMATURE' and context.mode in {'POSE', 'EDIT_ARMATURE'}:
                bone = obj.data.edit_bones.active if context.mode == 'EDIT_ARMATURE' else context.active_pose_bone
                if bone: props.bone_name = bone.name
        return {'FINISHED'}
class INFAME_OT_rename_object(bpy.types.Operator):
    bl_idname = "infame.rename_object"; bl_label = "Rename Object"; bl_description = "Rename the selected object"
    def execute(self, context):
        props = context.scene.infame_rig_tools; obj = context.active_object
        if obj and props.object_name: obj.name = props.object_name
        return {'FINISHED'}
class INFAME_OT_rename_bone(bpy.types.Operator):
    bl_idname = "infame.rename_bone"; bl_label = "Rename Bone"; bl_description = "Rename the selected bone (Pose/Edit mode)"
    def execute(self, context):
        props = context.scene.infame_rig_tools; obj = context.active_object
        if obj and obj.type == 'ARMATURE' and context.mode in {'POSE', 'EDIT_ARMATURE'}:
            bone = obj.data.edit_bones.active if context.mode == 'EDIT_ARMATURE' else context.active_pose_bone
            if bone and props.bone_name: bone.name = props.bone_name
        return {'FINISHED'}
class INFAME_OT_toggle_in_front(bpy.types.Operator):
    bl_idname = "infame.toggle_in_front"; bl_label = "Toggle In Front"; bl_description = "Toggle 'In Front' display for armature objects"
    def execute(self, context):
        obj = context.active_object
        if obj and obj.type == 'ARMATURE': obj.show_in_front = not obj.show_in_front
        return {'FINISHED'}
class INFAME_OT_set_display_type(bpy.types.Operator):
    bl_idname = "infame.set_display_type"; bl_label = "Set Display Type"; bl_description = "Set display type for armature objects"
    type: bpy.props.EnumProperty(items=[('WIRE', "Wire", ""), ('SOLID', "Solid", "")])
    def execute(self, context):
        obj = context.active_object
        if obj and obj.type == 'ARMATURE': obj.display_type = self.type
        return {'FINISHED'}
class INFAME_OT_toggle_wire_overlay(bpy.types.Operator):
    bl_idname = "infame.toggle_wire_overlay"; bl_label = "Toggle Wire Overlay"; bl_description = "Toggle 'Wireframe Overlay' for mesh objects"
    def execute(self, context):
        obj = context.active_object
        if obj and obj.type == 'MESH': obj.show_wire = not obj.show_wire
        return {'FINISHED'}
class INFAME_OT_set_armature_display(bpy.types.Operator):
    bl_idname = "infame.set_armature_display"; bl_label = "Set Armature Display"; bl_description = "Set armature viewport display type"
    type: bpy.props.EnumProperty(items=[('OCTAHEDRAL', "Oct", ""), ('STICK', "Stick", ""), ('BBONE', "B-Bone", ""), ('ENVELOPE', "Nvlp", ""), ('WIRE', "Wire", "")])
    def execute(self, context):
        obj = context.active_object
        if obj and obj.type == 'ARMATURE': obj.data.display_type = self.type
        return {'FINISHED'}

# ---- Operadores de Drivers ----

def get_driver_fcurve_from_context(context):
    obj = context.active_object
    if not obj: return None, "No active object"
    button_pointer = context.button_pointer
    button_prop = context.button_prop
    if not button_pointer or not button_prop: return None, "No UI button context available"
    try: path = button_pointer.path_from_id(button_prop.identifier)
    except Exception: return None, "Unable to generate path from context"
    if obj.animation_data:
        for fc in obj.animation_data.drivers:
            if fc.data_path == path: return fc, ""
    return None, "No driver found on this property"
class INFAME_OT_invert_current_driver(bpy.types.Operator):
    bl_idname = "infame.invert_current_driver"; bl_label = "Invert Current Driver"; bl_options = {'REGISTER', 'UNDO'}
    mode: bpy.props.EnumProperty(items=[('CURVE_ZERO', "Curve from Zero", ""), ('CURVE_AVG', "Curve Average", "")], name="Invert Mode")
    def execute(self, context):
        fcurve, error_msg = get_driver_fcurve_from_context(context)
        if error_msg: self.report({'WARNING'}, error_msg); return {'CANCELLED'}
        if not fcurve.keyframe_points: self.report({'WARNING'}, "Driver has no keyframes"); return {'CANCELLED'}
        if self.mode == 'CURVE_ZERO':
            for kp in fcurve.keyframe_points: kp.co[0] *= -1; kp.handle_left[0] *= -1; kp.handle_right[0] *= -1
        elif self.mode == 'CURVE_AVG':
            xs = [kp.co[0] for kp in fcurve.keyframe_points]
            if not xs: return {'CANCELLED'}
            avg_x = sum(xs) / len(xs)
            for kp in fcurve.keyframe_points: kp.co[0] = 2 * avg_x - kp.co[0]; kp.handle_left[0] = 2 * avg_x - kp.handle_left[0]; kp.handle_right[0] = 2 * avg_x - kp.handle_right[0]
        fcurve.update(); return {'FINISHED'}
class INFAME_OT_convert_driver_curve(bpy.types.Operator):
    bl_idname = "infame.convert_driver_curve"; bl_label = "Convert Driver Curve Type"; bl_options = {'REGISTER', 'UNDO'}
    mode: bpy.props.EnumProperty(items=[('LINEAR', "Linear", ""), ('CONSTANT', "Constant", "")], name="Conversion Mode")
    def execute(self, context):
        fcurve, error_msg = get_driver_fcurve_from_context(context)
        if error_msg: self.report({'WARNING'}, error_msg); return {'CANCELLED'}
        if not fcurve.keyframe_points: self.report({'WARNING'}, "Driver has no keyframes"); return {'CANCELLED'}
        for kp in fcurve.keyframe_points:
            if self.mode == 'LINEAR': kp.interpolation = 'LINEAR'
            elif self.mode == 'CONSTANT': kp.interpolation = 'CONSTANT'
        fcurve.update(); return {'FINISHED'}

#----- Flip Drivers ------------------

# --- Funciones para Flip Driver ---
import re

def _flip_token(token: str) -> str:
    patterns = [
        (r'([._-])l(?=$|[^a-zA-Z0-9])', r'\1r'),
        (r'([._-])r(?=$|[^a-zA-Z0-9])', r'\1l'),
        (r'([._-])L(?=$|[^a-zA-Z0-9])', r'\1R'),
        (r'([._-])R(?=$|[^a-zA-Z0-9])', r'\1L'),
        (r'^(l)([._-])', r'r\2'),
        (r'^(r)([._-])', r'l\2'),
        (r'^(L)([._-])', r'R\2'),
        (r'^(R)([._-])', r'L\2'),
    ]
    for pattern, replacement in patterns:
        flipped = re.sub(pattern, replacement, token)
        if flipped != token:
            return flipped
    return token

def flip_path_universal(path: str) -> str:
    parts = re.split(r'([.\[\]"\'])', path)
    flipped_parts = [_flip_token(p) for p in parts]
    return "".join(flipped_parts)

def get_driver_fcurve(context):
    obj = context.active_object
    button_pointer = context.button_pointer
    button_prop = context.button_prop

    if not obj or not button_pointer or not button_prop:
        return None, "No active object or button context"

    try:
        path = button_pointer.path_from_id(button_prop.identifier)
    except Exception:
        return None, "Could not resolve path"

    if not obj.animation_data:
        return None, "Object has no animation data"

    for fc in obj.animation_data.drivers:
        if fc.data_path == path:
            if not fc.driver:
                return None, "FCurve has no driver assigned"
            return fc.driver, ""

    return None, "Driver not found"

# --- Operador Flip Driver ---

class INFAME_OT_flip_driver(bpy.types.Operator):
    bl_idname = "infame.flip_driver"
    bl_label = "Flip Driver"
    bl_description = "Flip L/R in driver variable targets"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        driver, error = get_driver_fcurve(context)
        if not driver:
            self.report({'WARNING'}, error)
            return {'CANCELLED'}

        flipped_any = False

        for var in driver.variables:
            for target in var.targets:
                if target.bone_target:
                    new_bone = _flip_token(target.bone_target)
                    if new_bone != target.bone_target:
                        target.bone_target = new_bone
                        flipped_any = True

                if var.type == 'SINGLE_PROP' and target.data_path:
                    new_path = flip_path_universal(target.data_path)
                    if new_path != target.data_path:
                        target.data_path = new_path
                        flipped_any = True

                if target.id:
                    old_name = target.id.name
                    new_name = _flip_token(old_name)
                    if new_name != old_name:
                        alt = bpy.data.objects.get(new_name)
                        if alt:
                            target.id = alt
                            flipped_any = True

        if flipped_any:
            self.report({'INFO'}, "Driver variables flipped")
            context.view_layer.update()
        else:
            self.report({'INFO'}, "No flippable L/R variables found")

        return {'FINISHED'}


# ---- Operador de Live Parenting ----

class INFAME_OT_live_parenting(bpy.types.Operator):
    bl_idname = "infame.live_parenting"
    bl_label = "Live Parenting"
    bl_description = "Parent selected items progressively. Add to Quick Favorites via: Object > Parent > (right click)"
    bl_options = {'REGISTER', 'UNDO'}

    _handle = None
    last_item = None
    rollback_data = []

    def invoke(self, context, event):
        self.last_item = None
        self.rollback_data.clear()
        if context.mode == 'OBJECT':
            for obj in context.scene.objects: obj.select_set(False)
            context.view_layer.objects.active = None
        elif context.mode == 'EDIT_ARMATURE':
            for bone in context.object.data.edit_bones: bone.select = False
        if not self._handle:
            self._handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback, (context,), 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        self.report({'INFO'}, "Live Parenting: Select in order. Enter to finish, Esc to cancel.")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if context.area: context.area.tag_redraw()
        if event.type == 'ESC':
            self.rollback(context); self.cleanup_draw()
            self.report({'WARNING'}, "Live Parenting cancelled.")
            return {'CANCELLED'}
        elif event.type == 'RET' and event.value == 'PRESS':
            self.cleanup_draw()
            self.report({'INFO'}, "Live Parenting finished.")
            return {'FINISHED'}
        current = self.get_current_selection(context)
        if current and current != self.last_item:
            if self.last_item: self.do_parent(context, self.last_item, current)
            self.last_item = current
            self.force_selection(context, current)
        return {'PASS_THROUGH'}

    def get_current_selection(self, context):
        if context.mode == 'OBJECT': return context.active_object
        elif context.mode == 'EDIT_ARMATURE': return context.active_bone
        return None

    def force_selection(self, context, item):
        if context.mode == 'OBJECT':
            for obj in context.selected_objects: obj.select_set(False)
            item.select_set(True); context.view_layer.objects.active = item
        elif context.mode == 'EDIT_ARMATURE':
            for bone in context.object.data.edit_bones: bone.select = False
            item.select = True

    def do_parent(self, context, parent, child):
        if parent == child: return
        if context.mode == 'OBJECT':
            self.rollback_data.append((child, child.parent, child.matrix_world.copy()))
            child.parent = parent
            child.matrix_parent_inverse = parent.matrix_world.inverted()
        elif context.mode == 'EDIT_ARMATURE':
            ebones = context.object.data.edit_bones
            if parent.name not in ebones or child.name not in ebones: return
            pbone = ebones[parent.name]; cbone = ebones[child.name]
            self.rollback_data.append((cbone, cbone.parent, cbone.use_connect))
            cbone.parent = pbone; cbone.use_connect = False
            if (pbone.tail - cbone.head).length < 0.001: cbone.use_connect = True

    def rollback(self, context):
        if context.mode == 'OBJECT':
            for obj, old_parent, old_matrix in reversed(self.rollback_data):
                obj.parent = old_parent; obj.matrix_world = old_matrix
        elif context.mode == 'EDIT_ARMATURE':
            for bone, old_parent, old_connect in reversed(self.rollback_data):
                bone.parent = old_parent; bone.use_connect = old_connect

    def cleanup_draw(self):
        if self._handle:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            self._handle = None

    def draw_callback(self, context):
        font_id = 0; blf.position(font_id, 20, 50, 0); blf.size(font_id, 18, 72)
        blf.color(font_id, 1.0, 1.0, 0.0, 1.0)
        blf.draw(font_id, "⚠️ LIVE PARENTING ACTIVE – Press Enter to confirm, Esc to cancel")

# ---- Menús contextuales ----

def draw_driver_context_menu(self, context):

    if not context.button_pointer or not context.button_prop: return
    layout = self.layout; layout.separator()
    op = layout.operator("infame.invert_current_driver", text="Invert Driver (from Zero)"); op.mode = 'CURVE_ZERO'
    op = layout.operator("infame.invert_current_driver", text="Invert Driver (Average)"); op.mode = 'CURVE_AVG'
    layout.separator()
    op = layout.operator("infame.convert_driver_curve", text="Convert to Linear"); op.mode = 'LINEAR'
    op = layout.operator("infame.convert_driver_curve", text="Convert to Constant"); op.mode = 'CONSTANT'

def draw_live_parenting_in_object_menu(self, context):
    mode = context.mode
    if mode in {'OBJECT', 'EDIT_ARMATURE'}:
        self.layout.separator()
        self.layout.operator("infame.live_parenting", text="Live Parenting")
        
def draw_flip_driver_menu(self, context):
    layout = self.layout
    layout.separator()
    layout.operator("infame.flip_driver", text="Flip Driver Sides, (L>R,R>L)")


# ---- Panel ----

class INFAME_PT_rig_tools(bpy.types.Panel):
    bl_label = "Infame Rig Tools"; bl_idname = "INFAME_PT_rig_tools"
    bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = "Infame Rig Tools"

    def draw(self, context):
        layout = self.layout
        props = context.scene.infame_rig_tools
        obj = context.active_object

        # --- Renaming Section ---
        row = layout.row(align=True)
        row.prop(props, "show_renaming_tools", text="Renaming Tools", icon="TRIA_DOWN" if props.show_renaming_tools else "TRIA_RIGHT", emboss=False)
        if props.show_renaming_tools:
            box = layout.box(); box.operator("infame.sync_names", icon="FILE_REFRESH")
            col = box.column(align=True); col.prop(props, "object_name"); col.operator("infame.rename_object", icon="OUTLINER_OB_EMPTY", text="Rename Object")
            if obj and obj.type == 'ARMATURE' and context.mode in {'POSE', 'EDIT_ARMATURE'}:
                col.separator(); col.prop(props, "bone_name"); col.operator("infame.rename_bone", icon="BONE_DATA", text="Rename Bone")
        layout.separator()

        # --- Viewport Display Section ---
        row = layout.row(align=True)
        row.prop(props, "show_viewport_display", text="Viewport Display", icon="TRIA_DOWN" if props.show_viewport_display else "TRIA_RIGHT", emboss=False)
        if props.show_viewport_display:
            box = layout.box()
            if obj:
                if obj.type == 'ARMATURE':
                    box.operator("infame.toggle_in_front", icon="GHOST_ENABLED")
                    row = box.row(align=True); row.label(text="Display As:")
                    op = row.operator("infame.set_display_type", text="Wire"); op.type = 'WIRE'
                    op = row.operator("infame.set_display_type", text="Solid"); op.type = 'SOLID'
                    row = box.row(align=True); row.label(text="Rig Shape:")
                    for dtype, label in [('OCTAHEDRAL', 'Oct'), ('STICK', 'Stick'), ('BBONE', 'B-Bone'), ('ENVELOPE', 'Nvlp'), ('WIRE', 'Wire')]:
                        op = row.operator("infame.set_armature_display", text=label); op.type = dtype
                elif obj.type == 'MESH':
                    box.operator("infame.toggle_wire_overlay", icon="MOD_WIREFRAME")
                else:
                    box.label(text="Select Armature or Mesh")
            else:
                box.label(text="Select an object")
        layout.separator()
        
        # --- Parenting Section ---

        row = layout.row(align=True)
        row.prop(props, "show_parenting_tools", text="Parenting", icon="TRIA_DOWN" if props.show_parenting_tools else "TRIA_RIGHT", emboss=False)
        if props.show_parenting_tools:
            box = layout.box()
            box.operator("infame.live_parenting", icon='CONSTRAINT')

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
    INFAME_OT_convert_driver_curve,
    INFAME_OT_live_parenting,
    INFAME_OT_flip_driver,
    INFAME_PT_rig_tools,
)

def register():
    for cls in classes: bpy.utils.register_class(cls)
    bpy.types.Scene.infame_rig_tools = bpy.props.PointerProperty(type=InfameRigToolsProperties)
    bpy.types.UI_MT_button_context_menu.append(draw_driver_context_menu)
    bpy.types.VIEW3D_MT_object_parent.append(draw_live_parenting_in_object_menu)
    bpy.types.UI_MT_button_context_menu.append(draw_flip_driver_menu)

def unregister():
    bpy.types.UI_MT_button_context_menu.remove(draw_driver_context_menu)
    bpy.types.VIEW3D_MT_object_parent.remove(draw_live_parenting_in_object_menu)
    del bpy.types.Scene.infame_rig_tools
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
    bpy.types.UI_MT_button_context_menu.remove(draw_flip_driver_menu)

if __name__ == "__main__":
    register()
