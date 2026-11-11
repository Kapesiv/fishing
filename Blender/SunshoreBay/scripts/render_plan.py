"""
Sunshore Bay - phase A plan check and plan map.

Reads plan/map_plan.json, checks every planned point against the current v2 map
(ground height, water, distance to nearest planned item and to the nearest warning sign)
and renders a numbered top view to renders/v2/SunshoreBay_Plan.png.
Nothing is saved: the .blend stays unchanged.

  blender -b Blender/SunshoreBay/SunshoreBay_Blockout_v2.blend --python Blender/SunshoreBay/scripts/render_plan.py
"""
import bpy, json, math, os
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
plan = json.load(open(os.path.join(ROOT, "plan", "map_plan.json"), encoding="utf-8"))
items = plan["items"]
scene = bpy.context.scene
terrain = bpy.data.objects["TERRAIN_SunshoreBay"]
dg = bpy.context.evaluated_depsgraph_get()


def ground(x, y):
    hit, loc, *_ = terrain.ray_cast(Vector((x, y, 300)), Vector((0, 0, -1)), depsgraph=dg)
    return loc.z if hit else None


# ---- checks
signs = [i for i in items if i["type"] == "sign"]
real = [i for i in items if i["type"] != "night"]
print("PLAN id    z(m)  where   nearest-item  nearest-sign")
for it in items:
    z = ground(it["x"], it["y"])
    where = "water" if z is not None and z < 0 else "land"
    others = [o for o in real if o is not it and o["area"] != "Night hooks"]
    near = min(others, key=lambda o: math.hypot(o["x"] - it["x"], o["y"] - it["y"]))
    dn = math.hypot(near["x"] - it["x"], near["y"] - it["y"])
    ds = ""
    if it["type"] == "sign":
        so = min((s for s in signs if s is not it), key=lambda s: math.hypot(s["x"] - it["x"], s["y"] - it["y"]))
        ds = f"{math.hypot(so['x'] - it['x'], so['y'] - it['y']):.0f} m ({so['id']})"
    print(f"PLAN {it['id']:4s} {z if z is not None else float('nan'):6.1f}  {where:6s}  {dn:5.0f} m ({near['id']})  {ds}")
area_land = 400 * 400 - 28000
pois = [i for i in items if i["status"] != "existing" and i["type"] not in ("night",)]
print(f"PLAN new/changed items: {len(pois)}  land area ~{area_land/1e3:.0f}k m2  -> one item per ~{area_land/len(pois):.0f} m2")

# ---- overlay: numbered discs and labels above the map, viewed from CAM_Top
COL = {"building": (1.0, .75, .2), "structure": (1.0, .75, .2), "props": (.9, .9, .9), "sign": (1.0, .25, .2),
       "note": (1.0, .5, .3), "mystery": (.75, .4, 1.0), "magic": (.3, 1.0, .85), "poi": (.3, .7, 1.0),
       "fishing": (.2, .55, 1.0), "path": (.95, .85, .6), "area": (.3, 1.0, .4), "night": (.35, .35, .45)}
mats = {}
def emit(col):
    if col in mats:
        return mats[col]
    m = bpy.data.materials.new(f"PLAN_{len(mats)}")
    m.use_nodes = True
    bs = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bs.inputs["Base Color"].default_value = (*col, 1); bs.inputs["Emission Color"].default_value = (*col, 1)
    bs.inputs["Emission Strength"].default_value = 1.0
    mats[col] = m
    return m

black = emit((0.02, 0.02, 0.03))
for it in items:
    col = COL.get(it["type"], (1, 1, 1))
    night = it["type"] == "night"
    x, y = it["x"] + (5 if night else 0), it["y"] - (5 if night else 0)      # night hooks sit beside their place
    if it["type"] == "area":
        bpy.ops.mesh.primitive_torus_add(major_radius=16, minor_radius=.9, location=(x, y, 80))
        bpy.context.active_object.data.materials.append(emit(col))
        ly = y + 19
    else:
        r = 1.8 if night else 3.0
        bpy.ops.mesh.primitive_cylinder_add(vertices=28, radius=r + .8, depth=.2, location=(x, y, 79.9))
        bpy.context.active_object.data.materials.append(black)
        bpy.ops.mesh.primitive_cylinder_add(vertices=28, radius=r, depth=.3, location=(x, y, 80))
        bpy.context.active_object.data.materials.append(emit(col))
        ly = y + 5.5
    if night:
        continue
    cu = bpy.data.curves.new(f"PLANLBL_{it['id']}", 'FONT'); cu.body = it["id"]; cu.size = 5.0
    cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    t = bpy.data.objects.new(f"PLANLBL_{it['id']}", cu); scene.collection.objects.link(t)
    t.location = (x, ly, 81); t.data.materials.append(emit((1, 1, 1)))
    tb = bpy.data.objects.new(f"PLANLBLB_{it['id']}", cu.copy()); scene.collection.objects.link(tb)
    tb.location = (x + .45, ly - .45, 80.95); tb.data.materials.append(black)
for q in plan["quiet_zones"]:
    cx, cy = (q["x0"] + q["x1"]) / 2, (q["y0"] + q["y1"]) / 2
    cu = bpy.data.curves.new(f"PLANQ_{q['id']}", 'FONT'); cu.body = f"{q['id']} quiet"; cu.size = 7.0
    cu.align_x = 'CENTER'
    t = bpy.data.objects.new(f"PLANQ_{q['id']}", cu); scene.collection.objects.link(t)
    t.location = (cx, cy, 81); t.data.materials.append(emit((.85, .95, .85)))

scene.camera = bpy.data.objects["CAM_Top"]
scene.view_settings.view_transform = "Standard"
scene.render.resolution_x = 1800; scene.render.resolution_y = 1800
scene.render.filepath = os.path.join(ROOT, "renders", "v2", "SunshoreBay_Plan.png")
bpy.ops.render.render(write_still=True)
print("PLAN rendered", scene.render.filepath)
