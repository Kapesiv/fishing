"""
LURELOOM - Sunshore Bay blockout generator.

Builds the first map layout (about 400 x 400 m) from LURELOOM_PRODUCTION_PLAN.md section 7:
  - Sunshore Lake in the middle (shoreline with coves)
  - Sunshore Village on the south shore (tackle shop, 4 cottages, boathouse, warehouse,
    docks, lanterns, barrels, crates, nets, fences, boats)
  - Pinewood Forest around the lake (pines, spruces, bushes, flowers, mossy rocks,
    paths, a viewpoint hill)
  - East cliffs, small islands and the Forgotten Isle (abandoned cabin, broken dock,
    stone circle)

This is a BLOCKOUT: correct scale, layout and colours, with simple stylised shapes.
Final assets (cottage, dock, trees...) replace these one by one later.
Every building, dock, tree and prop is its own object (not one big mesh).
Trees / rocks / props are linked duplicates of prototype meshes kept in "_Prototypes".

Run (from repo root):
  blender -b --python Blender/SunshoreBay/scripts/build_sunshore_bay.py
Outputs:
  Blender/SunshoreBay/SunshoreBay_Blockout.blend
  Blender/SunshoreBay/renders/*.png
Change SEED or the layout constants below and re-run to iterate.
"""
import bpy, bmesh, math, random, os, sys, time
from mathutils import Vector, Matrix, Euler, noise

T0 = time.time()
SEED = 42
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.dirname(SCRIPT_DIR)
RENDER_DIR = os.path.join(OUT_DIR, "renders")
BLEND_PATH = os.path.join(OUT_DIR, "SunshoreBay_Blockout.blend")
DO_RENDER = "--no-render" not in sys.argv
os.makedirs(RENDER_DIR, exist_ok=True)
rng = random.Random(SEED)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0

# ---------------------------------------------------------------- helpers
def C(r, g, b):
    """sRGB-ish 0..1 -> linear."""
    return (r ** 2.2, g ** 2.2, b ** 2.2)

def lerp(a, b, t):
    return a + (b - a) * t

def lerp3(a, b, t):
    return tuple(lerp(a[i], b[i], t) for i in range(3))

def ss(e0, e1, x):
    t = (x - e0) / (e1 - e0)
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)

def angdiff(a, b):
    return (a - b + math.pi) % (2 * math.pi) - math.pi

def fbm(x, y, octaves=4, seed=0):
    s = 0.0; amp = 1.0; f = 1.0; norm = 0.0
    for _ in range(octaves):
        s += amp * noise.noise(Vector((x * f + seed * 13.17, y * f - seed * 7.71, seed * 3.31)))
        norm += amp; amp *= 0.5; f *= 2.0
    return s / norm

def coll(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or scene.collection).children.link(c)
    return c

MATS = {}
def mat(name, col, rough=0.8, emit=0.0, alpha=1.0, metal=0.0):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    m.diffuse_color = (*col, alpha)
    m.roughness = rough
    nt = m.node_tree
    if nt is not None:
        p = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if p is not None:
            p.inputs["Base Color"].default_value = (*col, 1)
            p.inputs["Roughness"].default_value = rough
            p.inputs["Metallic"].default_value = metal
            if emit > 0:
                p.inputs["Emission Color"].default_value = (*col, 1)
                p.inputs["Emission Strength"].default_value = emit
            if alpha < 1:
                p.inputs["Alpha"].default_value = alpha
    if alpha < 1:
        for attr, val in (("surface_render_method", 'BLENDED'), ("blend_method", 'BLEND')):
            try:
                setattr(m, attr, val); break
            except Exception:
                pass
    MATS[name] = m
    return m


class MB:
    """Small bmesh builder: boxes, cones, spheres, prisms with per-part materials."""
    def __init__(self):
        self.bm = bmesh.new(); self.mats = []

    def mi(self, m):
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def _tag(self, verts, m):
        i = self.mi(m); fs = set()
        for v in verts:
            fs.update(v.link_faces)
        for f in fs:
            f.material_index = i

    def _M(self, loc, rot, scale):
        return Matrix.LocRotScale(Vector(loc), Euler(rot), Vector(scale))

    def box(self, loc, size, m, rot=(0, 0, 0)):
        r = bmesh.ops.create_cube(self.bm, size=1.0, matrix=self._M(loc, rot, size))
        self._tag(r['verts'], m); return r['verts']

    def cone(self, loc, r1, r2, depth, m, seg=8, rot=(0, 0, 0), scale=(1, 1, 1)):
        r = bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=seg,
                                  radius1=r1, radius2=r2, depth=depth,
                                  matrix=self._M(loc, rot, scale))
        self._tag(r['verts'], m); return r['verts']

    def ico(self, loc, r, m, sub=1, scale=(1, 1, 1), rot=(0, 0, 0), jitter=0.0, seed=0):
        r_ = bmesh.ops.create_icosphere(self.bm, subdivisions=sub, radius=r,
                                        matrix=self._M(loc, rot, scale))
        if jitter:
            c = Vector(loc)
            for v in r_['verts']:
                d = v.co - c
                if d.length > 1e-6:
                    n = noise.noise(d.normalized() * 1.7 + Vector((seed * 3.1, seed * 1.7, 0)))
                    v.co = c + d * (1 + jitter * n)
        self._tag(r_['verts'], m); return r_['verts']

    def poly(self, pts, faces, mats):
        vs = [self.bm.verts.new(Vector(p)) for p in pts]
        if not isinstance(mats, (list, tuple)):
            mats = [mats] * len(faces)
        for f, m in zip(faces, mats):
            self.bm.faces.new([vs[i] for i in f]).material_index = self.mi(m)

    def prism(self, loc, size, m, rot=(0, 0, 0)):
        """Gable shape, ridge along local X, base at z=0, apex at z=1 (before scale)."""
        M = self._M(loc, rot, size)
        p = [(-.5, -.5, 0), (-.5, .5, 0), (-.5, 0, 1), (.5, -.5, 0), (.5, .5, 0), (.5, 0, 1)]
        self.poly([M @ Vector(q) for q in p],
                  [(0, 2, 1), (3, 4, 5), (0, 3, 5, 2), (1, 2, 5, 4), (0, 1, 4, 3)], m)

    def mesh(self, name):
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces[:])
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me); self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        return me

    def obj(self, name, collection, loc=(0, 0, 0), rot=0.0, tilt=(0, 0)):
        ob = bpy.data.objects.new(name, self.mesh(name))
        ob.location = loc; ob.rotation_euler = (tilt[0], tilt[1], rot)
        collection.objects.link(ob)
        return ob


def inst(me, name, collection, loc, rotz=0.0, scale=1.0, tilt=(0, 0)):
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.rotation_euler = (tilt[0], tilt[1], rotz)
    ob.scale = (scale, scale, scale) if isinstance(scale, (int, float)) else scale
    collection.objects.link(ob)
    return ob


def marker(name, collection, loc, kind='PLAIN_AXES', size=2.0):
    ob = bpy.data.objects.new(name, None)
    ob.empty_display_type = kind; ob.empty_display_size = size
    ob.location = loc
    collection.objects.link(ob)
    return ob

# ---------------------------------------------------------------- palette
M = {
    "wood":       mat("M_Wood", C(.58, .40, .25)),
    "wood_dark":  mat("M_WoodDark", C(.36, .24, .16)),
    "wood_old":   mat("M_WoodWeathered", C(.50, .48, .44), 0.9),
    "stone":      mat("M_Stone", C(.62, .60, .57), 0.9),
    "trim":       mat("M_TrimWhite", C(.95, .93, .88)),
    "glass":      mat("M_WindowGlass", C(.55, .76, .86), 0.15),
    "door":       mat("M_Door", C(.32, .20, .13)),
    "metal":      mat("M_Metal", C(.28, .28, .30), 0.45, metal=0.6),
    "pine_bark":  mat("M_PineBark", C(.66, .38, .22)),
    "bark":       mat("M_Bark", C(.38, .27, .20)),
    "dead_wood":  mat("M_DeadWood", C(.52, .49, .45)),
    "pine_leaf":  mat("M_PineNeedles", C(.20, .44, .24)),
    "spruce_leaf": mat("M_SpruceNeedles", C(.12, .34, .23)),
    "isle_leaf":  mat("M_IsleNeedles", C(.10, .25, .22)),
    "bush":       mat("M_Bush", C(.34, .58, .25)),
    "rock":       mat("M_Rock", C(.70, .69, .66), 0.95),
    "rock_dark":  mat("M_RockDark", C(.45, .47, .50), 0.95),
    "moss":       mat("M_Moss", C(.40, .55, .26)),
    "reed":       mat("M_Reed", C(.64, .66, .38)),
    "cattail":    mat("M_Cattail", C(.40, .26, .16)),
    "flower_w":   mat("M_FlowerWhite", C(.97, .96, .92)),
    "flower_y":   mat("M_FlowerYellow", C(.98, .82, .25)),
    "flower_p":   mat("M_FlowerPink", C(.90, .45, .65)),
    "flower_b":   mat("M_FlowerBlue", C(.45, .55, .95)),
    "grass_tuft": mat("M_GrassTuft", C(.48, .72, .30)),
    "lantern":    mat("M_LanternGlow", C(1.0, .76, .42), 0.5, emit=4.0),
    "myst":       mat("M_MysteryGlow", C(.30, .95, .85), 0.4, emit=3.0),
    "net":        mat("M_FishingNetRope", C(.80, .72, .54), 0.9),
    "float":      mat("M_NetFloatOrange", C(.95, .55, .20), 0.6),
    "mannequin":  mat("M_ScaleMannequin", C(.95, .35, .25), 0.6),
    "buoy_red":   mat("M_BuoyRed", C(.88, .20, .16), 0.5),
    "buoy_white": mat("M_BuoyWhite", C(.96, .96, .94), 0.5),
    "path_dirt":  mat("M_PathDirt", C(.66, .52, .35), 0.95),
    "sign_teal":  mat("M_SignTeal", C(.18, .55, .58)),
    "water":      mat("M_LakeWater", C(.20, .66, .74), 0.05, alpha=0.78),
}
WALLS = {
    "yellow": mat("M_Wall_Yellow", C(.96, .80, .36)),
    "red":    mat("M_Wall_Red", C(.74, .20, .15)),
    "blue":   mat("M_Wall_Blue", C(.32, .50, .74)),
    "mint":   mat("M_Wall_Mint", C(.58, .80, .68)),
    "ochre":  mat("M_Wall_Ochre", C(.88, .66, .30)),
    "steel":  mat("M_Wall_GreyBlue", C(.47, .54, .60)),
    "barn":   mat("M_Wall_BarnRed", C(.56, .16, .12)),
    "aban":   mat("M_Wall_Abandoned", C(.46, .45, .42), 0.95),
}
ROOFS = {
    "red":   mat("M_Roof_Red", C(.68, .20, .16)),
    "slate": mat("M_Roof_Slate", C(.27, .29, .32)),
    "brown": mat("M_Roof_Brown", C(.42, .27, .19)),
    "green": mat("M_Roof_Green", C(.22, .38, .30)),
    "rust":  mat("M_Roof_Rust", C(.58, .32, .19)),
    "aban":  mat("M_Roof_Abandoned", C(.20, .22, .22)),
}

# ---------------------------------------------------------------- terrain shape
MAP = 200.0                      # half size -> 400 x 400 m
LAKE_C = (0.0, 15.0); LAKE_A = 125.0; LAKE_B = 90.0
COVES = [(math.pi - 0.25, 0.12, 0.12),   # west cove
         (0.95, 0.10, 0.10),             # north-east cove
         (-2.15, 0.07, 0.10),            # small south-west bay
         (-math.pi / 2, 0.05, 0.25)]     # village harbour
VIEWPOINT = (-136.0, 124.0)
MEADOW = (88.0, -128.0)
# (x, y, shoreline radius, top height, name)
ISLANDS = [(35.0, 62.0, 18.0, 6.0, "ForgottenIsle"),
           (-72.0, 28.0, 7.0, 2.6, "Isle_West"),
           (78.0, -8.0, 6.0, 2.2, "Isle_East"),
           (-30.0, -38.0, 3.5, 1.3, "Isle_Rock"),
           (58.0, 42.0, 4.5, 1.8, "Isle_NorthEast")]


def lake_d(x, y):
    dx = (x - LAKE_C[0]) / LAKE_A; dy = (y - LAKE_C[1]) / LAKE_B
    th = math.atan2(dy, dx); r = math.hypot(dx, dy)
    k = 1 + 0.07 * math.sin(3 * th + 0.5) + 0.05 * math.sin(5 * th + 1.3) \
        + 0.06 * fbm(math.cos(th) * 2, math.sin(th) * 2, 3, 5)
    for ang, amp, wid in COVES:
        k += amp * math.exp(-(angdiff(th, ang) / wid) ** 2)
    return r / k


def east_w(x, y):
    th = math.atan2((y - LAKE_C[1]) / LAKE_B, (x - LAKE_C[0]) / LAKE_A)
    return math.exp(-(angdiff(th, -0.05) / 0.45) ** 2)


def _shore_south():
    y = LAKE_C[1]
    while lake_d(0.0, y) < 1.0:
        y -= 0.25
    return y

SHORE_Y = _shore_south()          # lake shoreline straight south of centre (village)
STREET_Y = SHORE_Y - 20.0


def village_mask(x, y):
    y0 = SHORE_Y - 8; y1 = SHORE_Y - 62
    # long, soft fall-off behind the village so the land rises gently instead of a wall
    return ss(100, 70, abs(x)) * ss(y0 + 8, y0, y) * ss(y1 - 40, y1, y)


def south_soft(x, y):
    """1 behind the village (south), 0 elsewhere: used to tame hills/ridge there."""
    return ss(SHORE_Y - 40, SHORE_Y - 70, y) * ss(130, 80, abs(x))


def island_h(x, y):
    best = -99.0
    for ix, iy, S, top, _ in ISLANDS:
        r = math.hypot(x - ix, y - iy) * (1 + 0.18 * fbm(x / 9, y / 9, 2, 21))
        rad = S / math.sqrt(math.log((top + 8) / 8) / 2)
        best = max(best, -8 + (top + 8) * math.exp(-2 * (r / rad) ** 2))
    return best


def H(x, y):
    d = lake_d(x, y)
    if d < 1.0:
        h = -7.0 * ss(1.0, 0.62, d)
    else:
        t = d - 1.0
        hill = 0.5 + 0.5 * fbm(x / 70, y / 70, 4, 1)
        h = 1.4 * ss(0, 0.08, t) + 16 * ss(0.08, 0.9, t) * hill
        h += 14 * ss(0.03, 0.12, t) * east_w(x, y)           # east cliffs
        h *= 1 - 0.55 * south_soft(x, y)                     # gentle rolling land behind village
    h += 0.6 * fbm(x / 14, y / 14, 3, 2) * ss(0.98, 1.1, d)
    e = max(abs(x), abs(y)) / MAP                            # framing ridge at map edge
    sw = south_soft(x, y)
    ridge = lerp(28, 14, sw) * ss(lerp(0.78, 0.66, sw), 1.0, e)
    h += ridge * (0.7 + 0.3 * fbm(x / 40, y / 40, 2, 3))
    h += 16 * math.exp(-((x - VIEWPOINT[0]) ** 2 + (y - VIEWPOINT[1]) ** 2) / 28 ** 2)
    m = village_mask(x, y)
    if m > 0:
        target = 1.3 + 0.05 * max(0.0, (SHORE_Y - 6) - y)
        h = h * (1 - m) + target * m
    return max(h, island_h(x, y))


def slope(x, y):
    return math.hypot(H(x + 1, y) - H(x - 1, y), H(x, y + 1) - H(x, y - 1)) / 2


def shore_point(x, y, dx, dy, maxd=200.0):
    """March from land (x,y) along (dx,dy) until reaching water."""
    for _ in range(int(maxd / 0.5)):
        x += dx * 0.5; y += dy * 0.5
        if H(x, y) < 0:
            return x, y
    return x, y


def forest_density(x, y):
    d = lake_d(x, y)
    v = ss(1.06, 1.4, d) * (0.55 + 0.9 * fbm(x / 50, y / 50, 3, 9))
    v *= 1 + 0.35 * ss(-60, -150, x)          # Pinewood Forest is densest in the west
    v *= 1 + 0.25 * ss(90, 150, y)            # and north
    v *= 1 - 0.55 * east_w(x, y)              # cliffs are sparse
    v *= 1 - 0.97 * village_mask(x, y)
    v *= ss(12, 26, math.hypot(x - VIEWPOINT[0], y - VIEWPOINT[1]))
    v *= ss(10, 30, math.hypot(x - MEADOW[0], y - MEADOW[1]))
    return max(0.0, min(0.92, v))


# ---------------------------------------------------------------- collections
ROOT = coll("SunshoreBay")
C_TERRAIN = coll("Terrain", ROOT)
C_WATER = coll("Water", ROOT)
C_VILLAGE = coll("SunshoreVillage", ROOT)
C_VBLD = coll("Village_Buildings", C_VILLAGE)
C_VDOCK = coll("Village_Docks", C_VILLAGE)
C_VPROP = coll("Village_Props", C_VILLAGE)
C_FOREST = coll("PinewoodForest", ROOT)
C_TREES = coll("Trees", C_FOREST)
C_BUSH = coll("Bushes_Flowers", C_FOREST)
C_ROCKS = coll("Rocks", ROOT)
C_REEDS = coll("Reeds", ROOT)
C_PATHS = coll("Paths", ROOT)
C_ISLE = coll("ForgottenIsle", ROOT)
C_ISLANDS = coll("SmallIslands", ROOT)
C_MARK = coll("Markers", ROOT)
C_LIGHT = coll("Lights_Cameras", ROOT)
C_PROTO = coll("_Prototypes")

EXCL = []   # (x, y, r) circles where scatter must not go


def excluded(x, y, pad=0.0):
    for ex, ey, r in EXCL:
        if (x - ex) ** 2 + (y - ey) ** 2 < (r + pad) ** 2:
            return True
    return False


def in_island(x, y, pad=0.0):
    for ix, iy, S, _, _ in ISLANDS:
        if math.hypot(x - ix, y - iy) < S + pad:
            return True
    return False

# ---------------------------------------------------------------- paths (layout)
def catmull(pts, step):
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = [Vector(p) for p in P[i - 1:i + 3]]
        n = max(2, int((p2 - p1).length / step))
        for k in range(n):
            t = k / n; t2 = t * t; t3 = t2 * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(Vector(pts[-1]))
    return out

PATHS = [
    ("PATH_VillageStreet", [(-66, STREET_Y), (-32, STREET_Y + 1), (0, STREET_Y),
                            (32, STREET_Y - 1), (66, STREET_Y)], 4.0, "dirt"),
    ("PATH_WestForest", [(-66, STREET_Y), (-100, STREET_Y + 12), (-138, -45), (-155, 25),
                         (-150, 88), (VIEWPOINT[0], VIEWPOINT[1] - 2)], 2.4, "dirt"),
    ("PATH_EastShore", [(66, STREET_Y), (102, -84), (138, -42), (150, 0)], 2.4, "dirt"),
    ("PATH_NorthLoop", [(-150, 88), (-92, 124), (-22, 130), (58, 126), (118, 96),
                        (148, 42), (150, 0)], 2.2, "dirt"),
    ("PATH_Meadow", [(40, STREET_Y - 1), (66, STREET_Y - 18), (MEADOW[0], MEADOW[1] + 6)], 1.8, "dirt"),
]
PATH_PTS = []    # dense points: (Vector2, half width)
for name, pts, w, kind in PATHS:
    for p in catmull(pts, 1.5):
        PATH_PTS.append((p, w / 2))
PGRID = {}
for p, hw in PATH_PTS:
    PGRID.setdefault((int(math.floor(p.x / 4)), int(math.floor(p.y / 4))), []).append((p.x, p.y, hw))


def path_dist(x, y, search=6.0):
    cx, cy = int(math.floor(x / 4)), int(math.floor(y / 4)); r = int(search / 4) + 1
    best = 99.0
    for i in range(cx - r, cx + r + 1):
        for j in range(cy - r, cy + r + 1):
            for px, py, hw in PGRID.get((i, j), ()):
                d = math.hypot(x - px, y - py) - hw
                if d < best:
                    best = d
    return best

# ---------------------------------------------------------------- terrain mesh
print("[SunshoreBay] terrain ...")
N = 201; STEP = 2 * MAP / (N - 1)
hs = [[H(-MAP + i * STEP, -MAP + j * STEP) for i in range(N)] for j in range(N)]
verts = []; cols = []
SAND = C(.90, .82, .62); GRASS = C(.58, .78, .35); GRASS2 = C(.45, .68, .29)
FORESTF = C(.31, .50, .23); ROCKC = C(.70, .68, .64); BED = C(.62, .66, .50)
DEEP = C(.30, .44, .40); DIRT = C(.66, .52, .35)
for j in range(N):
    for i in range(N):
        x = -MAP + i * STEP; y = -MAP + j * STEP; h = hs[j][i]
        verts.append((x, y, h))
        il, ir = max(0, i - 1), min(N - 1, i + 1); jl, jr = max(0, j - 1), min(N - 1, j + 1)
        sl = math.hypot((hs[j][ir] - hs[j][il]) / ((ir - il) * STEP),
                        (hs[jr][i] - hs[jl][i]) / ((jr - jl) * STEP))
        if h < -0.4:
            c = lerp3(BED, DEEP, ss(-0.4, -6.0, h))
        elif h < 1.1:
            c = lerp3(SAND, GRASS, ss(0.55, 1.1, h))
        else:
            n = 0.5 + 0.5 * fbm(x / 22, y / 22, 3, 4)
            c = lerp3(GRASS, GRASS2, n)
            c = lerp3(c, FORESTF, ss(0.15, 0.6, forest_density(x, y)))
        # bare rock only on real cliffs / very steep ground; ordinary hills stay green
        ew = east_w(x, y) if h > 0 else 0.0
        c = lerp3(c, ROCKC, ss(lerp(0.75, 0.45, ew), lerp(1.2, 0.85, ew), sl))
        if h > -0.3:
            pd = path_dist(x, y, 5.0)
            c = lerp3(c, DIRT, ss(1.2, -0.3, pd))
        cols.extend((*c, 1.0))
faces = [(j * N + i, j * N + i + 1, (j + 1) * N + i + 1, (j + 1) * N + i)
         for j in range(N - 1) for i in range(N - 1)]
me = bpy.data.meshes.new("TERRAIN_SunshoreBay")
me.from_pydata(verts, [], faces); me.update()
ca = me.color_attributes.new("Col", 'FLOAT_COLOR', 'POINT')
ca.data.foreach_set("color", cols)
me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
tm = bpy.data.materials.new("M_Terrain_VertexColor")
tm.diffuse_color = (*C(.50, .70, .33), 1)
try:
    tm.use_nodes = True
except Exception:
    pass
if tm.node_tree is not None:
    nt = tm.node_tree
    p = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    a = nt.nodes.new('ShaderNodeAttribute'); a.attribute_name = "Col"
    nt.links.new(a.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.95
me.materials.append(tm)
terrain = bpy.data.objects.new("TERRAIN_SunshoreBay", me)
C_TERRAIN.objects.link(terrain)

# water
wm = MB()
wm.box((0, 0, 0), (1, 1, 0.0), M["water"])
water_me = bpy.data.meshes.new("WATER_SunshoreLake")
water_me.from_pydata([(-160, -95, 0), (160, -95, 0), (160, 125, 0), (-160, 125, 0)], [], [(0, 1, 2, 3)])
water_me.materials.append(M["water"])
wm.bm.free()
water = bpy.data.objects.new("WATER_SunshoreLake", water_me)
C_WATER.objects.link(water)

# path ribbons (kept as separate objects for Unity reference / splines)
for name, pts, w, kind in PATHS:
    dense = catmull(pts, 1.5)
    vs = []; fs = []
    for k, p in enumerate(dense):
        a_ = dense[max(0, k - 1)]; b_ = dense[min(len(dense) - 1, k + 1)]
        t = (b_ - a_); t = t.normalized() if t.length > 0 else Vector((1, 0))
        n = Vector((-t.y, t.x)) * (w / 2)
        for q in (p - n, p + n):
            vs.append((q.x, q.y, max(H(q.x, q.y), 0.05) + 0.12))
        if k:
            b = 2 * k
            fs.append((b - 2, b - 1, b + 1, b))
    pm = bpy.data.meshes.new(name); pm.from_pydata(vs, [], fs)
    pm.materials.append(M["path_dirt"])
    C_PATHS.objects.link(bpy.data.objects.new(name, pm))

# ---------------------------------------------------------------- prototypes
print("[SunshoreBay] prototypes ...")
PROTO = {}

def keep_proto(me):
    ob = bpy.data.objects.new("PROTO_" + me.name, me)
    C_PROTO.objects.link(ob)
    PROTO[me.name] = me
    return me

def proto_pine(v):
    r = random.Random(100 + v); mb = MB(); h = r.uniform(9.5, 12.5)
    mb.cone((0, 0, h / 2), .38, .18, h, M["pine_bark"], seg=7)
    for i in range(2):  # a couple of bare branch stubs
        a = r.uniform(0, 6.28)
        mb.cone((math.cos(a) * .6, math.sin(a) * .6, h * .55 + i), .07, .03, 1.4, M["pine_bark"], seg=5,
                rot=(0, 1.1, a))
    for i in range(4):
        a = i * 1.7 + v; rr = r.uniform(1.3, 2.0)
        mb.ico((math.cos(a) * 1.3, math.sin(a) * 1.3, h - .9 + r.uniform(-.9, .6)), 1.0, M["pine_leaf"],
               scale=(rr * 1.25, rr * 1.25, rr * .7), jitter=.18, seed=i + v * 10)
    mb.ico((0, 0, h + .3), 1.0, M["pine_leaf"], scale=(1.9, 1.9, 1.1), jitter=.15, seed=v)
    return keep_proto(mb.mesh(f"Pine_{v}"))

def proto_spruce(v, leaf="spruce_leaf"):
    r = random.Random(200 + v); mb = MB(); total = r.uniform(9, 13); n = 5
    mb.cone((0, 0, 1.0), .32, .24, 2.0, M["bark"], seg=7)
    for i in range(n):
        t = i / (n - 1); rad = lerp(2.9, .8, t); dep = lerp(3.8, 2.4, t)
        z = 1.5 + i * (total - 3.5) / (n - 1) + dep / 2
        mb.cone((0, 0, z), rad, .08, dep, M[leaf], seg=9, rot=(0, 0, r.uniform(0, 1)))
    mb.cone((0, 0, total + .2), .45, .02, 1.6, M[leaf], seg=7)
    return keep_proto(mb.mesh(f"Spruce_{leaf}_{v}"))

def proto_dead():
    mb = MB()
    mb.cone((0, 0, 3.5), .3, .1, 7, M["dead_wood"], seg=6)
    for z, a, l in ((3.2, 0.3, 2.2), (4.4, 2.5, 1.8), (5.4, 4.4, 1.4)):
        mb.cone((math.cos(a) * l * .4, math.sin(a) * l * .4, z + .3), .09, .02, l, M["dead_wood"], seg=5,
                rot=(0, 0.95, a))
    return keep_proto(mb.mesh("DeadTree"))

def proto_bush(v):
    r = random.Random(300 + v); mb = MB()
    for i in range(4):
        a = r.uniform(0, 6.28); d = r.uniform(.2, .6); s = r.uniform(.55, .9)
        mb.ico((math.cos(a) * d, math.sin(a) * d, s * .55), s, M["bush"], scale=(1, 1, .8), jitter=.2, seed=i + v)
    return keep_proto(mb.mesh(f"Bush_{v}"))

def proto_rock(v, mossy=False):
    mb = MB()
    mb.ico((0, 0, 0), 1.0, M["rock_dark"] if v % 2 else M["rock"], sub=2,
           scale=(1.3, 1.0, .72), rot=(0, 0, v), jitter=.32, seed=v + 3)
    if mossy:
        mb.ico((0, 0, .42), .95, M["moss"], sub=2, scale=(1.05, .8, .32), jitter=.2, seed=v + 9)
    return keep_proto(mb.mesh(f"Rock_{v}{'_Moss' if mossy else ''}"))

def proto_reeds():
    r = random.Random(400); mb = MB()
    for i in range(16):
        a = r.uniform(0, 6.28); d = r.uniform(0, .8); hgt = r.uniform(2.4, 3.2)
        mb.cone((math.cos(a) * d, math.sin(a) * d, hgt / 2), .04, .006, hgt, M["reed"], seg=4,
                rot=(r.uniform(-.12, .12), r.uniform(-.12, .12), 0))
    for i in range(4):
        a = r.uniform(0, 6.28); d = r.uniform(0, .6)
        mb.cone((math.cos(a) * d, math.sin(a) * d, r.uniform(2.3, 2.8)), .07, .07, .45, M["cattail"], seg=6)
    return keep_proto(mb.mesh("Reeds"))

def proto_flowers(v):
    r = random.Random(500 + v); mb = MB()
    fm = [M["flower_w"], M["flower_y"], M["flower_p"], M["flower_b"]]
    for i in range(10):
        a = r.uniform(0, 6.28); d = r.uniform(0, 1.2)
        mb.cone((math.cos(a) * d, math.sin(a) * d, .2), .12, .01, .4, M["grass_tuft"], seg=4)
    for i in range(9):
        a = r.uniform(0, 6.28); d = r.uniform(0, 1.1)
        mb.ico((math.cos(a) * d, math.sin(a) * d, .38), .09, fm[(i + v) % 4 if i % 3 else v % 4])
    return keep_proto(mb.mesh(f"Flowers_{v}"))

def proto_barrel():
    mb = MB()
    mb.cone((0, 0, .5), .36, .36, 1.0, M["wood"], seg=12)
    mb.cone((0, 0, .5), .4, .4, .5, M["wood"], seg=12)
    for z in (.18, .82):
        mb.cone((0, 0, z), .41, .41, .06, M["metal"], seg=12)
    return keep_proto(mb.mesh("Barrel"))

def proto_crate():
    mb = MB()
    mb.box((0, 0, .4), (.8, .8, .8), M["wood"])
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box((sx * .39, sy * .39, .4), (.07, .07, .82), M["wood_dark"])
    return keep_proto(mb.mesh("Crate"))

def proto_lantern_post():
    mb = MB()
    mb.box((0, 0, 1.3), (.14, .14, 2.6), M["wood_dark"])
    mb.box((.3, 0, 2.55), (.6, .1, .1), M["wood_dark"])
    mb.box((.55, 0, 2.25), (.26, .26, .34), M["lantern"])
    mb.cone((.55, 0, 2.5), .22, .02, .18, M["metal"], seg=4, rot=(0, 0, .785))
    return keep_proto(mb.mesh("LanternPost"))

def proto_fence():
    mb = MB()
    for x in (-1.2, 1.2):
        mb.box((x, 0, .55), (.14, .14, 1.1), M["wood_old"])
    for z in (.45, .85):
        mb.box((0, 0, z), (2.5, .06, .12), M["wood_old"])
    return keep_proto(mb.mesh("FenceSegment"))

def proto_sign():
    mb = MB()
    mb.box((0, 0, 1.2), (.14, .14, 2.4), M["wood_dark"])
    mb.box((.5, 0, 2.0), (1.1, .07, .3), M["wood"], rot=(0, 0, .2))
    mb.box((-.45, 0, 1.6), (1.0, .07, .3), M["wood"], rot=(0, 0, 2.6))
    return keep_proto(mb.mesh("Signpost"))

def proto_netrack():
    """Drying rack with an open rope net (strands, not a solid board) and cork floats."""
    mb = MB(); r = random.Random(600)
    for x in (-1.6, 1.6):
        mb.box((x, 0, 1.1), (.14, .14, 2.2), M["wood"])
    mb.box((0, 0, 2.15), (3.4, .12, .12), M["wood"])
    top, bot = 2.05, 0.55
    for i in range(15):                          # vertical strands, sagging a little
        x = -1.4 + i * 0.2
        mb.box((x, .02 * math.sin(i), (top + bot) / 2), (.025, .025, top - bot), M["net"])
    for k in range(9):                           # horizontal strands, middle ones sag more
        z = top - k * (top - bot) / 8
        sag = 0.12 * math.sin(math.pi * k / 8)
        mb.box((0, .03, z - sag * .5), (2.85, .025, .025), M["net"], rot=(0, 0, 0))
    for i in range(8):                           # floats along the top line
        mb.ico((-1.3 + i * .37, .06, top - .05), .07, M["float"] if i % 2 else M["buoy_white"], sub=1)
    mb.box((0, .05, bot - .05), (2.9, .04, .04), M["net"])
    return keep_proto(mb.mesh("NetRack"))

def proto_buoy():
    mb = MB()
    mb.ico((0, 0, 0), .45, M["buoy_red"], sub=2, scale=(1, 1, .9))
    mb.cone((0, 0, .45), .3, .3, .15, M["buoy_white"], seg=12)
    mb.cone((0, 0, .9), .04, .04, .9, M["metal"], seg=6)
    return keep_proto(mb.mesh("Buoy"))

def proto_boat(name, hull):
    mb = MB()
    secs = [(-1.9, .56), (-1.3, .72), (.2, .76), (1.2, .55), (2.05, .07)]
    pts = []
    for k, (y, w) in enumerate(secs):
        zb = .28 if k == len(secs) - 1 else 0.0
        pts += [(-w, y, .62), (w, y, .62), (w * .55, y, zb), (-w * .55, y, zb)]
    fs = []; ms = []
    for i in range(len(secs) - 1):
        a = 4 * i; b = 4 * (i + 1)
        fs += [(a, a + 3, b + 3, b), (a + 1, b + 1, b + 2, a + 2), (a + 3, a + 2, b + 2, b + 3)]
        ms += [hull, hull, M["wood_dark"]]
    last = 4 * (len(secs) - 1)
    fs += [(0, 1, 2, 3), (last, last + 3, last + 2, last + 1)]; ms += [hull, hull]
    fs.append(tuple([4 * i + 1 for i in range(len(secs))] + [4 * i for i in reversed(range(len(secs)))]))
    ms.append(M["wood"])
    mb.poly(pts, fs, ms)
    for y in (-.8, .5):
        mb.box((0, y, .68), (1.35, .32, .07), M["wood_dark"])
    mb.box((.25, .1, .74), (.08, 2.6, .05), M["wood_old"], rot=(0, 0, .15))   # oar
    return keep_proto(mb.mesh(name))

PINES = [proto_pine(v) for v in range(3)]
SPRUCES = [proto_spruce(v) for v in range(3)]
ISLE_SPRUCE = [proto_spruce(v, "isle_leaf") for v in range(2)]
DEAD = proto_dead()
BUSHES = [proto_bush(v) for v in range(3)]
ROCKS = [proto_rock(v) for v in range(4)]
MOSSROCKS = [proto_rock(v + 10, True) for v in range(2)]
REEDS = proto_reeds()
FLOWERS = [proto_flowers(v) for v in range(4)]
BARREL = proto_barrel(); CRATE = proto_crate(); LANTERN = proto_lantern_post()
FENCE = proto_fence(); SIGN = proto_sign(); NETRACK = proto_netrack(); BUOY = proto_buoy()
BOATS = [proto_boat("Rowboat_Red", mat("M_Boat_Red", C(.80, .25, .18))),
         proto_boat("Rowboat_Blue", mat("M_Boat_Blue", C(.25, .45, .72))),
         proto_boat("Rowboat_Green", mat("M_Boat_Green", C(.30, .58, .42)))]

# ---------------------------------------------------------------- buildings
def window(mb, x, y, z, axis, s=1.0, glass=None):
    glass = glass or M["glass"]
    if axis == 'y':
        mb.box((x, y, z), (s + .28, .16, s + .28), M["trim"])
        mb.box((x, y, z), (s, .2, s), glass)
        mb.box((x, y, z), (.07, .24, s), M["trim"]); mb.box((x, y, z), (s, .24, .07), M["trim"])
    else:
        mb.box((x, y, z), (.16, s + .28, s + .28), M["trim"])
        mb.box((x, y, z), (.2, s, s), glass)
        mb.box((x, y, z), (.24, .07, s), M["trim"]); mb.box((x, y, z), (.24, s, .07), M["trim"])


def house(name, x, y, w, d, h, wall, roof, ridge='x', rot=0.0, chimney=True, rh=None,
          door_x=0.0, sign=None, porch=False, tilt=(0, 0), glass=None, big_door=False, z=None,
          coll_=None, foundation=2.0):
    z0 = H(x, y) if z is None else z
    rh = rh or min(w, d) * 0.42
    oh = 0.45; f = 0.45; mb = MB()
    mb.box((0, 0, (f - foundation) / 2), (w + .2, d + .2, f + foundation), M["stone"])
    mb.box((0, 0, f + h / 2), (w, d, h), wall)
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box((sx * w / 2, sy * d / 2, f + h / 2), (.22, .22, h), M["trim"])
    top = f + h
    if ridge == 'x':
        mb.prism((0, 0, top), (w, d, rh * .98), wall)
        a = math.atan2(rh, d / 2); sw = (d / 2 + oh) / math.cos(a)
        for s in (1, -1):
            mb.box((0, s * math.cos(a) * sw / 2, top + rh - math.sin(a) * sw / 2 + .09),
                   (w + 2 * oh, sw, .18), roof, rot=(-s * a, 0, 0))
        gable_win = [((w / 2 + .02, 0), 'x'), ((-w / 2 - .02, 0), 'x')]
    else:
        mb.prism((0, 0, top), (d, w, rh * .98), wall, rot=(0, 0, math.pi / 2))
        a = math.atan2(rh, w / 2); sw = (w / 2 + oh) / math.cos(a)
        for s in (1, -1):
            mb.box((s * math.cos(a) * sw / 2, 0, top + rh - math.sin(a) * sw / 2 + .09),
                   (sw, d + 2 * oh, .18), roof, rot=(0, s * a, 0))
        gable_win = [((0, d / 2 + .02), 'y'), ((0, -d / 2 - .02), 'y')]
    for (gx, gy), ax in gable_win:
        window(mb, gx, gy, top + rh * .35, ax, .7, glass)
    # door (front = +Y)
    dw, dh = (2.8, 3.0) if big_door else (1.1, 2.1)
    mb.box((door_x, d / 2 + .03, f + dh / 2 + .05), (dw + .3, .1, dh + .25), M["trim"])
    mb.box((door_x, d / 2 + .07, f + dh / 2), (dw, .12, dh), M["door"])
    mb.box((door_x, d / 2 + .55, f / 2 - .25), (dw + .6, .9, f + .5), M["stone"])
    wz = f + h * .55
    for wx in (-w / 4 - .2, w / 4 + .2):
        if abs(wx - door_x) > dw / 2 + .9 and abs(wx) < w / 2 - .7:
            window(mb, wx, d / 2, wz, 'y', 1.0, glass)
    for wx in (-w / 4, w / 4):
        window(mb, wx, -d / 2, wz, 'y', 1.0, glass)
    for sx in (-1, 1):
        window(mb, sx * w / 2, 0, wz, 'x', 1.0, glass)
    if chimney:
        cx, cy = (w * .22, -d * .12) if ridge == 'x' else (w * .12, -d * .22)
        mb.box((cx, cy, top + (rh + .9) / 2), (.7, .7, rh + .9), M["stone"])
    if sign is not None:
        mb.box((door_x, d / 2 + .14, f + h - .4), (min(3.2, w - 1), .1, .75), sign)
        mb.box((door_x, d / 2 + .2, f + h - .4), (1.0, .06, .3), M["trim"])
    if porch:
        mb.box((0, d / 2 + 1.3, f - .08), (w * .85, 2.6, .16), M["wood"])
        for sx in (-1, 1):
            mb.box((sx * w * .4, d / 2 + 2.45, f + 1.25), (.16, .16, 2.5), M["wood_dark"])
        mb.box((0, d / 2 + 1.3, f + 2.55), (w * .9, 2.9, .14), roof, rot=(-.18, 0, 0))
    ob = mb.obj(name, coll_ or C_VBLD, (x, y, z0 - .05), rot, tilt)
    EXCL.append((x, y, max(w, d) * .75 + 2.5))
    return ob


def dock(name, x, y, ang, length, width=2.4, deck_z=1.0, broken=0.0, t_width=0.0,
         coll_=None, wood=None):
    wood = wood or M["wood"]; post = M["wood_dark"] if not broken else M["wood_old"]
    r = random.Random(hash(name) & 0xffff); mb = MB(); pw = .3
    for i in range(int(length / pw)):
        if broken and r.random() < broken:
            continue
        t = (r.uniform(-.05, .05), r.uniform(-.04, .04), r.uniform(-.06, .06)) if broken else (0, 0, r.uniform(-.01, .01))
        mb.box((r.uniform(-.03, .03), i * pw + pw / 2, deck_z - (r.uniform(0, .15) if broken else 0)),
               (width, pw - .04, .09), wood, rot=t)
    for sx in (-1, 1):
        mb.box((sx * (width / 2 - .25), length / 2, deck_z - .14), (.14, length, .18), post)
    k = int(length / 2.6)
    for i in range(k + 1):
        py = min(length - .2, .2 + i * 2.6)
        for sx in (-1, 1):
            lean = (r.uniform(-.15, .15), r.uniform(-.15, .15), 0) if broken else (0, 0, 0)
            mb.box((sx * width / 2, py, (deck_z + .35 - 3.5) / 2), (.22, .22, deck_z + .35 + 3.5), post, rot=lean)
    if t_width:
        tl = 4.2
        for i in range(int(tl / pw)):
            mb.box((0, length + i * pw + pw / 2, deck_z), (t_width, pw - .04, .09), wood)
        for tx in (-t_width / 2, -t_width / 4, t_width / 4, t_width / 2):
            for ty in (length + .2, length + tl - .2):
                mb.box((tx, ty, (deck_z + .35 - 3.5) / 2), (.22, .22, deck_z + .35 + 3.5), post)
        for tx in (-t_width / 2 + .3, t_width / 2 - .3):
            mb.cone((tx, length + tl - .4, deck_z + .3), .15, .15, .6, post, seg=10)
    else:
        for sx in (-1, 1):
            mb.cone((sx * (width / 2 - .2), length - .4, deck_z + .3), .14, .14, .6, post, seg=10)
    mb.obj(name, coll_ or C_VDOCK, (x, y, 0), ang)
    dx, dy = -math.sin(ang), math.cos(ang)
    total = length + (4.2 if t_width else 0)
    for s in range(0, int(total) + 4, 3):
        EXCL.append((x + dx * s, y + dy * s, max(width, t_width) / 2 + 2.5))
    return (x + dx * length, y + dy * length)


print("[SunshoreBay] village ...")
ys = STREET_Y
# Tackle shop: biggest, gable to the street, yellow with sign and porch
house("BLD_TackleShop", 0, ys - 12, 10, 8, 3.6, WALLS["yellow"], ROOFS["red"], ridge='y',
      sign=M["sign_teal"], porch=True, chimney=False)
house("BLD_Cottage_Red", -24, ys - 11, 7, 6, 3.0, WALLS["red"], ROOFS["slate"], ridge='x', door_x=-1.2)
house("BLD_Cottage_Blue", -45, ys - 14, 6.5, 6, 2.8, WALLS["blue"], ROOFS["brown"], ridge='y', rot=.15)
house("BLD_Cottage_Mint", 25, ys - 12, 7.5, 6.5, 3.0, WALLS["mint"], ROOFS["red"], ridge='x', rot=-.08,
      door_x=1.3, porch=True)
house("BLD_Cottage_Ochre", 47, ys - 9, 6, 5.5, 2.7, WALLS["ochre"], ROOFS["green"], ridge='y', rot=-.2)
house("BLD_Warehouse", 62, ys - 30, 12, 9, 4.2, WALLS["steel"], ROOFS["rust"], ridge='y', big_door=True,
      chimney=False, rot=-.1)
bx, by = shore_point(-24, ys, 0, 1)
house("BLD_Boathouse", -24, by + 1.5, 6.5, 10, 3.0, WALLS["barn"], ROOFS["slate"], ridge='y',
      big_door=True, chimney=False, z=0.55, foundation=3.5)

# docks
mx, my = shore_point(0, ys, 0, 1)
main_end = dock("DOCK_Main", 0, my - 4, 0.0, 30, width=2.6, t_width=10)
wx_, wy_ = shore_point(-46, ys, 0, 1)
dock("DOCK_West", -46, wy_ - 3, 0.12, 14)
ex_, ey_ = shore_point(36, ys, 0, 1)
dock("DOCK_East", 36, ey_ - 3, -0.1, 13)

# boardwalk from street to main dock
bw = MB()
for i in range(int((my - 4 - (ys + 2)) / .3)):
    yy = ys + 2 + i * .3 + .15
    bw.box((0, yy, H(0, yy) + .12), (2.4, .26, .08), M["wood"])
bw.obj("PATH_Boardwalk_Dock", C_PATHS)

# props
def P(me, name, x, y, rotz=None, scale=1.0, z=None, c=C_VPROP, tilt=(0, 0)):
    rz = rng.uniform(0, 6.28) if rotz is None else rotz
    return inst(me, name, c, (x, y, H(x, y) if z is None else z), rz, scale, tilt)

k = 0
for i, x in enumerate(range(-56, 60, 16)):
    s = 1 if i % 2 else -1
    P(LANTERN, f"PROP_Lantern_{k:02d}", x, ys + s * 3.0, rotz=(0 if s < 0 else math.pi)); k += 1
for yy in (my + 6, my + 18):
    P(LANTERN, f"PROP_Lantern_{k:02d}", 1.4, yy, rotz=math.pi, z=1.0); k += 1
P(LANTERN, f"PROP_Lantern_{k:02d}", -20, by - 5, rotz=math.pi)
# shop porch / dock clutter
for i, (x, y) in enumerate([(-4.2, ys - 6.6), (-3.4, ys - 6.0), (4.0, ys - 6.4)]):
    P(BARREL, f"PROP_Barrel_{i:02d}", x, y, z=H(0, ys - 12) + .4)
for i, (x, y, z) in enumerate([(3.5, main_end[1] + 2.5, 1.05), (4.2, main_end[1] + 2.0, 1.05),
                               (-3.8, main_end[1] + 3, 1.05)]):
    P(BARREL if i < 2 else CRATE, f"PROP_DockClutter_{i:02d}", x, y, z=z)
for i, (x, y, s) in enumerate([(56, ys - 23, 0), (57.2, ys - 23.2, 0), (56.6, ys - 22.9, .8),
                               (68, ys - 24, 0), (69, ys - 24.5, 0)]):
    P(CRATE, f"PROP_Crate_{i:02d}", x, y, rotz=rng.uniform(-.3, .3), z=H(x, y) + s)
for i, (x, y) in enumerate([(65, ys - 23), (66.2, ys - 22.5), (-28.5, by - 6.5)]):
    P(BARREL, f"PROP_Barrel_W{i:02d}", x, y)
P(NETRACK, "PROP_NetRack_00", -33, by - 4, rotz=.3)
P(NETRACK, "PROP_NetRack_01", 12, my - 6, rotz=-.1)
P(SIGN, "PROP_Signpost_West", -63, ys + 3.5, rotz=.4)
P(SIGN, "PROP_Signpost_East", 63, ys + 3.5, rotz=-.6)
P(SIGN, "PROP_Signpost_North", -150, 86, rotz=1.2)
k = 0
for x0, x1, yy in ((-58, -14, ys - 22), (14, 40, ys - 21)):
    x = x0
    while x < x1:
        if rng.random() > .12:
            P(FENCE, f"PROP_Fence_{k:03d}", x, yy, rotz=rng.uniform(-.04, .04)); k += 1
        x += 2.45
# boats
inst(BOATS[0], "BOAT_Rowboat_Red", C_VPROP, (3.1, my + 12, .05), 0.02)
inst(BOATS[1], "BOAT_Rowboat_Blue", C_VPROP, (-44.5 - 2.2, wy_ + 6, .05), .14)
inst(BOATS[2], "BOAT_Rowboat_Green", C_VPROP, (16, my - 1.5, H(16, my - 1.5) + .05), 1.35, 1.0, (.08, .05))
EXCL += [(-24, ys - 6, 4), (0, ys - 5, 4), (25, ys - 5, 4)]

# viewpoint platform
vz = H(*VIEWPOINT)
vp = MB()
vp.box((0, 0, .5), (6, 6, .25), M["wood"])
for sx in (-1, 1):
    for sy in (-1, 1):
        vp.box((sx * 2.9, sy * 2.9, .2), (.25, .25, 2.4), M["wood_dark"])
for sx in (-1, 1):
    vp.box((sx * 2.9, 0, 1.6), (.1, 6, .1), M["wood_dark"])
vp.box((0, 2.9, 1.6), (6, .1, .1), M["wood_dark"])
vp.box((0, -1.5, .95), (2.4, .45, .1), M["wood"])
vp.obj("STR_ViewpointDeck", C_FOREST, (VIEWPOINT[0], VIEWPOINT[1], vz), -.6)
EXCL.append((VIEWPOINT[0], VIEWPOINT[1], 7))

# ---------------------------------------------------------------- Forgotten Isle
print("[SunshoreBay] Forgotten Isle ...")
fx, fy = ISLANDS[0][0], ISLANDS[0][1]
house("BLD_AbandonedCabin", fx - 3, fy - 3, 6, 5, 2.6, WALLS["aban"], ROOFS["aban"], ridge='x',
      tilt=(.035, -.03), rot=.5, glass=M["myst"], coll_=C_ISLE, chimney=True)
sx_, sy_ = shore_point(fx - 4, fy - 6, 0, -1)
dock("DOCK_ForgottenIsle_Broken", sx_, sy_ + 3, math.pi, 11, width=2.2, deck_z=.85, broken=.28,
     coll_=C_ISLE, wood=M["wood_old"])
inst(LANTERN, "PROP_IsleLantern", C_ISLE, (sx_ + 1.2, sy_ - 7, .85), .4, 1.0, (.06, 0))
# stone circle + obelisk with faint glowing runes
scx, scy = fx + 6, fy + 7
scz = H(scx, scy)
for i in range(7):
    a = i / 7 * 6.283
    st = MB()
    st.ico((0, 0, 1.0), 1.0, M["rock_dark"], sub=1, scale=(.55, .4, 1.4), jitter=.15, seed=i)
    st.obj(f"ISLE_Stone_{i}", C_ISLE, (scx + math.cos(a) * 5, scy + math.sin(a) * 5, H(scx + math.cos(a) * 5, scy + math.sin(a) * 5) - .3),
           a, (rng.uniform(-.12, .12), rng.uniform(-.12, .12)))
ob = MB()
ob.cone((0, 0, 1.8), .55, .25, 3.6, M["rock_dark"], seg=4)
for z in (1.2, 2.0, 2.7):
    ob.box((0, .42 - z * .05, z), (.22, .1, .35), M["myst"])
ob.obj("ISLE_Obelisk", C_ISLE, (scx, scy, scz - .2), .3)
EXCL.append((scx, scy, 7))
rr = random.Random(77)
for i in range(16):
    a = rr.uniform(0, 6.28); d = rr.uniform(4, 15)
    x, y = fx + math.cos(a) * d, fy + math.sin(a) * d
    h = H(x, y)
    if h < 1.0 or excluded(x, y):
        continue
    me_ = DEAD if i % 4 == 0 else ISLE_SPRUCE[i % 2]
    inst(me_, f"TREE_Isle_{i:02d}", C_ISLE, (x, y, h - .3), rr.uniform(0, 6.28), rr.uniform(.7, 1.05),
         (rr.uniform(-.06, .06), rr.uniform(-.06, .06)))

# small islands: classic lake islets with a couple of pines and rocks
for ix, iy, S, top, nm in ISLANDS[1:]:
    rr = random.Random(hash(nm) & 0xffff)
    n = 0 if S < 4 else (1 if S < 5 else 3)
    for i in range(n):
        a = rr.uniform(0, 6.28); d = rr.uniform(0, S * .35)
        x, y = ix + math.cos(a) * d, iy + math.sin(a) * d
        inst(PINES[i % 3], f"TREE_{nm}_{i}", C_ISLANDS, (x, y, H(x, y) - .3), rr.uniform(0, 6.28), rr.uniform(.6, .85))
    for i in range(3 + int(S)):
        a = rr.uniform(0, 6.28); d = S * rr.uniform(.5, 1.05)
        x, y = ix + math.cos(a) * d, iy + math.sin(a) * d
        s = rr.uniform(.6, 1.6)
        inst(ROCKS[i % 4], f"ROCK_{nm}_{i}", C_ISLANDS, (x, y, H(x, y) - s * .3), rr.uniform(0, 6.28), s)

# ---------------------------------------------------------------- scatter
def scatter(spacing, x0, x1, y0, y1, fn, seed):
    r = random.Random(seed); n = 0
    y = y0
    while y < y1:
        x = x0
        while x < x1:
            px = x + r.uniform(-.45, .45) * spacing; py = y + r.uniform(-.45, .45) * spacing
            n += fn(px, py, r)
            x += spacing
        y += spacing
    return n

CNT = {"tree": 0, "bush": 0, "flower": 0, "rock": 0, "reed": 0}

def tree_fn(x, y, r):
    h = H(x, y)
    if h < 1.3 or in_island(x, y, 3) or excluded(x, y) or path_dist(x, y, 8) < 3.8:
        return 0
    p = forest_density(x, y)
    if p <= 0 or r.random() > p or slope(x, y) > 0.95:
        return 0
    d = lake_d(x, y)
    pine_p = .3 + .4 * ss(8, 22, h) + .35 * ss(1.2, 1.05, d) + .3 * east_w(x, y)
    me_ = r.choice(PINES) if r.random() < pine_p else r.choice(SPRUCES)
    CNT["tree"] += 1
    inst(me_, f"TREE_{me_.name}_{CNT['tree']:04d}", C_TREES, (x, y, h - .3), r.uniform(0, 6.28),
         r.uniform(.75, 1.2), (r.uniform(-.04, .04), r.uniform(-.04, .04)))
    return 1

def bush_fn(x, y, r):
    h = H(x, y)
    if h < 1.1 or in_island(x, y, 2) or excluded(x, y) or path_dist(x, y, 4) < 1.0:
        return 0
    fd = forest_density(x, y); vm = village_mask(x, y)
    p = .06 + 1.3 * fd * (1 - fd) * .5 + .25 * vm * (1 - vm) * 4 * .5
    if r.random() > p:
        return 0
    CNT["bush"] += 1
    inst(r.choice(BUSHES), f"BUSH_{CNT['bush']:04d}", C_BUSH, (x, y, h - .15), r.uniform(0, 6.28), r.uniform(.7, 1.4))
    return 1

def flower_fn(x, y, r):
    h = H(x, y)
    if not (1.2 < h < 10) or in_island(x, y, 2) or excluded(x, y) or path_dist(x, y, 3) < .8:
        return 0
    meadow = ss(30, 10, math.hypot(x - MEADOW[0], y - MEADOW[1]))
    p = (.3 * ss(0.05, 0.4, fbm(x / 25, y / 25, 2, 13)) + .55 * meadow) * ss(.3, .05, forest_density(x, y))
    if r.random() > p or slope(x, y) > .45:
        return 0
    CNT["flower"] += 1
    inst(r.choice(FLOWERS), f"FLOWERS_{CNT['flower']:04d}", C_BUSH, (x, y, h - .05), r.uniform(0, 6.28), r.uniform(.8, 1.3))
    return 1

def rock_fn(x, y, r):
    h = H(x, y)
    if in_island(x, y, 2) or excluded(x, y) or path_dist(x, y, 4) < 1.0:
        return 0
    sl = slope(x, y); ew = east_w(x, y); fd = forest_density(x, y)
    if -0.9 < h < 1.3:
        p, s, mossy = .07 * (1 + fbm(x / 15, y / 15, 2, 17)), r.uniform(.5, 1.5), False
    elif ew > .35 and sl > .45 and h > 1:
        p, s, mossy = .45, r.uniform(1.8, 4.5), False
    elif h > 18:
        p, s, mossy = .05, r.uniform(1.2, 3.0), False
    elif fd > .35:
        p, s, mossy = .035, r.uniform(.8, 1.8), True
    else:
        return 0
    if r.random() > p:
        return 0
    CNT["rock"] += 1
    me_ = r.choice(MOSSROCKS) if mossy else r.choice(ROCKS)
    inst(me_, f"ROCK_{CNT['rock']:04d}", C_ROCKS, (x, y, h - s * .3), r.uniform(0, 6.28), s,
         (r.uniform(-.2, .2), r.uniform(-.2, .2)))
    return 1

def reed_fn(x, y, r):
    h = H(x, y)
    if not (-1.4 < h < -0.12) or excluded(x, y, 1.5):
        return 0
    if r.random() > .6 * ss(.0, .3, fbm(x / 18, y / 18, 2, 11)):
        return 0
    CNT["reed"] += 1
    inst(REEDS, f"REEDS_{CNT['reed']:04d}", C_REEDS, (x, y, h), r.uniform(0, 6.28), r.uniform(.75, 1.25))
    return 1

print("[SunshoreBay] scattering forest ...")
scatter(5.5, -196, 196, -196, 196, tree_fn, 1)
scatter(6.0, -196, 196, -196, 196, bush_fn, 2)
scatter(4.5, -196, 196, -196, 196, flower_fn, 3)
scatter(4.0, -196, 196, -196, 196, rock_fn, 4)
scatter(2.6, -165, 165, -100, 130, reed_fn, 5)
# a few hand-placed feature trees inside the village
for i, (x, y) in enumerate([(-12, ys - 18), (13, ys - 20), (-36, ys - 4), (38, ys - 26), (-58, ys - 30)]):
    inst(PINES[i % 3] if i % 2 == 0 else SPRUCES[i % 3], f"TREE_Village_{i}", C_TREES, (x, y, H(x, y) - .3),
         rng.uniform(0, 6.28), rng.uniform(.9, 1.15))

# ---------------------------------------------------------------- markers
marker("MK_PlayerSpawn", C_MARK, (0, ys + 4, H(0, ys + 4) + .1), 'ARROWS', 2)
for nm, (x, y) in {"MK_Zone_SunshoreVillage": (0, ys - 10), "MK_Zone_PinewoodForest": (-150, 20),
                   "MK_Zone_EastCliffs": (150, 0), "MK_Zone_ForgottenIsle": (fx, fy),
                   "MK_Zone_Viewpoint": VIEWPOINT, "MK_Zone_Meadow": MEADOW}.items():
    marker(nm, C_MARK, (x, y, H(x, y) + 3), 'SPHERE', 6)
spots = [(0, main_end[1] + 14), (-108, 18), (96, 8), (32, 40), (-62, 62), (-22, -22), (110, 55)]
k = 0
for x, y in spots:
    if H(x, y) < -1.5:
        marker(f"MK_FishingSpot_{k:02d}", C_MARK, (x, y, 0), 'CIRCLE', 4)
        inst(BUOY, f"PROP_Buoy_{k:02d}", C_VPROP, (x + 3, y, .05), 0, 1.0)
        k += 1

# ---------------------------------------------------------------- light, sky, cameras
w = bpy.data.worlds.new("SkyDay"); scene.world = w
try:
    w.use_nodes = True
except Exception:
    pass
if w.node_tree is not None:
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs[0].default_value = (*C(.62, .80, .98), 1); bg.inputs[1].default_value = 1.1
w.color = C(.62, .80, .98)

def aim(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

sun_d = bpy.data.lights.new("SUN_Day", 'SUN'); sun_d.energy = 4.2; sun_d.color = (1.0, .93, .82)
sun_d.angle = math.radians(2.5)
sun = bpy.data.objects.new("SUN_Day", sun_d); C_LIGHT.objects.link(sun)
sun.location = (0, 0, 100); aim(sun, Vector((0, 0, 100)) - Vector((0.35, -0.55, 0.75)) * 10)

CAMS = {}
def cam(name, loc, target, lens=32, ortho=None):
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.clip_end = 3000
    if ortho:
        cd.type = 'ORTHO'; cd.ortho_scale = ortho
    ob = bpy.data.objects.new(name, cd); ob.location = loc; C_LIGHT.objects.link(ob)
    if target is not None:
        aim(ob, target)
    CAMS[name] = ob
    return ob

# --- 1.8 m scale mannequins (reference only, delete / hide in Unity) ---
def mannequin(name, x, y, z=None, rot=0.0):
    mb = MB()
    mb.cone((0, 0, .45), .11, .1, .9, M["mannequin"], seg=8)            # legs
    mb.cone((0, 0, 1.18), .2, .17, .62, M["mannequin"], seg=10)         # torso
    mb.ico((0, 0, 1.64), .13, M["mannequin"], sub=2, scale=(1, 1, 1.15))  # head (top at ~1.8 m)
    for s in (-1, 1):
        mb.cone((s * .26, 0, 1.12), .05, .04, .62, M["mannequin"], seg=6, rot=(0, s * .12, 0))
    zz = H(x, y) if z is None else z
    return mb.obj(name, C_MARK, (x, y, zz), rot)

mannequin("REF_Human180_Street", 4, ys + 1.5, rot=.4)
mannequin("REF_Human180_Shop", -2.2, ys - 6.8, z=H(0, ys - 12) + .4)
mannequin("REF_Human180_Dock", -.4, main_end[1] - 7, z=1.05, rot=2.8)
mannequin("REF_Human180_Isle", fx - 3.5, fy - 7.5, rot=2.0)
mannequin("REF_Human180_Forest", -146, -10, rot=-.3)

cam("CAM_Overview", (-70, -330, 175), (0, 5, 0), 30)
# --- player eye-height views (1.7 m above ground) ---
EYE = 1.7
cam("CAM_Eye_VillageStreet", (-30, ys + 1.2, H(-30, ys + 1.2) + EYE), (14, ys + 2, H(14, ys) + 2.0), 22)
cam("CAM_Eye_MainDock", (1.0, main_end[1] + 3.0, 1.05 + EYE), (-4, ys - 10, 3.5), 22)
cam("CAM_Eye_DockToLake", (0.0, main_end[1] + 3.5, 1.05 + EYE), (30, 70, 2.5), 22)
# stand on the west forest path and look along it (north) with the lake on the right
_wp = catmull(PATHS[1][1], 1.5)
_i = min(range(len(_wp)), key=lambda k: (_wp[k] - Vector((-146.0, -28.0))).length)
fp = _wp[_i]; fa = _wp[min(len(_wp) - 1, _i + 16)]
cam("CAM_Eye_ForestPath", (fp.x, fp.y, H(fp.x, fp.y) + EYE), (fa.x + 6, fa.y, H(fa.x, fa.y) + 1.2), 22)
# arrive on the Forgotten Isle: stand at the end of the broken dock, look up at the cabin
cam("CAM_Eye_ForgottenIsle", (sx_ + .1, sy_ - 6.5, .85 + EYE), (fx - 3, fy - 2, H(fx - 3, fy - 3) + 1.8), 24)
cam("CAM_Village", (-34, SHORE_Y + 42, 13), (6, ys - 12, 3), 26)
cam("CAM_ForgottenIsle", (8, 18, 6), (fx, fy + 2, 3), 35)
cam("CAM_Top", (0, 0, 400), None, ortho=405)
scene.camera = CAMS["CAM_Overview"]

# hide prototype holder from the view layer (meshes are still used by instances)
try:
    bpy.context.view_layer.layer_collection.children["_Prototypes"].exclude = True
except Exception:
    pass

# viewport: show material colours and look through the overview camera
for scr in bpy.data.screens:
    for area in scr.areas:
        if area.type == 'VIEW_3D':
            for sp in area.spaces:
                if sp.type == 'VIEW_3D':
                    try:
                        sp.shading.type = 'SOLID'; sp.shading.color_type = 'MATERIAL'
                        sp.clip_end = 3000
                        sp.region_3d.view_perspective = 'CAMERA'
                    except Exception:
                        pass

# render settings
for eng in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try:
        scene.render.engine = eng; break
    except Exception:
        pass
try:
    scene.eevee.taa_render_samples = 32
except Exception:
    pass
for look in ('AgX - Medium High Contrast', 'Medium High Contrast'):
    try:
        scene.view_settings.look = look; break
    except Exception:
        pass
scene.render.resolution_x = 1600; scene.render.resolution_y = 900
scene.render.image_settings.file_format = 'PNG'

n_obj = len(bpy.data.objects)
print(f"[SunshoreBay] objects={n_obj} trees={CNT['tree']} bushes={CNT['bush']} flowers={CNT['flower']} "
      f"rocks={CNT['rock']} reeds={CNT['reed']} shoreY={SHORE_Y:.1f} ({time.time() - T0:.1f}s)")

bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH, compress=True)
print("[SunshoreBay] saved", BLEND_PATH)

if DO_RENDER:
    for name in ("CAM_Overview", "CAM_Village", "CAM_ForgottenIsle", "CAM_Eye_VillageStreet",
                 "CAM_Eye_MainDock", "CAM_Eye_DockToLake", "CAM_Eye_ForestPath",
                 "CAM_Eye_ForgottenIsle", "CAM_Top"):
        scene.camera = CAMS[name]
        if name == "CAM_Top":
            scene.render.resolution_x = 1400; scene.render.resolution_y = 1400
        scene.render.filepath = os.path.join(RENDER_DIR, name.replace("CAM_", "SunshoreBay_") + ".png")
        bpy.ops.render.render(write_still=True)
        print("[SunshoreBay] rendered", scene.render.filepath, f"({time.time() - T0:.1f}s)")
    scene.camera = CAMS["CAM_Overview"]
    scene.render.resolution_x = 1600; scene.render.resolution_y = 900
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH, compress=True)
print("[SunshoreBay] done", f"({time.time() - T0:.1f}s)")
