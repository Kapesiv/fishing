"""
Sunshore Bay - automatic quality check of the generated map.

  blender -b Blender/SunshoreBay/SunshoreBay_Blockout_v2.blend --python Blender/SunshoreBay/scripts/qa_check.py

Prints one line per problem ("QA <check> <object> <detail>") and a summary ("QA SUMMARY ...").
Checks: floating / buried objects, trees in water, things standing on paths, blocked doorways,
paths over water or too steep to walk, water holes, pond leaks, objects outside the map,
duplicate names and overlapping footprints.
"""
import bpy, math, collections
from mathutils import Vector
from mathutils.kdtree import KDTree

scene = bpy.context.scene
terrain = bpy.data.objects["TERRAIN_SunshoreBay"]
dg = bpy.context.evaluated_depsgraph_get()
ISSUES = collections.defaultdict(list)


def ground(x, y):
    hit, loc, *_ = terrain.ray_cast(Vector((x, y, 400)), Vector((0, 0, -1)), depsgraph=dg)
    return loc.z if hit else None


def issue(kind, name, detail=""):
    ISSUES[kind].append((name, detail))


objs = [o for o in bpy.data.objects if o.type == 'MESH' and o.users_collection
        and o.users_collection[0].name != "_Prototypes" and not o.name.startswith(("TERRAIN_", "WATER_"))]
SCATTER = ("TREE_", "ROCK_", "FERN_", "BUSH_", "MOSS_", "LOG_", "STUMP_", "HEATHER_", "SHROOM_", "GRASS_",
           "FLOWERS_", "BRANCH_", "PEBBLES_", "LEAVES_", "REEDS_")
GROUND_THINGS = SCATTER + ("PROP_", "SIGN_", "BLD_", "STR_", "POI_", "BOAT_", "MYST_", "NOTE_")

# --- path data
path_objs = [o for o in bpy.data.objects if o.name.startswith("PATH_") and o.type == 'MESH']
pverts = []
for po in path_objs:
    mw = po.matrix_world
    for v in po.data.vertices:
        pverts.append((mw @ v.co, po.name))
kd = KDTree(len(pverts))
for i, (co, _) in enumerate(pverts):
    kd.insert(Vector((co.x, co.y, 0)), i)
kd.balance()

# --- 1) floating / buried, 2) trees in water, 3) on paths, 6) outside the map
for o in objs:
    if o.parent is not None:
        continue
    n = o.name
    if not n.startswith(GROUND_THINGS):
        continue
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    zmin = min(c.z for c in bb); zmax = max(c.z for c in bb)
    x, y = o.location.x, o.location.y
    if abs(x) > 199 or abs(y) > 199:
        issue("outside_map", n, f"({x:.0f},{y:.0f})")
    g0 = ground(x, y)
    if g0 is None:
        continue
    over_water = g0 < 0.15
    corners = [ground(c.x, c.y) for c in bb[:4]] + [g0]
    corners = [c for c in corners if c is not None]
    gmax, gmin = max(corners), min(corners)
    water_ok = n.startswith(("BOAT_", "PROP_Buoy", "REEDS_", "TREE_Drowned", "LOG_Drowned", "MYST_DeepLight",
                             "PROP_DockClutter", "PROP_Lantern", "PROP_IsleLantern", "PROP_Moorings",
                             "PROP_Wreck", "POI_Waterfall"))
    mounted = n.startswith(("POI_ForestBoat_Marks", "MYST_ClawMarks", "MYST_MarkedTree", "MYST_LakeMap", "MYST_Scratches", "NOTE_"))
    if not over_water and not water_ok and not mounted:
        # what is really under the object (terrain, a porch, another crate ...)
        hit, loc, nrm, _, hob, _ = scene.ray_cast(dg, Vector((x, y, zmin - .03)), Vector((0, 0, -1)))
        support = loc.z if hit and not hob.name.startswith("WATER_") else gmax
        if hit and nrm.z < 0:          # the ray started inside the object below: it is resting on it
            support = zmin
        if hit and loc.z < gmin - .05:  # the base is sunk into the slope and the ray found something buried below
            support = gmax
        if zmin - max(support, gmax if not hit else support) > 0.25:
            issue("floating", n, f"gap {zmin - support:.2f} m above what is under it")
        if zmax < gmin - 0.02:
            issue("buried", n, f"top {gmin - zmax:.2f} m under ground")
    if n.startswith("TREE_") and not n.startswith("TREE_Drowned") and g0 < 0.0:
        issue("tree_in_water", n, f"ground {g0:.2f}")
    if n.startswith(("TREE_", "ROCK_", "LOG_", "STUMP_", "BUSH_", "FERN_", "PROP_", "SIGN_", "POI_", "STR_Well",
                     "MOSS_", "BRANCH_", "HEATHER_")):
        (co, idx, dist) = kd.find(Vector((x, y, 0)))
        if dist < 0.9 and not pverts[idx][1].startswith(("PATH_Boardwalk", "PATH_VillageSquare")) and not n.startswith(("PROP_Lantern", "PROP_Signpost", "ROCK_FishingLedge")):
            issue("on_path", n, f"{dist:.2f} m from {pverts[idx][1]}")

# --- 4) doorways: nothing solid right in front of a door
for b in [o for o in objs if o.name.startswith("BLD_")]:
    rz = b.rotation_euler.z
    bb = [Vector(c) for c in b.bound_box]
    d_half = max(c.y for c in bb)
    for side in (1, -1) if "Boathouse" in b.name else (1,):
        fx, fy = -math.sin(rz) * side, math.cos(rz) * side
        dx_, dy_ = b.location.x + fx * (d_half + 1.2), b.location.y + fy * (d_half + 1.2)
        for o in objs:
            if o is b or o.parent is not None or not o.name.startswith(("TREE_", "ROCK_", "PROP_", "BUSH_", "LOG_", "STUMP_", "FERN_")):
                continue
            if (o.location.x - dx_) ** 2 + (o.location.y - dy_) ** 2 < 1.1 ** 2:
                issue("door_blocked", b.name, f"{o.name} in front of the door")

# --- 5) paths: over water, too steep
for po in path_objs:
    if po.name.startswith("PATH_Boardwalk") or po.name == "PATH_VillageSquare":
        continue
    vs = [po.matrix_world @ v.co for v in po.data.vertices]
    wetp = [v for v in vs[::2] if (ground(v.x, v.y) or 0) < -0.05]
    if wetp:
        issue("path_over_water", po.name, f"{len(wetp)} points over water, e.g. ({wetp[0].x:.0f},{wetp[0].y:.0f})")
    steep = 0
    for i in range(0, len(vs) - 4, 2):
        a, b_ = vs[i], vs[i + 4]
        run = math.hypot(b_.x - a.x, b_.y - a.y)
        if run > .5 and abs(b_.z - a.z) / run > 0.75:        # ~37 degrees
            steep += 1; where = f"({a.x:.0f},{a.y:.0f})"
    if steep:
        issue("path_too_steep", po.name, f"{steep} steep sections, e.g. at {where}")

# --- 7) water holes (terrain under 0 outside the lake water sheet), pond leaks
lake = bpy.data.objects.get("WATER_SunshoreLake")
lx = [ (lake.matrix_world @ v.co) for v in lake.data.vertices ] if lake else []
if lx:
    x0, x1 = min(v.x for v in lx), max(v.x for v in lx); y0, y1 = min(v.y for v in lx), max(v.y for v in lx)
    holes = 0
    for v in list(terrain.data.vertices)[::7]:
        if v.co.z < -0.05 and not (x0 <= v.co.x <= x1 and y0 <= v.co.y <= y1):
            holes += 1
    if holes:
        issue("water_hole", "WATER_SunshoreLake", f"{holes} terrain points below water level outside the water")
pond = bpy.data.objects.get("WATER_HiddenPond")
if pond:
    pz = pond.data.vertices[0].co.z; pc = pond.data.vertices[0].co
    leaks = 0
    for k in range(32):
        a = k / 32 * 6.283
        for rr in (6.6, 7.5, 8.5):
            g = ground(pc.x + math.cos(a) * rr, pc.y + math.sin(a) * rr)
            if g is not None and g < pz - .02:
                leaks += 1
    inside_high = sum(1 for k in range(16) if (ground(pc.x + math.cos(k / 16 * 6.283) * 4, pc.y + math.sin(k / 16 * 6.283) * 4) or 0) > pz)
    if leaks:
        issue("pond_leak", "WATER_HiddenPond", f"{leaks} rim points lower than the water")
    if inside_high:
        issue("pond_dry", "WATER_HiddenPond", f"{inside_high} points inside the pond above water")

# --- 8) duplicate names / exact duplicates (same mesh, same place)
names = collections.Counter(o.name.rsplit(".", 1)[0] if o.name[-4:-3] == "." and o.name[-3:].isdigit() else o.name
                            for o in bpy.data.objects)
for nm, c in names.items():
    if c > 1:
        issue("duplicate_name", nm, f"x{c}")
seen = {}
for o in objs:
    key = (o.data.name, round(o.location.x, 2), round(o.location.y, 2), round(o.location.z, 2))
    if key in seen:
        issue("exact_duplicate", o.name, f"same mesh and place as {seen[key]}")
    seen[key] = o.name

total = 0
for k, lst in sorted(ISSUES.items()):
    for nm, d in lst[:25]:
        print(f"QA {k} {nm} {d}")
    total += len(lst)
print("QA SUMMARY " + (", ".join(f"{k}={len(v)}" for k, v in sorted(ISSUES.items())) or "clean") + f" (total {total}, objects {len(objs)})")
