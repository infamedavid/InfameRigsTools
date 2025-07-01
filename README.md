# InfameRigsTools
A collection of tools for Riggers using Blender 4.x  

---

### Rename Objects and Bones
- Edit the name of the active object.
- If the object is an armature, also edit the active bone name (in Pose or Edit mode).
- Sync button to copy names from current selection.

### Viewport Display
- Toggle X-ray display for armature objects.
- Change object display type: Wire, Solid.
- Change rig shape display: Octahedral, Stick, B-Bone, Envelope, Wire.
- Toggle wireframe overlay for mesh objects.

---

### ⇄ Invert Driver
- Available via right-click on properties with drivers.
- Two modes:
  - Invert curve around x = 0.
  - Invert curve around the average of x.

### 🔄 Convert Driver Curve
- Switches driver function interpolation between **Linear** and **Constant**.

### 🔀 Flip Driver Side
- Flips left/right references in driver targets.
- Works with:
  - `bone_target`
  - `data_path` (Single Property)
  - `target.id` (if the symmetric object exists)
- Detects suffixes and prefixes like `.L`, `_R`, `.l`, `-r`, etc.
- Does not rename objects, only flips the driver reference.
- Accessed via right-click on a driven property.

---

## 🪜 Advanced Parenting

### ⚡ Live Parenting (Modal)
- Enables progressive parenting interactively by selection order.
- Works in Object and Edit Armature modes.
- Parents one by one as you click through the chain.
- Press `Enter` to confirm, `Esc` to cancel and revert changes.
- Appears in:
  - Sidebar panel (Parenting section)
  - Object > Parent menu
  - Recommended to add to Quick Favorites (right-click)

---

## 📊 Addon Layout
- Tools are in the **3D View Sidebar** under the "Infame Rig Tools" tab.
- Tools grouped by section:
  - Renaming Tools
  - Viewport Display
  - Driver Tools
  - Parenting
- Context menu tools are active immediately after installing the addon.
