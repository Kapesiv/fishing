"""
LURELOOM - Sunshore Bay blockout generator, layout v2.

v1 (straight village, regular lake) is kept in versions/v1/ and SunshoreBay_Blockout.blend.
v2 changes (see LAYOUT_V2.md):
  - Organic fishing village: building clusters with varied facing, a small village square,
    winding street and lanes, a creek with a wooden bridge, gentle terraces.
  - Lake with a more natural shoreline: extra coves and headlands, asymmetric islands.
  - Forest: dark-fantasy trees (Gloom Spruce, Crooked Pine, Ashen Birch, snags, logs, stumps,
    ferns, heather, glowing mushrooms) placed by site conditions with no overlaps; groves, glades,
    varied path edges, open shore views.
  - Forgotten Isle: hooked island with a ridge, a sheltered cove, cabin terrace, stone circle and obelisk.
  - Less empty lawn: knolls, outcrops, tall grass, birches at the village edges.

Run headless (from repo root):
  blender -b --python Blender/SunshoreBay/scripts/build_sunshore_bay.py [-- --no-render]
Run inside an open Blender (e.g. via BlenderMCP): exec the file; it clears the scene,
saves a backup of the open file first, builds the map live and saves the v2 .blend.
Outputs: SunshoreBay_Blockout_v2.blend, renders/v2/*.png
"""
import bpy, bmesh, math, random, os, sys, time, json
from mathutils import Vector, Matrix, Euler, noise

VERSION = "v2"
T0 = time.time()
SEED = 42
GUI = not bpy.app.background
try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = r"C:\Users\kappu\fishing\Blender\SunshoreBay\scripts"
OUT_DIR = os.path.dirname(SCRIPT_DIR)
RENDER_DIR = os.path.join(OUT_DIR, "renders", VERSION)
BLEND_PATH = os.path.join(OUT_DIR, f"SunshoreBay_Blockout_{VERSION}.blend")
DO_RENDER = (not GUI) and "--no-render" not in sys.argv
os.makedirs(RENDER_DIR, exist_ok=True)
rng = random.Random(SEED)


def progress(msg):
    print(f"[SunshoreBay {VERSION}] {msg} ({time.time() - T0:.1f}s)")
    if GUI:
        try:
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        except Exception:
            pass


if GUI:
    if bpy.data.filepath:
        try:
            bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, "_backup_before_v2.blend"), copy=True)
        except Exception as e:
            print("backup failed:", e)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for ids in (bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.cameras,
                bpy.data.lights, bpy.data.worlds):
        bpy.data.batch_remove(list(ids))
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0

# ---------------------------------------------------------------- helpers
def C(r, g, b):
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

def face(x, y, tx, ty):
    """Z rotation so that an object's local +Y (front) points from (x,y) toward (tx,ty)."""
    return math.atan2(-(tx - x), (ty - y))

def l2w(cx, cy, rot, lx, ly):
    c, s = math.cos(rot), math.sin(rot)
    return cx + lx * c - ly * s, cy + lx * s + ly * c

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

class Grid:
    """Spatial hash of dense polyline points for fast 'distance to path' queries."""
    def __init__(self, cell=4.0):
        self.cell = cell; self.g = {}
    def add(self, p, hw):
        k = (int(math.floor(p.x / self.cell)), int(math.floor(p.y / self.cell)))
        self.g.setdefault(k, []).append((p.x, p.y, hw))
    def dist(self, x, y, search=6.0):
        cx, cy = int(math.floor(x / self.cell)), int(math.floor(y / self.cell))
        r = int(search / self.cell) + 1; best = 99.0
        for i in range(cx - r, cx + r + 1):
            for j in range(cy - r, cy + r + 1):
                for px, py, hw in self.g.get((i, j), ()):
                    d = math.hypot(x - px, y - py) - hw
                    if d < best:
                        best = d
        return best

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

    def cone_dir(self, base, d, length, r1, r2, m, seg=8):
        d = Vector(d).normalized()
        rot = d.to_track_quat('Z', 'Y').to_euler()
        return self.cone(Vector(base) + d * (length / 2), r1, r2, length, m, seg, tuple(rot))

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
        M_ = self._M(loc, rot, size)
        p = [(-.5, -.5, 0), (-.5, .5, 0), (-.5, 0, 1), (.5, -.5, 0), (.5, .5, 0), (.5, 0, 1)]
        self.poly([M_ @ Vector(q) for q in p],
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
    "square":     mat("M_SquareStone", C(.80, .75, .66), 0.9),
    "trim":       mat("M_TrimWhite", C(.95, .93, .88)),
    "glass":      mat("M_WindowGlass", C(.55, .76, .86), 0.15),
    "door":       mat("M_Door", C(.32, .20, .13)),
    "metal":      mat("M_Metal", C(.28, .28, .30), 0.45, metal=0.6),
    "pine_bark":  mat("M_PineBark", C(.66, .38, .22)),
    "bark":       mat("M_Bark", C(.38, .27, .20)),
    "birch_bark": mat("M_BirchBark", C(.93, .91, .86)),
    "birch_mark": mat("M_BirchMarks", C(.22, .21, .20)),
    "dead_wood":  mat("M_DeadWood", C(.52, .49, .45)),
    "pine_leaf":  mat("M_PineNeedles", C(.20, .44, .24)),
    "pine_leaf2": mat("M_PineNeedlesWarm", C(.27, .48, .22)),
    "spruce_leaf": mat("M_SpruceNeedles", C(.12, .34, .23)),
    "spruce_leaf2": mat("M_SpruceNeedlesBlue", C(.14, .32, .29)),
    "birch_leaf": mat("M_BirchLeaves", C(.56, .76, .32)),
    "birch_leaf2": mat("M_BirchLeavesYellow", C(.70, .78, .32)),
    "isle_leaf":  mat("M_IsleNeedles", C(.10, .25, .22)),
    # dark-fantasy vegetation palette
    "gs_dark":    mat("M_GloomSpruce_Dark", C(.11, .22, .20), 0.9),
    "gs_mid":     mat("M_GloomSpruce_Mid", C(.15, .28, .23), 0.9),
    "gs_isle":    mat("M_GloomSpruce_Isle", C(.07, .15, .15), 0.9),
    "gs_isle2":   mat("M_GloomSpruce_Isle2", C(.10, .19, .18), 0.9),
    "gs_bark":    mat("M_GloomSpruce_Bark", C(.22, .18, .16)),
    "cp_bark":    mat("M_CrookedPine_Bark", C(.40, .26, .20)),
    "cp_pad":     mat("M_CrookedPine_Needles", C(.19, .31, .21), 0.9),
    "cp_pad2":    mat("M_CrookedPine_Needles2", C(.23, .35, .21), 0.9),
    "ab_bark":    mat("M_AshenBirch_Bark", C(.78, .76, .72)),
    "ab_mark":    mat("M_AshenBirch_Marks", C(.14, .13, .13)),
    "ab_leaf":    mat("M_AshenBirch_Olive", C(.50, .52, .28), 0.85),
    "ab_leaf2":   mat("M_AshenBirch_Amber", C(.64, .47, .22), 0.85),
    "ab_leaf3":   mat("M_AshenBirch_Pale", C(.42, .49, .30), 0.85),
    "snag":       mat("M_Snag_Grey", C(.46, .44, .41), 0.95),
    "log_end":    mat("M_Log_EndGrain", C(.62, .50, .36)),
    "fern":       mat("M_Fern", C(.24, .38, .20), 0.85),
    "fern2":      mat("M_FernDark", C(.18, .30, .18), 0.85),
    "shrub":      mat("M_ThornShrub", C(.19, .30, .20), 0.9),
    "twig":       mat("M_ThornTwig", C(.20, .15, .13)),
    "heather":    mat("M_Heather", C(.33, .25, .35), 0.9),
    "heather_f":  mat("M_HeatherFlower", C(.55, .40, .58), 0.9),
    "flower_v":   mat("M_FlowerPaleViolet", C(.70, .64, .82)),
    "shroom_st":  mat("M_MushroomStem", C(.86, .83, .76)),
    "moss_dark":  mat("M_MossDark", C(.26, .38, .20), 0.95),
    "rug":        mat("M_Rug", C(.55, .22, .18), 0.95),
    "blueberry_leaf": mat("M_BlueberryLeaf", C(.26, .42, .20), 0.9),
    "blueberry":  mat("M_Blueberry", C(.18, .20, .45), 0.5),
    "lily":       mat("M_LilyPad", C(.22, .40, .20), 0.4),
    "wicker":     mat("M_Wicker", C(.62, .48, .30), 0.9),
    "mud":        mat("M_Mud", C(.30, .25, .19), 0.95),
    "shutter_green": mat("M_Shutter_Green", C(.22, .40, .28)),
    "shutter_blue": mat("M_Shutter_Blue", C(.25, .38, .55)),
    "shutter_red": mat("M_Shutter_Red", C(.60, .20, .16)),
    "soil":       mat("M_GardenSoil", C(.33, .25, .18), 0.95),
    "blanket":    mat("M_Blanket", C(.30, .38, .55), 0.95),
    "moss_glow":  mat("M_MossGlow", C(.30, .62, .48), 0.9, emit=0.35),
    "leaf_brown": mat("M_LeafBrown", C(.45, .30, .18), 0.9),
    "leaf_red":   mat("M_LeafRust", C(.55, .22, .15), 0.9),
    "deep_glow":  mat("M_DeepGlow", C(.35, .95, .80), 0.4, emit=4.0),
    "bush":       mat("M_Bush", C(.34, .58, .25)),
    "bush2":      mat("M_BushDark", C(.24, .46, .22)),
    "rock":       mat("M_Rock", C(.57, .53, .47), 0.95),
    "rock_dark":  mat("M_RockDark", C(.40, .38, .35), 0.95),
    "moss":       mat("M_Moss", C(.40, .55, .26)),
    "reed":       mat("M_Reed", C(.64, .66, .38)),
    "cattail":    mat("M_Cattail", C(.40, .26, .16)),
    "tallgrass":  mat("M_TallGrass", C(.50, .58, .32)),
    "flower_w":   mat("M_FlowerWhite", C(.97, .96, .92)),
    "flower_y":   mat("M_FlowerYellow", C(.98, .82, .25)),
    "flower_p":   mat("M_FlowerPink", C(.90, .45, .65)),
    "flower_b":   mat("M_FlowerBlue", C(.45, .55, .95)),
    "grass_tuft": mat("M_GrassTuft", C(.48, .72, .30)),
    "lantern":    mat("M_LanternGlow", C(1.0, .76, .42), 0.5, emit=4.0),
    "myst":       mat("M_MysteryGlow", C(.30, .95, .85), 0.4, emit=3.0),
    "myst_soft":  mat("M_MysteryGlowSoft", C(.30, .95, .85), 0.4, emit=1.2),
    "net":        mat("M_FishingNetRope", C(.80, .72, .54), 0.9),
    "net_tar":    mat("M_FishingNet_Tarred", C(.26, .25, .19), 0.95, alpha=0.55),
    "float":      mat("M_NetFloatOrange", C(.95, .55, .20), 0.6),
    "mannequin":  mat("M_ScaleMannequin", C(.95, .35, .25), 0.6),
    "buoy_red":   mat("M_BuoyRed", C(.88, .20, .16), 0.5),
    "buoy_white": mat("M_BuoyWhite", C(.96, .96, .94), 0.5),
    "path_dirt":  mat("M_PathDirt", C(.66, .52, .35), 0.95),
    "path_stone": mat("M_PathStone", C(.58, .58, .56), 0.95),
    "sign_teal":  mat("M_SignTeal", C(.18, .55, .58)),
    "water":      mat("M_LakeWater", C(.20, .66, .74), 0.05, alpha=0.78),
    "creek":      mat("M_CreekWater", C(.16, .36, .38), 0.05, alpha=0.85),
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
# (angle, amplitude, width): positive = cove (lake reaches further), negative = headland
COVES = [(math.pi - 0.25, 0.13, 0.11),   # west cove (reeds)
         (math.pi + 0.35, -0.10, 0.07),  # south-west headland
         (2.35, -0.13, 0.07),            # Pinewood Point (north-west headland)
         (1.75, 0.09, 0.06),             # north bay
         (0.95, 0.11, 0.09),             # north-east cove
         (0.35, -0.08, 0.06),            # point below the east cliffs
         (-0.55, 0.10, 0.08),            # south-east cove
         (-1.05, -0.09, 0.06),           # harbour point east of the village
         (-2.15, 0.08, 0.09),            # small south-west bay
         (-math.pi / 2, 0.05, 0.22)]     # village harbour
VIEWPOINT = (-136.0, 124.0)
MEADOW = (88.0, -128.0)
GLADES = [(-60, 118, 12), (100, 112, 13), (-168, -75, 12), (128, -118, 14), (-20, -160, 15),
          (-150, -112, 16), (-128, -22, 7)]          # last two: Ancient Grove, abandoned camp
POND = (160.0, 24.0)                                 # hidden pond on the east cliff plateau
POND_Z = None

# Forgotten Isle: local frame (u along the long axis, v across), see forgotten_h()
FI = (32.0, 60.0); FI_ANG = 0.5
_ca, _sa = math.cos(FI_ANG), math.sin(FI_ANG)
def isle_local(x, y):
    dx, dy = x - FI[0], y - FI[1]
    return dx * _ca + dy * _sa, -dx * _sa + dy * _ca
def isle_world(u, v):
    return FI[0] + u * _ca - v * _sa, FI[1] + u * _sa + v * _ca
ISLE_SOUTH = (_sa, -_ca)          # world direction of local -v (toward the cove)

# small islands: name, x, y, shore radius, top, elongation, angle, lobes (lu, lv, size factor, top)
SMALL_ISLES = [("Isle_West", -70.0, 30.0, 7.5, 2.6, 1.9, -0.4, [(6, 1, .55, 2.0)]),
               ("Isle_East", 80.0, -6.0, 6.0, 2.4, 1.4, 1.1, [(-4, 3, .6, 1.8)]),
               ("Isle_Rock", -30.0, -40.0, 3.5, 1.6, 1.6, 0.2, []),
               ("Isle_NorthEast", 60.0, 40.0, 4.5, 2.0, 2.3, -0.9, [(3, -2, .5, 1.2)]),
               # skerries: tiny bare rock islets
               ("Skerry_1", -98.0, -8.0, 2.6, 1.0, 1.6, 0.7, []),
               ("Skerry_2", -45.0, 72.0, 2.2, 0.9, 1.3, -0.3, []),
               ("Skerry_3", 92.0, 38.0, 2.4, 1.1, 1.8, 1.2, [(2.5, 1, .5, .7)]),
               ("Skerry_4", 68.0, -40.0, 2.0, 0.8, 1.4, 0.2, [])]
ISLAND_DISCS = [(FI[0], FI[1], 30.0)] + [(x, y, S * el + 2) for _, x, y, S, _, el, _, _ in SMALL_ISLES]


def lake_d(x, y):
    dx = (x - LAKE_C[0]) / LAKE_A; dy = (y - LAKE_C[1]) / LAKE_B
    th = math.atan2(dy, dx); r = math.hypot(dx, dy)
    k = 1 + 0.07 * math.sin(3 * th + 0.5) + 0.05 * math.sin(5 * th + 1.3) + 0.03 * math.sin(7 * th + 2.1) \
        + 0.08 * fbm(math.cos(th) * 3, math.sin(th) * 3, 4, 5)
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

SHORE_Y = _shore_south()
SY = SHORE_Y
SQ = (4.0, SY - 15.0)              # village square centre
SQ_H = 1.8


def village_mask(x, y):
    y0 = SY - 8; y1 = SY - 62
    return ss(100, 70, abs(x)) * ss(y0 + 8, y0, y) * ss(y1 - 40, y1, y)


def south_soft(x, y):
    return ss(SY - 40, SY - 70, y) * ss(130, 80, abs(x))


def mound(r, S, top):
    rad = S / math.sqrt(math.log((top + 8) / 8) / 2)
    return -8 + (top + 8) * math.exp(-2 * (r / rad) ** 2)


def small_isle_h(x, y):
    best = -99.0
    for _, ix, iy, S, top, el, ang, lobes in SMALL_ISLES:
        dx, dy = x - ix, y - iy
        if abs(dx) > 30 or abs(dy) > 30:
            continue
        c, s = math.cos(ang), math.sin(ang)
        u = dx * c + dy * s; v = -dx * s + dy * c
        n = 1 + 0.28 * fbm(x / 8, y / 8, 3, 21)
        best = max(best, mound(math.hypot(u / el, v) * n, S, top))
        for lu, lv, f, ltop in lobes:
            best = max(best, mound(math.hypot((u - lu) / (el * .8), v - lv) * n, S * f, ltop))
    return best


def forgotten_h(x, y):
    u, v = isle_local(x, y)
    if abs(u) > 60 or abs(v) > 45:
        return -99.0
    n = 1 + 0.22 * fbm(x / 7, y / 7, 3, 31)
    h = mound(math.hypot(u / 1.7, v) * n, 16, 4.0)                 # main body
    h = max(h, mound(math.hypot((u - 15) / 1.25, v + 7) * n, 7, 2.8))   # east arm hooking south
    h = max(h, mound(math.hypot((u + 17) / 1.3, v - 2) * n, 8, 3.2))    # west lobe
    h -= 6.5 * math.exp(-(((u - 5) / 6.5) ** 2 + ((v + 13) / 5) ** 2))  # sheltered south cove
    land = ss(-1.0, 2.0, h)
    h += 8.5 * math.exp(-((v - 6) / 3.2) ** 2) * ss(-21, -9, u) * ss(12, 3, u) * land  # north ridge
    h += 2.5 * math.exp(-((u + 5) ** 2 + (v - 7) ** 2) / 14) * land                   # summit
    if h > 0:
        # gentle ramp from the broken dock up to the cabin door
        ax_, ay_, bx_, by_ = 5.5, -7.8, 6.0, -5.2
        t = max(0.0, min(1.0, ((u - ax_) * (bx_ - ax_) + (v - ay_) * (by_ - ay_)) / ((bx_ - ax_) ** 2 + (by_ - ay_) ** 2)))
        dseg = math.hypot(u - (ax_ + t * (bx_ - ax_)), v - (ay_ + t * (by_ - ay_)))
        h = lerp(h, lerp(1.0, 2.8, t), ss(2.8, 1.2, dseg))
        h = lerp(h, 2.8, ss(7.5, 4.5, math.hypot(u - 7, v + 2)))      # cabin terrace
        h = lerp(h, 3.2, ss(5.5, 3.5, math.hypot(u + 15, v + 1)))     # stone circle plateau
    return h


# creek from the southern hills into the lake west of the village
CREEK = [(-72, -178), (-80, -150), (-70, SY - 50), (-64, SY - 30), (-60, SY - 12), (-57, SY + 4)]
CREEK_D = catmull(CREEK, 1.5)
CGRID = Grid()
for p in CREEK_D:
    CGRID.add(p, 0.0)


def H(x, y):
    d = lake_d(x, y)
    if d < 1.0:
        h = -7.0 * ss(1.0, 0.62, d)
    else:
        t = d - 1.0
        hill = 0.5 + 0.5 * fbm(x / 70, y / 70, 4, 1)
        h = 1.4 * ss(0, 0.08, t) + 16 * ss(0.08, 0.9, t) * hill
        h += 14 * ss(0.03, 0.12, t) * east_w(x, y)
        h *= 1 - 0.55 * south_soft(x, y)
        h += 2.5 * max(0.0, fbm(x / 35, y / 35, 3, 71) - 0.15) * ss(1.1, 1.3, d)   # knolls
        h += .35 * fbm(x / 6, y / 6, 2, 72) * ss(1.12, 1.35, d) * (1 - village_mask(x, y))   # uneven forest floor
    h += 0.6 * fbm(x / 14, y / 14, 3, 2) * ss(0.98, 1.1, d)
    e = max(abs(x), abs(y)) / MAP
    sw = south_soft(x, y)
    h += lerp(28, 14, sw) * ss(lerp(0.78, 0.66, sw), 1.0, e) * (0.7 + 0.3 * fbm(x / 40, y / 40, 2, 3))
    h += 16 * math.exp(-((x - VIEWPOINT[0]) ** 2 + (y - VIEWPOINT[1]) ** 2) / 28 ** 2)
    if POND_Z is not None:
        pdp = math.hypot(x - POND[0], y - POND[1])
        if pdp < 6.3:
            target = POND_Z - .3 - 1.1 * ss(5.8, 2.0, pdp)
            h = min(h, lerp(target, h, ss(5.6, 6.3, pdp)))
    m = village_mask(x, y)
    if m > 0:
        target = 1.3 + 0.05 * max(0.0, (SY - 6) - y) + 1.4 * ss(SY - 30, SY - 42, y) \
            + 0.45 * fbm(x / 25, y / 25, 2, 41)
        h = h * (1 - m) + target * m
    sq = ss(13, 8, math.hypot(x - SQ[0], y - SQ[1]))
    if sq > 0:
        h = lerp(h, SQ_H, sq)
    if h > -0.5:
        dc = CGRID.dist(x, y, 6)
        if dc < 5:
            h -= 1.3 * ss(4.5, 1.2, dc)
    return max(h, small_isle_h(x, y), forgotten_h(x, y))


POND_Z = min(H(POND[0] + math.cos(a) * rr, POND[1] + math.sin(a) * rr)
             for rr in (6.5, 7.5, 8.5) for a in [k / 24 * 2 * math.pi for k in range(24)]) - .3


def slope(x, y):
    return math.hypot(H(x + 1, y) - H(x - 1, y), H(x, y + 1) - H(x, y - 1)) / 2


def shore_point(x, y, dx, dy, maxd=200.0):
    for _ in range(int(maxd / 0.5)):
        x += dx * 0.5; y += dy * 0.5
        if H(x, y) < 0:
            return x, y
    return x, y


def in_island(x, y, pad=0.0):
    for ix, iy, R in ISLAND_DISCS:
        if math.hypot(x - ix, y - iy) < R + pad:
            return True
    return False


def village_core(x, y):
    """Tighter village footprint than village_mask (which also shapes the terrain far south)."""
    return ss(85, 65, abs(x)) * ss(SY, SY - 8, y) * ss(SY - 80, SY - 60, y)


def forest_density(x, y):
    d = lake_d(x, y)
    n = fbm(x / 50, y / 50, 3, 9)
    base = max(ss(1.05, 1.35, d),
               0.6 * ss(0.2, 0.5, fbm(x / 28, y / 28, 2, 99)) * ss(1.03, 1.09, d))   # shore groves
    v = base * ss(-0.35, 0.25, n) * (0.8 + 0.4 * fbm(x / 17, y / 17, 2, 19))
    v *= 1 + 0.35 * ss(-60, -150, x)
    v *= 1 + 0.25 * ss(90, 150, y)
    v *= 1 - 0.55 * east_w(x, y)
    v *= 1 - 0.85 * village_core(x, y)
    v *= ss(12, 26, math.hypot(x - VIEWPOINT[0], y - VIEWPOINT[1]))
    v *= ss(10, 30, math.hypot(x - MEADOW[0], y - MEADOW[1]))
    for gx, gy, gr in GLADES:
        v *= ss(gr * 0.6, gr * 1.25, math.hypot(x - gx, y - gy))
    if d < 1.14:
        v *= 0.7                       # keep the views over the lake open along the shore
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

EXCL = []


class Occ:
    """Footprint registry: every placed object reserves a circle, so nothing overlaps."""
    def __init__(self, cell, maxr):
        self.cell = cell; self.maxr = maxr; self.g = {}

    def free(self, x, y, r):
        c = self.cell; cx, cy = int(math.floor(x / c)), int(math.floor(y / c))
        n = int((r + self.maxr) / c) + 1
        for i in range(cx - n, cx + n + 1):
            for j in range(cy - n, cy + n + 1):
                for px, py, pr in self.g.get((i, j), ()):
                    if (x - px) ** 2 + (y - py) ** 2 < (r + pr) ** 2:
                        return False
        return True

    def add(self, x, y, r):
        c = self.cell
        self.g.setdefault((int(math.floor(x / c)), int(math.floor(y / c))), []).append((x, y, r))


CANOPY = Occ(6.0, 4.5)     # tree crowns: trees keep natural spacing
GROUND = Occ(3.0, 4.0)     # trunks, rocks, logs, props, undergrowth: no two things in the same spot


def forest_cover(x, y):
    return ss(0.12, 0.45, forest_density(x, y))


def site(x, y, h):
    """Site conditions -> (lake distance, slope, moisture 0..1, dryness 0..1.5)."""
    d = lake_d(x, y); sl = slope(x, y); cd = CGRID.dist(x, y, 10)
    moist = min(1.0, max(ss(1.25, 1.02, d), ss(9, 1.5, cd)) + .4 * ss(10, 2, h))
    dry = min(1.5, ss(8, 22, h) + ss(.35, .8, sl) + .8 * east_w(x, y) * ss(1.0, 1.2, d))
    return d, sl, moist, dry


def lean_tilt(x, y, rotz, d, kind):
    """Small natural lean: downhill, and shore pines reach out over the water."""
    gx = (H(x + 1, y) - H(x - 1, y)) / 2; gy = (H(x, y + 1) - H(x, y - 1)) / 2
    dx, dy = -gx * .06, -gy * .06
    if kind == "P" and d < 1.08:
        lx, ly = LAKE_C[0] - x, LAKE_C[1] - y; L = math.hypot(lx, ly) or 1
        dx += lx / L * .14; dy += ly / L * .14
    m = math.hypot(dx, dy)
    if m > .18:
        dx, dy = dx / m * .18, dy / m * .18
    c, s = math.cos(-rotz), math.sin(-rotz)
    ux, uy = dx * c - dy * s, dx * s + dy * c
    return (-uy, ux)

def excluded(x, y, pad=0.0):
    for ex, ey, r in EXCL:
        if (x - ex) ** 2 + (y - ey) ** 2 < (r + pad) ** 2:
            return True
    return False

# ---------------------------------------------------------------- paths (layout)
STREET = [(-74, SY - 30), (-52, SY - 21), (-30, SY - 25), (-12, SY - 19), (SQ[0] - 3, SQ[1] - 2),
          (SQ[0] + 6, SQ[1] - 3), (20, SY - 21), (38, SY - 28), (56, SY - 27), (76, SY - 35)]
ISLE_STEPS = [isle_world(u, v) for u, v in ((5.5, -7.0), (6, -6.0), (5, -5.2), (2, -3), (-6, 0), (-14, -1))]
PATHS = [
    ("PATH_VillageStreet", STREET, 3.4, "dirt"),
    ("PATH_HillLane", [(-12, SY - 19), (-18, SY - 30), (-30, SY - 37), (-44, SY - 37)], 2.0, "dirt"),
    ("PATH_HarbourLane", [(-30, SY - 25), (-36, SY - 19), (-32, SY - 8), (-27, SY - 3)], 2.0, "dirt"),
    ("PATH_EastLane", [(38, SY - 28), (45, SY - 18), (38, SY - 7)], 2.0, "dirt"),
    ("PATH_WestForest", [(-74, SY - 30), (-90, SY - 24), (-104, SY - 10), (-122, -62), (-138, -45),
                         (-150, -12), (-155, 25), (-146, 58), (-150, 88),
                         (VIEWPOINT[0], VIEWPOINT[1] - 2)], 2.4, "dirt"),
    ("PATH_EastShore", [(76, SY - 35), (92, -102), (108, -80), (126, -66), (138, -42), (148, -20),
                        (156, 2)], 2.4, "dirt"),
    ("PATH_NorthLoop", [(-150, 88), (-120, 110), (-92, 124), (-55, 121), (-22, 130), (18, 124),
                        (58, 126), (92, 116), (118, 96), (140, 70), (153, 40), (156, 2)], 2.2, "dirt"),
    ("PATH_Meadow", [(38, SY - 28), (56, SY - 40), (72, -122), (MEADOW[0], MEADOW[1] + 6)], 1.8, "dirt"),
    ("PATH_CampTrail", [(-150, -12), (-140, -16), (-131, -21)], 1.2, "dirt"),
    ("PATH_GroveTrail", [(-122, -62), (-131, -76), (-138, -88), (-146, -100), (-149, -106)], 1.4, "dirt"),
    ("PATH_HiddenCoveTrail", [(92, 116), (89, 109), (85, 103), (82, 99)], 1.1, "dirt"),
    ("PATH_CliffShore", [(112, -75), (110, -60), (104, -44), (103, -28), (105, -14), (114, -2), (128, 6),
                         (138, 9)], 1.4, "dirt"),
    ("PATH_ForgottenIsle_Steps", ISLE_STEPS, 1.6, "stone"),
]
def landify(pts, toward_centre=None, min_h=.35):
    """Push path points out of the water: away from the lake, or toward an island centre."""
    out = []
    for p in catmull(pts, 4.0):
        x, y = p.x, p.y
        cx, cy = toward_centre if toward_centre else LAKE_C
        dx, dy = x - cx, y - cy; L = math.hypot(dx, dy) or 1.0
        sgn = -1 if toward_centre else 1
        k = 0
        while H(x, y) < min_h and k < 80:
            x += sgn * dx / L * .4; y += sgn * dy / L * .4; k += 1
        out.append((x, y))
    return out


PATHS = [(n, landify(p, FI if n.startswith("PATH_ForgottenIsle") else None), w, k) for n, p, w, k in PATHS]
PGRID = Grid()
for _, pts, w, _k in PATHS:
    for p in catmull(pts, 1.5):
        PGRID.add(p, w / 2)

def path_dist(x, y, search=6.0):
    return PGRID.dist(x, y, search)

# ---------------------------------------------------------------- terrain mesh
progress("terrain")
N = 201; STEP = 2 * MAP / (N - 1)
hs = [[H(-MAP + i * STEP, -MAP + j * STEP) for i in range(N)] for j in range(N)]
verts = []; cols = []
SAND = C(.86, .79, .62); GRASS = C(.50, .66, .34); GRASS2 = C(.40, .56, .29); GRASSY = C(.60, .64, .36)
FORESTF = C(.22, .33, .20); ROCKC = C(.66, .65, .62); BED = C(.58, .62, .50)
DEEP = C(.30, .44, .40); DIRT = C(.66, .52, .35); SQUAREC = C(.74, .69, .60)
MOSSF = C(.30, .44, .21); NEEDLE = C(.36, .30, .21); DRYG = C(.64, .62, .36); SOIL = C(.45, .36, .25)
ISLEG = C(.34, .46, .33); ISLEROCK = C(.48, .50, .52); MUD = C(.52, .48, .36)
for j in range(N):
    for i in range(N):
        x = -MAP + i * STEP; y = -MAP + j * STEP; h = hs[j][i]
        verts.append((x, y, h))
        il, ir = max(0, i - 1), min(N - 1, i + 1); jl, jr = max(0, j - 1), min(N - 1, j + 1)
        sl = math.hypot((hs[j][ir] - hs[j][il]) / ((ir - il) * STEP),
                        (hs[jr][i] - hs[jl][i]) / ((jr - jl) * STEP))
        u, v = isle_local(x, y)
        isle = ss(1.15, 0.95, math.hypot(u / 32, v / 20))
        if h < -0.4:
            c = lerp3(BED, DEEP, ss(-0.4, -6.0, h))
        elif h < 1.1:
            c = lerp3(SAND, GRASS, ss(0.55, 1.1, h))
        else:
            c = lerp3(GRASS, GRASS2, 0.5 + 0.5 * fbm(x / 22, y / 22, 3, 4))
            c = lerp3(c, GRASSY, 0.6 * ss(0.3, 0.6, fbm(x / 40, y / 40, 2, 81)))
            fd_ = forest_density(x, y)
            c = lerp3(c, FORESTF, ss(0.15, 0.6, fd_))
            c = lerp3(c, MOSSF, ss(.1, .5, fbm(x / 9, y / 9, 2, 83)) * ss(.3, .7, fd_) * .7)
            c = lerp3(c, NEEDLE, ss(.15, .55, fbm(x / 13, y / 13, 2, 84)) * ss(.4, .8, fd_) * .6)
            c = lerp3(c, DRYG, ss(.25, .6, fbm(x / 17, y / 17, 2, 85)) * ss(.3, .05, fd_) * .5)
            c = lerp3(c, SOIL, ss(.45, .7, fbm(x / 7, y / 7, 2, 86)) * ss(.3, .05, fd_) * .55)
        if isle > 0 and h > -0.3:
            c = lerp3(c, ISLEG, isle * 0.85)
        ew = east_w(x, y) if h > 0 else 0.0
        rock_t = ss(lerp(0.75, 0.45, max(ew, isle)), lerp(1.2, 0.85, max(ew, isle)), sl)
        c = lerp3(c, ISLEROCK if isle > 0.5 else ROCKC, rock_t)
        if h > -0.3:
            c = lerp3(c, MUD, ss(3.0, 1.0, CGRID.dist(x, y, 5)))
            c = lerp3(c, DIRT, ss(1.2, -0.3, path_dist(x, y, 5.0)))
            c = lerp3(c, SQUAREC, ss(10.5, 9.0, math.hypot(x - SQ[0], y - SQ[1])))
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

progress("dark lake water")
MYST_POS = (-38.0, 38.0)          # where the faint light glows far below the surface
WS = 2.5; wx0, wx1, wy0, wy1 = -165.0, 165.0, -100.0, 130.0
nx = int((wx1 - wx0) / WS) + 1; ny = int((wy1 - wy0) / WS) + 1
wv = []; wdep = []; wglow = []
for j in range(ny):
    for i in range(nx):
        x = wx0 + i * WS; y = wy0 + j * WS
        dep = ss(0.0, -6.5, H(x, y))
        g = math.exp(-(((x - MYST_POS[0]) ** 2 + (y - MYST_POS[1]) ** 2) / 6.0 ** 2))
        calm = 1 - .85 * math.exp(-(((x - MYST_POS[0]) ** 2 + (y - MYST_POS[1]) ** 2) / 14.0 ** 2))
        amp = (.04 + .10 * dep) * calm          # swells grow in open water; eerily still above the light
        z = amp * (math.sin(x * .11 + y * .05) + .6 * math.sin(-x * .07 + y * .13 + 1.3)
                   + .35 * math.sin(x * .23 - y * .19 + 2.1))
        wv.append((x, y, z)); wdep.extend((dep, dep, dep, 1.0)); wglow.extend((g, g, g, 1.0))
wf = [(j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i)
      for j in range(ny - 1) for i in range(nx - 1)]
water_me = bpy.data.meshes.new("WATER_SunshoreLake")
water_me.from_pydata(wv, [], wf); water_me.update()
water_me.color_attributes.new("Depth", 'FLOAT_COLOR', 'POINT').data.foreach_set("color", wdep)
water_me.color_attributes.new("Glow", 'FLOAT_COLOR', 'POINT').data.foreach_set("color", wglow)
water_me.polygons.foreach_set("use_smooth", [True] * len(water_me.polygons))
wmat = M["water"]
wmat.diffuse_color = (*C(.06, .14, .17), .9)
nt = wmat.node_tree
if nt is not None:
    N = nt.nodes; Lk = nt.links
    bsdf = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    at = N.new('ShaderNodeAttribute'); at.attribute_name = "Depth"
    ramp = N.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = (*C(.24, .36, .31), 1)
    ramp.color_ramp.elements[1].position = 0.7; ramp.color_ramp.elements[1].color = (*C(.03, .08, .11), 1)
    Lk.new(at.outputs['Fac'], ramp.inputs['Fac']); Lk.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    mr = N.new('ShaderNodeMapRange')
    mr.inputs['To Min'].default_value = .72; mr.inputs['To Max'].default_value = .97
    Lk.new(at.outputs['Fac'], mr.inputs['Value']); Lk.new(mr.outputs['Result'], bsdf.inputs['Alpha'])
    tc = N.new('ShaderNodeTexCoord')
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = .35; nz.inputs['Detail'].default_value = 6
    wvn = N.new('ShaderNodeTexWave'); wvn.inputs['Scale'].default_value = .08; wvn.inputs['Distortion'].default_value = 6
    Lk.new(tc.outputs['Object'], nz.inputs['Vector']); Lk.new(tc.outputs['Object'], wvn.inputs['Vector'])
    add = N.new('ShaderNodeMath'); add.operation = 'ADD'
    Lk.new(nz.outputs['Fac'], add.inputs[0]); Lk.new(wvn.outputs['Fac'], add.inputs[1])
    bump = N.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = .3
    Lk.new(add.outputs['Value'], bump.inputs['Height']); Lk.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = .06
    ag = N.new('ShaderNodeAttribute'); ag.attribute_name = "Glow"
    gm = N.new('ShaderNodeMath'); gm.operation = 'MULTIPLY'; gm.inputs[1].default_value = .3
    Lk.new(ag.outputs['Fac'], gm.inputs[0])
    bsdf.inputs['Emission Color'].default_value = (*C(.30, .90, .78), 1)
    Lk.new(gm.outputs['Value'], bsdf.inputs['Emission Strength'])
water_me.materials.append(wmat)
C_WATER.objects.link(bpy.data.objects.new("WATER_SunshoreLake", water_me))


def ribbon(name, dense, w, material, collection, lift=0.12, flat_z=None):
    vs = []; fs = []
    for k, p in enumerate(dense):
        a_ = dense[max(0, k - 1)]; b_ = dense[min(len(dense) - 1, k + 1)]
        t = (b_ - a_); t = t.normalized() if t.length > 0 else Vector((1, 0))
        n = Vector((-t.y, t.x)) * (w / 2)
        zc = flat_z(p) if flat_z else None
        for q in (p - n, p + n):
            z = zc if zc is not None else max(H(q.x, q.y), 0.05) + lift
            vs.append((q.x, q.y, z))
        if k:
            b = 2 * k
            fs.append((b - 2, b - 1, b + 1, b))
    pm = bpy.data.meshes.new(name); pm.from_pydata(vs, [], fs)
    pm.materials.append(material)
    ob = bpy.data.objects.new(name, pm); collection.objects.link(ob)
    return ob

for name, pts, w, kind in PATHS:
    ribbon(name, catmull(pts, 1.5), w, M["path_stone"] if kind == "stone" else M["path_dirt"], C_PATHS)
ribbon("WATER_Creek", CREEK_D, 2.4, M["creek"], C_WATER,
       flat_z=lambda p: max(H(p.x, p.y) + 0.35, 0.03))

# village square paving disc that follows the ground
sv = [(SQ[0], SQ[1], H(*SQ) + 0.1)]; sf = []
RINGS, SEG = 3, 28
for ri in range(1, RINGS + 1):
    rr = 9.5 * ri / RINGS
    for k in range(SEG):
        a = k / SEG * 2 * math.pi
        x, y = SQ[0] + math.cos(a) * rr, SQ[1] + math.sin(a) * rr
        sv.append((x, y, H(x, y) + 0.1))
for k in range(SEG):
    sf.append((0, 1 + k, 1 + (k + 1) % SEG))
for ri in range(1, RINGS):
    b0 = 1 + (ri - 1) * SEG; b1 = 1 + ri * SEG
    for k in range(SEG):
        k2 = (k + 1) % SEG
        sf.append((b0 + k, b1 + k, b1 + k2, b0 + k2))
sqm = bpy.data.meshes.new("PATH_VillageSquare"); sqm.from_pydata(sv, [], sf)
sqm.materials.append(M["square"])
C_PATHS.objects.link(bpy.data.objects.new("PATH_VillageSquare", sqm))
EXCL.append((SQ[0], SQ[1], 10.5))
progress("terrain, water, paths ready")

# ---------------------------------------------------------------- prototypes
PROTO = {}

def keep_proto(me):
    ob = bpy.data.objects.new("PROTO_" + me.name, me)
    C_PROTO.objects.link(ob)
    PROTO[me.name] = me
    return me

def star_skirt(mb, cx, cy, z_top, z_tip, R, K, rot, m, r, inner=0.48, jit=0.12):
    """One drooping, star-shaped foliage layer: the branch tips hang below the layer top."""
    pts = [(cx, cy, z_top)]
    hgt = z_top - z_tip
    for k in range(K):
        a = rot + k * 2 * math.pi / K
        rr = R * (1 + r.uniform(-jit, jit))
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a), z_tip + r.uniform(-jit, jit) * hgt))
        a2 = a + math.pi / K
        pts.append((cx + R * inner * math.cos(a2), cy + R * inner * math.sin(a2), z_tip + hgt * 0.5))
    uc = len(pts)
    pts.append((cx, cy, z_tip + hgt * 0.22))
    faces = []
    for k in range(K):
        t = 1 + 2 * k; i = t + 1; tn = 1 + 2 * ((k + 1) % K)
        faces += [(0, t, i), (0, i, tn), (t, uc, i), (i, uc, tn)]
    mb.poly(pts, faces, m)


def proto_gloom_spruce(v, dark, mid, young=False, tag="GloomSpruce"):
    """Tall, narrow dark spruce made of drooping star-shaped tiers."""
    r = random.Random(1000 + v * 7 + (500 if young else 0)); mb = MB()
    Ht = r.uniform(2.6, 4.5) if young else r.uniform(11.0, 18.0)
    sc = Ht / 15.0
    baseR = r.uniform(.9, 1.3) if young else r.uniform(2.0, 2.7) * sc
    mb.cone((0, 0, Ht * .42), .28 * sc + .05, .05, Ht * .84, M["gs_bark"], seg=6)
    n = r.randint(4, 5) if young else r.randint(9, 12)
    z0 = Ht * (.18 if young else .2)
    for i in range(n):
        t = i / (n - 1)
        R = baseR * (1 - t) ** .9 + (.12 if young else .18 * sc)
        z_tip = z0 + t * (Ht - z0 - (.4 if young else 1.0))
        th = lerp(2.3, 1.1, t) * (.35 if young else sc)
        star_skirt(mb, r.uniform(-.06, .06), r.uniform(-.06, .06), z_tip + th, z_tip - th * .25, R,
                   r.choice((7, 8, 9)), r.uniform(0, 6.28), dark if t < .55 else mid, r)
    ts = max(sc, .4)
    mb.cone((0, 0, Ht + .3 * ts), .22 * ts, .01, 1.8 * ts, mid, seg=5)
    name = f"{tag}_{'Young_' if young else ''}{v}"
    return keep_proto(mb.mesh(name))


def proto_crooked_pine(v):
    """Old pine: slightly bent trunk, bare lower part, a broad irregular crown of layered needle pads."""
    r = random.Random(1100 + v * 13); mb = MB()
    Ht = r.uniform(10.0, 15.0); sc = Ht / 12
    p = Vector((0, 0, -.3)); d = Vector((0, 0, 1)); rad = .36 * sc
    trunk = []; L = Ht / 5
    for i in range(5):
        d = (d + Vector((r.uniform(-.16, .16), r.uniform(-.16, .16), 0))).normalized()
        if d.z < .9:
            hz = math.sqrt(1 - .9 ** 2); hl = math.hypot(d.x, d.y) or 1
            d = Vector((d.x / hl * hz, d.y / hl * hz, .9))
        mb.cone_dir(p, d, L * 1.04, rad, rad * .86, M["cp_bark"], seg=7)
        trunk.append((p.copy(), d.copy())); p = p + d * L; rad *= .86
    pad = M["cp_pad2"] if v % 2 else M["cp_pad"]
    top = p

    def needle_pad(c, R):
        for k, (dz0, dz1, f) in enumerate(((-.35, .45, 1.0), (.15, .85, .78), (.6, 1.2, .5))):
            star_skirt(mb, c.x + r.uniform(-.15, .15), c.y + r.uniform(-.15, .15), c.z + dz1, c.z + dz0,
                       R * f, 8, r.uniform(0, 6.28), pad, r, inner=.6, jit=.14)

    needle_pad(top, r.uniform(1.8, 2.4) * sc)
    for j in range(r.randint(5, 7)):           # crown pads spread around the upper trunk
        a = j * (6.283 / 6) + r.uniform(-.5, .5)
        base = trunk[r.choice((3, 3, 4))][0] + trunk[3][1] * r.uniform(0, L)
        e = r.uniform(.25, .6); armL = r.uniform(1.4, 2.6) * sc
        ad = Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e)))
        mb.cone_dir(base, ad, armL, rad * 1.5 + .05, rad * .7, M["cp_bark"], seg=5)
        needle_pad(base + ad * armL, r.uniform(1.3, 1.9) * sc)
    for j in range(r.randint(2, 4)):            # dry stubs on the bare lower trunk
        q = trunk[r.randint(0, 2)][0] + Vector((0, 0, r.uniform(.5, 1.5)))
        a = r.uniform(0, 6.28)
        mb.cone_dir(q, (math.cos(a), math.sin(a), r.uniform(-.1, .3)), r.uniform(.6, 1.3), .07, .02, M["snag"], seg=4)
    return keep_proto(mb.mesh(f"CrookedPine_{v}"))


def proto_ashen_birch(v):
    """Slender pale birch with an oval crown of drooping olive foliage (amber in one variant)."""
    r = random.Random(1200 + v * 17); mb = MB()
    Ht = r.uniform(8.0, 12.0)
    leaf = (M["ab_leaf"], M["ab_leaf3"], M["ab_leaf2"], M["ab_leaf"], M["ab_leaf3"])[v % 5]
    p = Vector((0, 0, -.2)); d = Vector((r.uniform(-.08, .08), r.uniform(-.08, .08), 1)).normalized(); rad = .17
    segs = []
    for i in range(3):
        d = (d + Vector((r.uniform(-.08, .08), r.uniform(-.08, .08), 0))).normalized()
        L = Ht / 3
        mb.cone_dir(p, d, L * 1.03, rad, rad * .78, M["ab_bark"], seg=7)
        for k in range(3):
            q = p + d * (L * r.uniform(.1, .9)); az = r.uniform(0, 6.28)
            mb.box((q.x + math.cos(az) * rad * .95, q.y + math.sin(az) * rad * .95, q.z), (.04, .16, .1),
                   M["ab_mark"], rot=(0, 0, az))
        segs.append((p.copy(), d.copy(), L)); p = p + d * L; rad *= .78
    top = p

    def droop(c, R):
        star_skirt(mb, c.x, c.y, c.z + .6, c.z - .75, R, 7, r.uniform(0, 6.28), leaf, r, inner=.62, jit=.12)

    droop(top + Vector((0, 0, .1)), r.uniform(1.3, 1.7))
    n = r.randint(7, 9)
    for j in range(n):                          # oval crown over the top ~40 % of the tree
        a = j / n * 6.283 + r.uniform(-.3, .3); t = r.uniform(0, 1)
        c = top + Vector((math.cos(a) * lerp(.4, 1.5, math.sin(t * math.pi)),
                          math.sin(a) * lerp(.4, 1.5, math.sin(t * math.pi)), -t * Ht * .38))
        mb.cone_dir(top - Vector((0, 0, t * Ht * .38)), c - (top - Vector((0, 0, t * Ht * .38))),
                    max(.3, (c - top).length * .8), .05, .02, M["ab_bark"], seg=4)
        droop(c, r.uniform(1.0, 1.5))
    return keep_proto(mb.mesh(f"AshenBirch_{v}"))


def proto_snag(v):
    """Dead standing tree with a broken top."""
    r = random.Random(1300 + v); mb = MB(); Ht = r.uniform(5, 9)
    p = Vector((0, 0, -.2)); d = Vector((0, 0, 1)); rad = .32
    for i in range(2):
        d = (d + Vector((r.uniform(-.15, .15), r.uniform(-.15, .15), 0))).normalized()
        mb.cone_dir(p, d, Ht / 2, rad, rad * .7, M["snag"], seg=6); p = p + d * (Ht / 2); rad *= .7
    mb.cone_dir(p, d, .8, rad, .02, M["snag"], seg=4)
    for j in range(r.randint(2, 4)):
        q = Vector((0, 0, Ht * r.uniform(.4, .85))); a = r.uniform(0, 6.28)
        mb.cone_dir(q, (math.cos(a), math.sin(a), r.uniform(.2, .9)), r.uniform(1.0, 2.2), .08, .015, M["snag"], seg=4)
    return keep_proto(mb.mesh(f"Snag_{v}"))


def proto_log(v):
    """Fallen trunk lying on the ground (origin at its middle), moss on top."""
    r = random.Random(1400 + v); mb = MB(); L = r.uniform(4.0, 6.0)
    mb.cone_dir((-L / 2, 0, .32), (1, 0, 0), L, .36, .3, M["snag"] if v % 2 else M["bark"], seg=8)
    mb.cone_dir((-L / 2 - .01, 0, .32), (1, 0, 0), .04, .35, .35, M["log_end"], seg=8)
    mb.box((r.uniform(-.8, .8), 0, .62), (L * .55, .36, .08), M["moss_dark"])
    for k in range(2):
        mb.cone_dir((r.uniform(-L / 3, L / 3), 0, .5), (r.uniform(-.3, .3), r.uniform(-.4, .4), 1), r.uniform(.4, .9),
                    .06, .02, M["snag"], seg=4)
    return keep_proto(mb.mesh(f"FallenLog_{v}"))


def proto_stump(v):
    r = random.Random(1500 + v); mb = MB(); hh = r.uniform(.4, .8)
    mb.cone((0, 0, hh / 2), .45, .38, hh, M["bark"], seg=9)
    mb.cone((0, 0, hh + .01), .37, .37, .03, M["log_end"], seg=9)
    for k in range(4):
        a = k / 4 * 6.28 + r.uniform(-.3, .3)
        mb.cone_dir((0, 0, .15), (math.cos(a), math.sin(a), -.45), .9, .16, .03, M["bark"], seg=5)
    return keep_proto(mb.mesh(f"Stump_{v}"))


def proto_fern(v):
    """Arching fern fronds."""
    r = random.Random(1600 + v); mb = MB(); m = M["fern2"] if v % 2 else M["fern"]
    K = r.randint(9, 13)
    for fr in range(K):
        a = fr / K * 2 * math.pi + r.uniform(-.2, .2); L = r.uniform(.7, 1.3); up = r.uniform(.6, .9)
        ca, sa = math.cos(a), math.sin(a); px, py = -sa, ca
        pts = []; S = 5
        for s in range(S + 1):
            t = s / S; dist = L * t; zz = L * (up * t - .8 * t * t) + .03
            w = .2 * math.sin(math.pi * min(1.0, t * 1.1)) + .015
            cx, cy = ca * dist, sa * dist
            pts += [(cx + px * w, cy + py * w, zz), (cx - px * w, cy - py * w, zz)]
        mb.poly(pts, [(2 * s, 2 * s + 1, 2 * s + 3, 2 * s + 2) for s in range(S)], m)
    return keep_proto(mb.mesh(f"Fern_{v}"))


def proto_shrub(v):
    """Low dark thorny shrub (replaces the old round bushes)."""
    r = random.Random(1700 + v); mb = MB()
    for i in range(r.randint(3, 5)):
        a = r.uniform(0, 6.28); d = r.uniform(.1, .6); s = r.uniform(.45, .8)
        mb.ico((math.cos(a) * d, math.sin(a) * d, s * .45), s, M["shrub"], sub=1, scale=(1, 1, .65), jitter=.38, seed=i + v * 5)
    for i in range(r.randint(4, 7)):
        a = r.uniform(0, 6.28); d = r.uniform(0, .5)
        mb.cone_dir((math.cos(a) * d, math.sin(a) * d, .3), (math.cos(a) * .5, math.sin(a) * .5, 1), r.uniform(.6, 1.1),
                    .025, .005, M["twig"], seg=3)
    return keep_proto(mb.mesh(f"ThornShrub_{v}"))


def proto_heather(v):
    r = random.Random(1800 + v); mb = MB()
    for i in range(6):
        a = r.uniform(0, 6.28); d = r.uniform(0, .9); s = r.uniform(.3, .5)
        mb.ico((math.cos(a) * d, math.sin(a) * d, s * .15), s, M["heather"], sub=1, scale=(1, 1, .35), jitter=.3, seed=i + v)
    for i in range(10):
        a = r.uniform(0, 6.28); d = r.uniform(0, 1.0)
        mb.ico((math.cos(a) * d, math.sin(a) * d, .2), .05, M["heather_f"])
    return keep_proto(mb.mesh(f"Heather_{v}"))


def proto_shrooms(v):
    """Small cluster of faintly glowing mushrooms."""
    r = random.Random(1900 + v); mb = MB()
    for i in range(r.randint(3, 6)):
        a = r.uniform(0, 6.28); d = r.uniform(0, .35); hh = r.uniform(.08, .25)
        x, y = math.cos(a) * d, math.sin(a) * d
        mb.cone((x, y, hh / 2), .025, .02, hh, M["shroom_st"], seg=5)
        mb.cone((x, y, hh + .02), r.uniform(.08, .14), .02, .06, M["myst_soft"], seg=7)
    return keep_proto(mb.mesh(f"GlowShrooms_{v}"))


def proto_rock(v, mossy=False):
    mb = MB()
    mb.ico((0, 0, 0), 1.0, M["rock_dark"] if v % 2 else M["rock"], sub=2,
           scale=(1.3, 1.0, .72), rot=(0, 0, v), jitter=.32, seed=v + 3)
    if mossy:
        mb.ico((0, 0, .42), .95, M["moss_dark"], sub=2, scale=(1.05, .8, .32), jitter=.2, seed=v + 9)
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


def proto_tallgrass(v):
    r = random.Random(950 + v); mb = MB()
    for i in range(18):
        a = r.uniform(0, 6.28); d = r.uniform(0, 1.3); hgt = r.uniform(.5, 1.1)
        mb.cone((math.cos(a) * d, math.sin(a) * d, hgt / 2), .06, .005, hgt,
                M["tallgrass"] if i % 4 else M["fern"], seg=3,
                rot=(r.uniform(-.25, .25), r.uniform(-.25, .25), 0))
    return keep_proto(mb.mesh(f"TallGrass_{v}"))


def proto_flowers(v):
    """Sparse, muted wildflowers (white, pale violet)."""
    r = random.Random(500 + v); mb = MB()
    fm = [M["flower_w"], M["flower_v"], M["heather_f"]]
    for i in range(8):
        a = r.uniform(0, 6.28); d = r.uniform(0, 1.2)
        mb.cone((math.cos(a) * d, math.sin(a) * d, .2), .1, .01, .4, M["tallgrass"], seg=4)
    for i in range(7):
        a = r.uniform(0, 6.28); d = r.uniform(0, 1.1)
        mb.ico((math.cos(a) * d, math.sin(a) * d, .38), .07, fm[(i + v) % 3])
    return keep_proto(mb.mesh(f"Flowers_{v}"))


def proto_moss(v, glow=False):
    """Low moss mound (the glow variant is used very rarely, deep in damp forest)."""
    r = random.Random(2000 + v); mb = MB()
    m1 = M["moss_glow"] if glow else (M["moss"] if v % 2 else M["moss_dark"])
    for i in range(r.randint(2, 4)):
        a = r.uniform(0, 6.28); d = r.uniform(0, .5); s = r.uniform(.4, .8)
        mb.ico((math.cos(a) * d, math.sin(a) * d, 0), s, m1, sub=1, scale=(1, 1, .16), jitter=.3, seed=i + v * 3)
    return keep_proto(mb.mesh(f"MossPatch_{'Glow_' if glow else ''}{v}"))


def proto_branch(v):
    """Fallen branch with a few twigs, lying on the ground."""
    r = random.Random(2100 + v); mb = MB(); L = r.uniform(1.4, 2.8)
    m = M["snag"] if v % 2 else M["bark"]
    a0 = r.uniform(0, 6.28); d = Vector((math.cos(a0), math.sin(a0), .02)).normalized()
    base = Vector((-d.x * L / 2, -d.y * L / 2, .06))
    mb.cone_dir(base, d, L, .06, .025, m, seg=5)
    for k in range(r.randint(2, 4)):
        q = base + d * (L * r.uniform(.25, .9)); a = a0 + r.choice((-1, 1)) * r.uniform(.5, 1.1)
        mb.cone_dir(q, (math.cos(a), math.sin(a), r.uniform(0, .25)), r.uniform(.35, .9), .025, .008, m, seg=4)
    return keep_proto(mb.mesh(f"FallenBranch_{v}"))


def proto_pebbles(v):
    r = random.Random(2200 + v); mb = MB()
    for i in range(r.randint(6, 10)):
        a = r.uniform(0, 6.28); d = math.sqrt(r.random()) * .7; s = r.uniform(.06, .18)
        mb.ico((math.cos(a) * d, math.sin(a) * d, s * .3), s, M["rock"] if i % 3 else M["rock_dark"], sub=1,
               scale=(1.2, 1, .6), jitter=.25, seed=i + v * 7)
    return keep_proto(mb.mesh(f"Pebbles_{v}"))


def proto_leaves(v):
    """Patch of fallen leaves (birch litter)."""
    r = random.Random(2300 + v); mb = MB()
    cols = [M["ab_leaf2"], M["leaf_brown"], M["ab_leaf"], M["leaf_red"]]
    for i in range(30):
        a = r.uniform(0, 6.28); d = math.sqrt(r.random()) * 1.2
        mb.box((math.cos(a) * d, math.sin(a) * d, .012), (.13, .08, .006), cols[(i * 7 + v) % 4],
               rot=(r.uniform(-.2, .2), r.uniform(-.2, .2), r.uniform(0, 6.28)))
    return keep_proto(mb.mesh(f"LeafLitter_{v}"))


def proto_blueberry(v):
    """Low blueberry shrub patch (mustikanvarvut)."""
    r = random.Random(2500 + v); mb = MB()
    for i in range(r.randint(10, 16)):
        a = r.uniform(0, 6.28); d = math.sqrt(r.random()) * .75; hh = r.uniform(.18, .38)
        x, y = math.cos(a) * d, math.sin(a) * d
        mb.cone((x, y, hh / 2), .012, .008, hh, M["twig"], seg=3)
        mb.ico((x, y, hh), r.uniform(.07, .12), M["blueberry_leaf"], sub=1, scale=(1, 1, .6), jitter=.3, seed=i + v)
    for i in range(r.randint(4, 8)):
        a = r.uniform(0, 6.28); d = math.sqrt(r.random()) * .65
        mb.ico((math.cos(a) * d, math.sin(a) * d, r.uniform(.12, .3)), .022, M["blueberry"], sub=1)
    return keep_proto(mb.mesh(f"Blueberry_{v}"))


def proto_lily(v):
    r = random.Random(2600 + v); mb = MB()
    for i in range(r.randint(5, 9)):
        a = r.uniform(0, 6.28); d = math.sqrt(r.random()) * 1.1
        mb.cone((math.cos(a) * d, math.sin(a) * d, 0), r.uniform(.16, .28), r.uniform(.16, .28), .012, M["lily"], seg=9)
    if v % 2 == 0:
        mb.ico((r.uniform(-.3, .3), r.uniform(-.3, .3), .05), .07, M["flower_w"], sub=1, scale=(1, 1, .6))
    return keep_proto(mb.mesh(f"LilyPads_{v}"))


def proto_rope():
    mb = MB()
    for k in range(3):
        mb.cone((0, 0, .03 + k * .055), .32 - k * .03, .32 - k * .03, .05, M["net"], seg=14)
    mb.cone((0, 0, .19), .12, .12, .02, M["wood_dark"], seg=10)
    return keep_proto(mb.mesh("RopeCoil"))


def proto_basket():
    mb = MB()
    mb.cone((0, 0, .2), .22, .3, .4, M["wicker"], seg=10)
    mb.cone((0, 0, .41), .31, .31, .04, M["wood_dark"], seg=10)
    return keep_proto(mb.mesh("Basket"))


def proto_log_boulder(v):
    """Small forest vignette: a mossy boulder with an old log resting across it."""
    r = random.Random(2400 + v); mb = MB()
    mb.ico((0, 0, .3), 1.1, M["rock"] if v % 2 else M["rock_dark"], sub=2, scale=(1.2, 1.0, .8), jitter=.3, seed=v + 40)
    mb.ico((0, 0, .95), .9, M["moss_dark"], sub=2, scale=(1.1, .9, .25), jitter=.2, seed=v + 41)
    mb.cone_dir((-2.6, .3, .25), (1, .05 + r.uniform(-.05, .05), .32), 5.2, .32, .26, M["snag"], seg=8)
    mb.box((-.8, .32, .9), (1.6, .3, .07), M["moss"], rot=(0, -.3, 0))
    return keep_proto(mb.mesh(f"LogOnBoulder_{v}"))


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
    """Net-drying rack: two posts, a top pole, nets hung over it in sagging folds with floats along the top."""
    r = random.Random(77); mb = MB()
    for x in (-1.7, 1.7):
        mb.box((x, 0, 1.15), (.16, .16, 2.3), M["wood_dark"])
        mb.box((x, 0, .05), (.5, .5, .1), M["stone"])
    mb.cone_dir((-1.95, 0, 2.2), (1, 0, 0), 3.9, .07, .07, M["wood_dark"], seg=6)  # round top pole
    x = -1.5
    while x < 1.5:                                                       # vertical folds, two sides of the pole
        fw = r.uniform(.18, .32)
        for side in (-1, 1):
            ln = r.uniform(1.2, 1.75) if side > 0 else r.uniform(.9, 1.4)
            mb.box((x + fw / 2, side * (.06 + .05 * r.random()), 2.2 - ln / 2), (fw * 1.05, .02, ln), M["net_tar"],
                   rot=(side * r.uniform(.03, .1), 0, r.uniform(-.06, .06)))
        x += fw
    for i in range(9):
        mb.ico((-1.4 + i * .35, .09, 2.12), .075, M["float"] if i % 2 else M["buoy_white"], sub=1)
    return keep_proto(mb.mesh("NetRack"))


def proto_buoy():
    mb = MB()
    mb.ico((0, 0, 0), .45, M["buoy_red"], sub=2, scale=(1, 1, .9))
    mb.cone((0, 0, .45), .3, .3, .15, M["buoy_white"], seg=12)
    mb.cone((0, 0, .9), .04, .04, .9, M["metal"], seg=6)
    return keep_proto(mb.mesh("Buoy"))

def proto_bench():
    mb = MB()
    mb.box((0, 0, .45), (1.8, .45, .08), M["wood"])
    mb.box((0, -.2, .75), (1.8, .06, .35), M["wood"])
    for x in (-.75, .75):
        mb.box((x, 0, .22), (.1, .4, .44), M["wood_dark"])
    return keep_proto(mb.mesh("Bench"))

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
    mb.box((.25, .1, .74), (.08, 2.6, .05), M["wood_old"], rot=(0, 0, .15))
    return keep_proto(mb.mesh(name))

SPRUCES = [proto_gloom_spruce(v, M["gs_dark"], M["gs_mid"]) for v in range(5)]
YOUNG = [proto_gloom_spruce(v, M["gs_dark"], M["gs_mid"], young=True) for v in range(3)]
PINES = [proto_crooked_pine(v) for v in range(5)]
BIRCHES = [proto_ashen_birch(v) for v in range(5)]
ISLE_SPRUCE = [proto_gloom_spruce(v + 20, M["gs_isle"], M["gs_isle2"], tag="GloomSpruceIsle") for v in range(3)]
DEADS = [proto_snag(v) for v in range(3)]
LOGS = [proto_log(v) for v in range(3)]
STUMPS = [proto_stump(v) for v in range(2)]
FERNS = [proto_fern(v) for v in range(4)]
BUSHES = [proto_shrub(v) for v in range(3)]
HEATHER = [proto_heather(v) for v in range(2)]
SHROOMS = [proto_shrooms(v) for v in range(2)]
ROCKS = [proto_rock(v) for v in range(5)]
MOSSROCKS = [proto_rock(v + 10, True) for v in range(3)]
REEDS = proto_reeds()
TALLGRASS = [proto_tallgrass(v) for v in range(3)]
FLOWERS = [proto_flowers(v) for v in range(3)]
R_KIND = {"S": 2.6, "P": 3.6, "B": 2.4, "D": 1.8}          # crown radius per kind at scale 1
KIND_LIST = {"S": SPRUCES, "P": PINES, "B": BIRCHES, "D": DEADS}
MOSS = [proto_moss(v) for v in range(3)]
MOSS_GLOW = proto_moss(9, glow=True)
BRANCHES = [proto_branch(v) for v in range(3)]
PEBBLES = [proto_pebbles(v) for v in range(3)]
LEAVES = [proto_leaves(v) for v in range(3)]
LOGBOULDER = [proto_log_boulder(v) for v in range(2)]
BLUEBERRY = [proto_blueberry(v) for v in range(3)]
LILIES = [proto_lily(v) for v in range(3)]
ROPE = proto_rope(); BASKET = proto_basket()
BARREL = proto_barrel(); CRATE = proto_crate(); LANTERN = proto_lantern_post()
FENCE = proto_fence(); SIGN = proto_sign(); NETRACK = proto_netrack(); BUOY = proto_buoy()
BENCH = proto_bench()
BOATS = [proto_boat("Rowboat_Red", mat("M_Boat_Red", C(.80, .25, .18))),
         proto_boat("Rowboat_Blue", mat("M_Boat_Blue", C(.25, .45, .72))),
         proto_boat("Rowboat_Green", mat("M_Boat_Green", C(.30, .58, .42)))]
M["alder_leaf"] = mat("M_Alder_Leaves", C(.22, .38, .21), 0.9)
M["alder_leaf2"] = mat("M_Alder_LeavesLight", C(.30, .45, .24), 0.9)
M["alder_bark"] = mat("M_Alder_Bark", C(.30, .27, .24))
M["juniper"] = mat("M_Juniper", C(.12, .25, .21), 0.9)
M["soot"] = mat("M_SootyWood", C(.17, .14, .12), 0.95)
M["soot2"] = mat("M_SootyWood2", C(.21, .17, .14), 0.95)
M["log_sauna"] = mat("M_Log_Weathered", C(.40, .33, .26), 0.9)
M["log_sauna2"] = mat("M_Log_Weathered2", C(.35, .29, .23), 0.9)


def proto_alder(v):
    """Shore alder: 3-5 stems from one root, side branches, an irregular oval crown of many small leaf clumps."""
    r = random.Random(2600 + v); mb = MB()
    for i in range(r.randint(3, 5)):
        a = r.uniform(0, 6.28); lean = r.uniform(.12, .38); L = r.uniform(4.2, 6.2)
        d = Vector((math.cos(a) * lean, math.sin(a) * lean, 1)).normalized()
        base = Vector((math.cos(a) * .15, math.sin(a) * .15, -.2))
        mb.cone_dir(base, d, L, .12, .05, M["alder_bark"], seg=5)
        for b in range(2):                                            # side branches
            t = r.uniform(.45, .8); q = base + d * (L * t)
            ba = a + r.uniform(-1.4, 1.4)
            bd = Vector((math.cos(ba), math.sin(ba), r.uniform(.6, 1.2)))
            mb.cone_dir(q, bd, r.uniform(1.0, 1.8), .045, .015, M["alder_bark"], seg=4)
        for j in range(r.randint(9, 12)):                             # leaf clumps along the upper stem
            t = r.uniform(.4, 1.0); q = base + d * (L * t)
            o = Vector((r.uniform(-.9, .9), r.uniform(-.9, .9), r.uniform(-.3, .5)))
            mb.ico(q + o, r.uniform(.42, .75), M["alder_leaf"] if (i + j) % 3 else M["alder_leaf2"], sub=1,
                   scale=(1, 1, .75), jitter=.35, seed=v * 31 + i * 7 + j)
    return keep_proto(mb.mesh(f"Alder_{v}"))


def proto_juniper(v):
    """Narrow dark juniper column for dry forest edges."""
    r = random.Random(2700 + v); mb = MB(); Ht = r.uniform(1.6, 2.6)
    mb.cone((0, 0, Ht * .45), .5, .32, Ht * .9, M["juniper"], seg=7)
    mb.cone((0, 0, Ht * .95), .33, .02, Ht * .35, M["juniper"], seg=7)
    mb.ico((.25, .1, Ht * .3), .42, M["juniper"], sub=1, scale=(1, 1, 1.4), jitter=.3, seed=v)
    return keep_proto(mb.mesh(f"Juniper_{v}"))


ALDERS = [proto_alder(v) for v in range(3)]
JUNIPERS = [proto_juniper(v) for v in range(2)]

# ---------------------------------------------------------------- buildings
WALL_T = 0.28          # chunky walls (How to Fish style); interiors are hollow and walkable


def window(mb, x, y, z, axis, s=1.0, glass=None, t=WALL_T):
    """Window set into a wall (visible from outside and inside)."""
    glass = glass or M["glass"]
    if axis == 'y':
        mb.box((x, y, z), (s + .44, t + .12, s + .44), M["trim"])
        mb.box((x, y, z), (s, t + .18, s), glass)
    else:
        mb.box((x, y, z), (t + .12, s + .44, s + .44), M["trim"])
        mb.box((x, y, z), (t + .18, s, s), glass)


def wall_x_span(mb, y, x0, x1, z0, z1, m, t=WALL_T, openings=()):
    """Wall running along X at depth y, with door openings [(centre_x, width, bottom, top)]."""
    cur = x0
    for cx, ow, ob, ot in sorted(openings):
        a, b = cx - ow / 2, cx + ow / 2
        if a > cur + 1e-3:
            mb.box(((cur + a) / 2, y, (z0 + z1) / 2), (a - cur, t, z1 - z0), m)
        if ob > z0 + 1e-3:
            mb.box((cx, y, (z0 + ob) / 2), (ow, t, ob - z0), m)
        if ot < z1 - 1e-3:
            mb.box((cx, y, (ot + z1) / 2), (ow, t, z1 - ot), m)
        cur = b
    if x1 > cur + 1e-3:
        mb.box(((cur + x1) / 2, y, (z0 + z1) / 2), (x1 - cur, t, z1 - z0), m)


def doorway(mb, door_x, yface, outward, dw, dh, f, leaves):
    """Door trim, door leaves swung open against the wall, and two steps up to the floor."""
    yo = yface + outward * .02
    for sx in (-1, 1):
        mb.box((door_x + sx * (dw / 2 + .1), yo, f + dh / 2), (.2, .12, dh), M["trim"])
    mb.box((door_x, yo, f + dh + .1), (dw + .6, .12, .2), M["trim"])
    lw = dw / leaves
    for k in range(leaves):
        hx = door_x - dw / 2 if k == 0 else door_x + dw / 2
        side = -1 if k == 0 else 1
        mb.box((hx + side * .04, yface + outward * lw / 2, f + dh / 2), (.06, lw, dh), M["door"])
    mb.box((door_x, yface + outward * .25, f - (f + .6) / 2), (dw + .4, .5, f + .6), M["stone"])
    mb.box((door_x, yface + outward * .75, f / 2 - (f / 2 + .6) / 2), (dw + .4, .5, f / 2 + .6), M["stone"])


def furnish(mb, kind, w, d, f, h, door_x, back_door):
    T = WALL_T; ix = w / 2 - T - .05; iy = d / 2 - T - .05
    wd, dk = M["wood"], M["wood_dark"]

    def table(cx, cy, sx, sy, zt=.76, tilt=0.0):
        mb.box((cx, cy, f + zt), (sx, sy, .06), wd, rot=(tilt, 0, 0))
        for ax in (-1, 1):
            for ay in (-1, 1):
                mb.box((cx + ax * (sx / 2 - .06), cy + ay * (sy / 2 - .06), f + zt / 2), (.06, .06, zt), dk)

    def lamp(cx, cy):
        mb.box((cx, cy, f + h - .3), (.02, .02, .6), M["net"])
        mb.box((cx, cy, f + h - .75), (.22, .22, .3), M["lantern"])

    mb.box((door_x * .3, .1, f + .055), (min(2.2, w * .4), min(1.5, d * .3), .02), M["rug"])
    if kind in ("cottage", "cabin"):
        bx, by = -ix + 1.05, -iy + .55
        mb.box((bx, by, f + .22), (2.0, 1.0, .4), dk)                     # bed
        mb.box((bx, by, f + .47), (1.9, .9, .12), M["trim"])
        mb.box((bx - .75, by, f + .58), (.35, .65, .1), M["trim"])
        mb.box((bx + .25, by, f + .55), (1.2, .92, .06), M["blanket"])
        table(ix * .3, -iy * .05, 1.1, .75, tilt=(.25 if kind == "cabin" else 0))
        mb.box((ix * .3 - .8, -iy * .05, f + .23), (.38, .38, .46), wd)  # stool
        mb.box((ix - .4, -iy + .4, f + .42), (.7, .6, .84), M["metal"])   # stove + pipe
        mb.cone((ix - .4, -iy + .4, f + .84 + (h - .84) / 2 + .3), .07, .07, h - .84 + .6, M["metal"], seg=6)
        mb.box((-ix + .17, iy * .25, f + .9), (.3, 1.3, 1.8), wd)         # shelf
        for zz in (.5, 1.0, 1.5):
            mb.box((-ix + .2, iy * .25, f + zz), (.34, 1.34, .04), dk)
        if kind == "cabin":
            for k in range(10):                                           # glowing rune ring
                a = k / 10 * 2 * math.pi
                mb.box((math.cos(a) * .9, math.sin(a) * .9 + .2, f + .07), (.18, .05, .01), M["myst"], rot=(0, 0, a))
            mb.box((ix * .3 + .9, -iy * .05 + .5, f + .2), (.38, .38, .46), wd, rot=(1.3, 0, .4))   # fallen stool
        else:
            mb.box((ix * .3 + .8, -iy * .05, f + .23), (.38, .38, .46), wd)
            lamp(0, 0)
    elif kind == "shop":
        mb.box((0, -iy * .25, f + .5), (w * .45, .7, 1.0), wd)            # counter
        mb.box((0, -iy * .25, f + 1.02), (w * .47, .8, .05), dk)
        mb.box((0, -iy + .2, f + 1.0), (w - 2 * T - .3, .35, 2.0), wd)    # back shelves with goods
        for k in range(int(w - 1.5)):
            for zz in (.6, 1.2, 1.7):
                mb.box((-w / 2 + 1.0 + k * .9, -iy + .42, f + zz), (.35, .25, .25),
                       (M["buoy_red"], M["float"], M["sign_teal"], M["flower_y"])[(k + int(zz * 10)) % 4])
        mb.box((-ix + .2, 0, f + .1), (.3, d * .5, .1), dk)               # rod rack
        for k in range(6):
            mb.cone((-ix + .2, -d * .2 + k * d * .08, f + 1.2), .02, .01, 2.2, dk, seg=4)
        lamp(0, .6); lamp(w * .25, -.8)
    else:                                                                 # storage / boathouse
        for cx, cy, s in ((-ix + .5, -iy + .5, 0), (-ix + 1.4, -iy + .5, 0), (-ix + .5, -iy + .5, .8),
                          (-ix + .5, -iy + 1.4, 0)):
            mb.box((cx, cy, f + .4 + s), (.8, .8, .8), wd)
        for k in range(3):
            mb.cone((ix - .5, -iy + .5 + k * .85, f + .5), .38, .38, 1.0, wd, seg=10)
        mb.box((ix - .45, iy * .35, f + .85), (.7, 2.2, .08), dk)         # workbench
        for sy in (-1, 1):
            mb.box((ix - .45, iy * .35 + sy * .95, f + .42), (.6, .08, .84), dk)
        lamp(0, 0)


SHUTTERS = {"BLD_Cottage_Red": "shutter_green", "BLD_Cottage_Blue": "trim", "BLD_Cottage_Mint": "shutter_blue",
            "BLD_Cottage_Ochre": "shutter_red", "BLD_TackleShop": "sign_teal", "BLD_AbandonedCabin": "wood_old"}


def window_deco(mb, x, y, z, axis, out, sh, s=1.0, flowers=False):
    """Chunky shutters beside a window (outer wall face at x / y). No small clutter."""
    if axis == 'y':
        for sx in (-1, 1):
            mb.box((x + sx * (s / 2 + .45), y + out * .08, z), (.5, .1, s + .35), sh)
    else:
        for sy in (-1, 1):
            mb.box((x + out * .08, y + sy * (s / 2 + .45), z), (.1, .5, s + .35), sh)


def house(name, x, y, w, d, h, wall, roof, ridge='x', rot=0.0, chimney=True, rh=None,
          door_x=0.0, sign=None, porch=False, tilt=(0, 0), glass=None, big_door=False, z=None,
          coll_=None, foundation=2.0):
    """Walk-in building: hollow walls, open doorway with the door swung open, plank floor, furniture."""
    kind = ("shop" if "Shop" in name else "storage" if ("Warehouse" in name or "Boathouse" in name)
            else "cabin" if "Abandoned" in name else "cottage")
    back_door = "Boathouse" in name
    z0 = H(x, y) if z is None else z
    rh = rh or min(w, d) * 0.55          # tall, oversized roof
    oh = 0.85; RT = .38; f = 0.45; T = WALL_T; mb = MB()
    mb.box((0, 0, (f - foundation) / 2), (w + .2, d + .2, f + foundation), M["stone"])
    mb.box((0, 0, f + .02), (w - 2 * T, d - 2 * T, .04), M["wood"])
    dw, dh = (2.8, 3.0) if big_door else (1.2, 2.2)
    dh = min(dh, h - .3)
    top = f + h
    wall_x_span(mb, d / 2 - T / 2, -w / 2, w / 2, f, top, wall, openings=[(door_x, dw, f, f + dh)])
    wall_x_span(mb, -d / 2 + T / 2, -w / 2, w / 2, f, top, wall,
                openings=[(0.0, 1.2, f, f + 2.2)] if back_door else [])
    for sx in (-1, 1):
        mb.box((sx * (w / 2 - T / 2), 0, f + h / 2), (T, d - 2 * T, h), wall)
        for sy in (-1, 1):
            mb.box((sx * w / 2, sy * d / 2, f + h / 2), (.36, .36, h + .1), M["trim"])
    if ridge == 'x':
        for sx in (-1, 1):
            mb.prism((sx * (w / 2 - T / 2), 0, top), (T, d, rh * .98), wall)
        a = math.atan2(rh, d / 2); sw = (d / 2 + oh) / math.cos(a)
        for s in (1, -1):
            mb.box((0, s * math.cos(a) * sw / 2, top + rh - math.sin(a) * sw / 2 + RT / 2),
                   (w + 2 * oh, sw, RT), roof, rot=(-s * a, 0, 0))
        mb.box((0, 0, top + rh - .3), (w - 2 * T, .2, .2), M["wood_dark"])          # ridge beam
        gable_win = [((sx * (w / 2 - T / 2), 0), 'x') for sx in (-1, 1)]
    else:
        for sy in (-1, 1):
            mb.prism((0, sy * (d / 2 - T / 2), top), (T, w, rh * .98), wall, rot=(0, 0, math.pi / 2))
        a = math.atan2(rh, w / 2); sw = (w / 2 + oh) / math.cos(a)
        for s in (1, -1):
            mb.box((s * math.cos(a) * sw / 2, 0, top + rh - math.sin(a) * sw / 2 + RT / 2),
                   (sw, d + 2 * oh, RT), roof, rot=(0, s * a, 0))
        mb.box((0, 0, top + rh - .3), (.2, d - 2 * T, .2), M["wood_dark"])
        gable_win = [((0, sy * (d / 2 - T / 2)), 'y') for sy in (-1, 1)]
    for sx in (-1, 1):                                                              # tie beams
        if ridge == 'x':
            mb.box((sx * w * .25, 0, top - .1), (.16, d - 2 * T, .16), M["wood_dark"])
        else:
            mb.box((0, sx * d * .25, top - .1), (w - 2 * T, .16, .16), M["wood_dark"])
    for (gx, gy), ax in gable_win:
        window(mb, gx, gy, top + rh * .35, ax, .7, glass)
    doorway(mb, door_x, d / 2, 1, dw, dh, f, 2 if big_door else 1)
    if back_door:
        doorway(mb, 0.0, -d / 2, -1, 1.2, 2.2, f, 1)
    wz = f + h * .55
    for wx in (-w / 4 - .2, w / 4 + .2):
        if abs(wx - door_x) > dw / 2 + .9 and abs(wx) < w / 2 - .7:
            window(mb, wx, d / 2 - T / 2, wz, 'y', 1.0, glass)
    for wx in (-w / 4, w / 4):
        if not back_door or abs(wx) > 1.5:
            window(mb, wx, -d / 2 + T / 2, wz, 'y', 1.0, glass)
    for sx in (-1, 1):
        window(mb, sx * (w / 2 - T / 2), 0, wz, 'x', 1.0, glass)
    if name in SHUTTERS and kind != "storage":
        sh = M[SHUTTERS[name]]; flw = kind != "cabin"
        for wx in (-w / 4 - .2, w / 4 + .2):
            if abs(wx - door_x) > dw / 2 + .9 and abs(wx) < w / 2 - .7:
                window_deco(mb, wx, d / 2, wz, 'y', 1, sh, flowers=flw)
        for sx in (-1, 1):
            window_deco(mb, sx * w / 2, 0, wz, 'x', sx, sh, flowers=flw and sx > 0)
    if chimney:
        cx, cy = (w * .22, -d * .12) if ridge == 'x' else (w * .12, -d * .22)
        mb.box((cx, cy, top + (rh + 1.1) / 2), (1.0, 1.0, rh + 1.1), M["stone"])
        mb.box((cx, cy, top + rh + 1.15), (1.2, 1.2, .2), M["stone"])
    if sign is not None:
        mb.box((door_x, d / 2 + .2, f + h - .35), (min(5.0, w - .6), .16, 1.1), M["trim"])
        mb.box((door_x, d / 2 + .26, f + h - .35), (min(4.7, w - .9), .14, .85), sign)
    if porch:
        mb.box((0, d / 2 + 1.3, f - .08), (w * .85, 2.6, .16), M["wood"])
        mb.box((0, d / 2 + 1.3, (f - .16 - 1.6) / 2), (w * .83, 2.5, 1.6 + f - .16), M["wood_dark"])
        for sx in (-1, 1):
            mb.box((sx * w * .4, d / 2 + 2.45, f + 1.25), (.16, .16, 2.5), M["wood_dark"])
        mb.box((0, d / 2 + 1.4, f + 2.55), (w * .95, 3.2, .3), roof, rot=(-.18, 0, 0))
        mb.box((door_x, d / 2 + 2.85, f / 2 - (f / 2 + .6) / 2), (dw + .6, .5, f / 2 + .6), M["stone"])
    furnish(mb, kind, w, d, f, h, door_x, back_door)
    ob = mb.obj(name, coll_ or C_VBLD, (x, y, z0 - .05), rot, tilt)
    EXCL.append((x, y, max(w, d) * .75 + 2.5))
    return ob


def dock(name, x, y, ang, length, width=2.4, deck_z=1.0, broken=0.0, t_width=0.0,
         coll_=None, wood=None):
    wood = wood or M["wood"]; post = M["wood_dark"] if not broken else M["wood_old"]
    r = random.Random(sum(map(ord, name))); mb = MB(); pw = .5       # wide chunky planks
    pz = deck_z - .035                                                  # plank top stays at deck_z + .045
    for i in range(int(length / pw)):
        if broken and r.random() < broken:
            continue
        t = (r.uniform(-.05, .05), r.uniform(-.04, .04), r.uniform(-.06, .06)) if broken else (0, 0, r.uniform(-.01, .01))
        mb.box((r.uniform(-.03, .03), i * pw + pw / 2, pz - (r.uniform(0, .15) if broken else 0)),
               (width, pw - .07, .16), wood, rot=t)
    for sx in (-1, 1):
        mb.box((sx * (width / 2 - .25), length / 2, deck_z - .22), (.26, length, .28), post)
    for i in range(int(length / 2.6) + 1):
        py = min(length - .2, .2 + i * 2.6)
        for sx in (-1, 1):
            lean = (r.uniform(-.15, .15), r.uniform(-.15, .15), 0) if broken else (0, 0, 0)
            mb.box((sx * width / 2, py, (deck_z + .35 - 3.5) / 2), (.34, .34, deck_z + .35 + 3.5), post, rot=lean)
    if t_width:
        tl = 4.2
        for i in range(int(tl / pw)):
            mb.box((0, length + i * pw + pw / 2, pz), (t_width, pw - .07, .16), wood)
        for tx in (-t_width / 2, -t_width / 4, t_width / 4, t_width / 2):
            for ty in (length + .2, length + tl - .2):
                mb.box((tx, ty, (deck_z + .35 - 3.5) / 2), (.34, .34, deck_z + .35 + 3.5), post)
        for tx in (-t_width / 2 + .3, t_width / 2 - .3):
            mb.cone((tx, length + tl - .4, deck_z + .3), .24, .24, .6, post, seg=8)
    else:
        for sx in (-1, 1):
            mb.cone((sx * (width / 2 - .25), length - .4, deck_z + .3), .22, .22, .6, post, seg=8)
    mb.obj(name, coll_ or C_VDOCK, (x, y, 0), ang)
    dx, dy = -math.sin(ang), math.cos(ang)
    total = length + (4.2 if t_width else 0)
    for s in range(0, int(total) + 4, 3):
        EXCL.append((x + dx * s, y + dy * s, max(width, t_width) / 2 + 2.5))
    return (x + dx * length, y + dy * length)


def fence_line(p0, p1, tag, c=None):
    p0 = Vector(p0); p1 = Vector(p1); d = p1 - p0; L = d.length
    if L < 1:
        return
    a = math.atan2(d.y, d.x); n = max(1, int(L / 2.45))
    for i in range(n):
        q = p0 + d * ((i + .5) / n)
        if rng.random() < .1 or path_dist(q.x, q.y, 4) < 1.4:
            continue
        inst(FENCE, f"PROP_Fence_{tag}_{i:02d}", c or C_VPROP, (q.x, q.y, H(q.x, q.y)), a + rng.uniform(-.04, .04))
        GROUND.add(q.x, q.y, 1.3)


def yard(name, x, y, rot, w, d, depth=7.0):
    """Fence three sides of a back garden behind a house (local -Y side)."""
    pts = [(-w / 2 - 1.5, -d / 2 - .5), (-w / 2 - 1.5, -d / 2 - depth), (w / 2 + 1.5, -d / 2 - depth),
           (w / 2 + 1.5, -d / 2 - .5)]
    wp = [l2w(x, y, rot, *p) for p in pts]
    for k in range(3):
        fence_line(wp[k], wp[k + 1], f"{name}_{k}")
    for i, bx in enumerate((-w / 4, w / 4)):     # small kitchen garden beds inside the fence
        q = l2w(x, y, rot, bx, -d / 2 - depth / 2)
        if path_dist(q[0], q[1], 5) < 1.8 or not GROUND.free(q[0], q[1], 1.0):
            continue
        hq = [H(*l2w(q[0], q[1], rot, ox, oy)) for ox in (-.8, .8) for oy in (-.5, .5)]
        mb = MB()
        mb.box((0, 0, .12 - (max(hq) - min(hq))), (1.6, 1.0, .3 + 2 * (max(hq) - min(hq))), M["wood_old"])
        mb.box((0, 0, .28), (1.45, .85, .04), M["soil"])
        for k in range(6):
            mb.cone((-.55 + (k % 3) * .55, -.2 + (k // 3) * .4, .4), .14, .02, .26, M["grass_tuft"], seg=5)
        mb.obj(f"PROP_GardenBed_{name}_{i}", C_VPROP, (q[0], q[1], max(hq) - .05), rot)
        GROUND.add(q[0], q[1], 1.0)


progress("village")
BLD = {}
BLD["shop"] = (10.0, SY - 27, face(10, SY - 27, *SQ))
BLD["red"] = (-33.0, SY - 14, face(-33, SY - 14, -20, SY + 20))
BLD["mint"] = (22.0, SY - 12, face(22, SY - 12, *SQ))
BLD["blue"] = (-44.0, SY - 42, face(-44, SY - 42, -20, SY))
BLD["ochre"] = (-25.0, SY - 41, face(-25, SY - 41, -18, SY - 25))
BLD["ware"] = (54.0, SY - 15, face(54, SY - 15, 40, SY))
x, y, r_ = BLD["shop"]
house("BLD_TackleShop", x, y, 10, 8, 3.6, WALLS["yellow"], ROOFS["red"], ridge='y', rot=r_,
      sign=M["sign_teal"], porch=True, chimney=False)
x, y, r_ = BLD["red"]
house("BLD_Cottage_Red", x, y, 7, 6, 3.0, WALLS["red"], ROOFS["slate"], ridge='x', rot=r_, door_x=-1.2)
yard("Red", x, y, r_, 7, 6, 6)
x, y, r_ = BLD["blue"]
house("BLD_Cottage_Blue", x, y, 6.5, 6, 2.8, WALLS["blue"], ROOFS["brown"], ridge='y', rot=r_)
yard("Blue", x, y, r_, 6.5, 6)
x, y, r_ = BLD["mint"]
house("BLD_Cottage_Mint", x, y, 7.5, 6.5, 3.0, WALLS["mint"], ROOFS["red"], ridge='x', rot=r_,
      door_x=1.3, porch=True)
x, y, r_ = BLD["ochre"]
house("BLD_Cottage_Ochre", x, y, 6, 5.5, 2.7, WALLS["ochre"], ROOFS["green"], ridge='y', rot=r_)
yard("Ochre", x, y, r_, 6, 5.5, 8)
x, y, r_ = BLD["ware"]
house("BLD_Warehouse", x, y, 12, 9, 4.2, WALLS["steel"], ROOFS["rust"], ridge='y', big_door=True,
      chimney=False, rot=r_)
bx, by = shore_point(-26, SY - 10, 0, 1)
house("BLD_Boathouse", -26, by + 1.5, 6.5, 10, 3.0, WALLS["barn"], ROOFS["slate"], ridge='y',
      big_door=True, chimney=False, z=0.55, foundation=3.5, rot=-.12, rh=4.3)   # tall boathouse gable

mx, my = shore_point(0, SY - 8, 0, 1)
main_end = dock("DOCK_Main", 0, my - 4, 0.0, 30, width=2.6, t_width=10)
wx_, wy_ = shore_point(-46, SY - 12, 0, 1)
dock("DOCK_West", -46, wy_ - 3, 0.18, 14)
ex_, ey_ = shore_point(36, SY - 8, 0, 1)
dock("DOCK_East", ex_, ey_ - 3, -0.25, 13)

bw = MB(); y0_ = SQ[1] + 8.5
for i in range(int((my - 4 - y0_) / .3)):
    yy = y0_ + i * .3 + .15
    bw.box((0, yy, H(0, yy) + .12), (2.4, .26, .08), M["wood"])
bw.obj("PATH_Boardwalk_Dock", C_PATHS)

# creek bridge where the street crosses the creek
sd = catmull(STREET, 1.0)
bi, bc = min(((i, c) for i, s in enumerate(sd) for c in CREEK_D[::2]),
             key=lambda ic: (sd[ic[0]] - ic[1]).length)
bp = sd[bi]; bt = (sd[min(len(sd) - 1, bi + 1)] - sd[max(0, bi - 1)]).normalized()
bang = math.atan2(-bt.x, bt.y); BL = 8.0
ends = [bp + bt * (BL / 2), bp - bt * (BL / 2)]
bz = max(H(e.x, e.y) for e in ends) + .15
bm_ = MB()
n = int(BL / .3)
for i in range(n):
    t = (i + .5) / n; yy = -BL / 2 + t * BL
    bm_.box((0, yy, .45 * math.sin(math.pi * t)), (3.0, .26, .09), M["wood"])
for sx in (-1, 1):
    for i in range(5):
        t = i / 4; yy = -BL / 2 + t * BL; zz = .45 * math.sin(math.pi * t)
        bm_.box((sx * 1.45, yy, zz + .5), (.12, .12, 1.0), M["wood_dark"])
    for i in range(4):
        t0, t1 = i / 4, (i + 1) / 4
        z0_, z1_ = .45 * math.sin(math.pi * t0), .45 * math.sin(math.pi * t1)
        y0b, y1b = -BL / 2 + t0 * BL, -BL / 2 + t1 * BL
        L_ = math.hypot(y1b - y0b, z1_ - z0_)
        bm_.box((sx * 1.45, (y0b + y1b) / 2, (z0_ + z1_) / 2 + .95), (.1, L_, .1), M["wood_dark"],
                rot=(math.atan2(z1_ - z0_, y1b - y0b), 0, 0))
    bm_.box((sx * 1.2, 0, -.2), (.2, BL, .25), M["wood_dark"])
bm_.obj("STR_Bridge_Creek", C_VILLAGE, (bp.x, bp.y, bz), bang)
EXCL.append((bp.x, bp.y, 6))

# props
def P(me, name, x, y, rotz=None, scale=1.0, z=None, c=C_VPROP, tilt=(0, 0)):
    rz = rng.uniform(0, 6.28) if rotz is None else rotz
    if name.startswith(("PROP_Barrel", "PROP_Crate")) and path_dist(x, y, 4) < 1.0:
        return None
    GROUND.add(x, y, .7)
    return inst(me, name, c, (x, y, H(x, y) if z is None else z), rz, scale, tilt)

k = 0; acc = 0.0; side = 1
for i in range(1, len(sd)):
    acc += (sd[i] - sd[i - 1]).length
    if acc < 15:
        continue
    acc = 0.0; side = -side
    t = (sd[min(len(sd) - 1, i + 1)] - sd[i - 1]).normalized(); nrm = Vector((-t.y, t.x))
    q = sd[i] + nrm * (2.7 * side)
    if math.hypot(q.x - SQ[0], q.y - SQ[1]) < 12 or (q - bp).length < 6 or excluded(q.x, q.y):
        continue
    P(LANTERN, f"PROP_Lantern_{k:02d}", q.x, q.y, rotz=math.atan2(-nrm.x * side, nrm.y * side) + math.pi / 2); k += 1
for a in (0.4, 2.0, 3.6, 5.2):           # lanterns around the square
    q = (SQ[0] + math.cos(a) * 9.8, SQ[1] + math.sin(a) * 9.8)
    P(LANTERN, f"PROP_Lantern_{k:02d}", *q, rotz=a + math.pi / 2); k += 1
for yy in (my + 6, my + 18):
    P(LANTERN, f"PROP_Lantern_{k:02d}", 1.4, yy, rotz=math.pi, z=1.0); k += 1
P(LANTERN, f"PROP_Lantern_{k:02d}", -21, by - 5, rotz=math.pi)

# square furniture: well, notice board, benches
wl = MB()
wl.cone((0, 0, .45), 1.1, 1.1, .9, M["stone"], seg=14)
wl.cone((0, 0, .9), .85, .85, .1, M["wood_dark"], seg=14)
for sx in (-1, 1):
    wl.box((sx * .95, 0, 1.4), (.14, .14, 1.9), M["wood_dark"])
wl.box((0, 0, 2.15), (2.2, .12, .12), M["wood_dark"])
wl.prism((0, 0, 2.2), (2.6, 1.8, .8), ROOFS["red"])
wl.obj("STR_Well_Square", C_VILLAGE, (SQ[0] - 3, SQ[1] - 1.5, H(SQ[0] - 3, SQ[1] - 1.5)), .3)
nb = MB()
for sx in (-1, 1):
    nb.box((sx * .9, 0, 1.0), (.14, .14, 2.0), M["wood_dark"])
nb.box((0, 0, 1.45), (2.0, .1, 1.0), M["wood"])
for i, (dx_, dz_) in enumerate(((-.5, 1.6), (.3, 1.5), (.6, 1.25), (-.2, 1.2))):
    nb.box((dx_, .07, dz_), (.35, .02, .45), M["trim"] if i % 2 else M["flower_y"])
nb.prism((0, 0, 2.0), (2.4, .6, .35), ROOFS["slate"])
nb.obj("STR_NoticeBoard_Square", C_VILLAGE, (SQ[0] - 7, SQ[1] - 6.5, H(SQ[0] - 7, SQ[1] - 6.5)),
       face(SQ[0] - 7, SQ[1] - 6.5, *SQ))
GROUND.add(SQ[0] - 7, SQ[1] - 6.5, 1.3)
for i, a in enumerate((1.2, 4.2)):
    q = (SQ[0] + math.cos(a) * 7, SQ[1] + math.sin(a) * 7)
    P(BENCH, f"PROP_Bench_{i:02d}", *q, rotz=face(q[0], q[1], *SQ))

sx_, sy_, sr_ = BLD["shop"]
for i, (lx, ly) in enumerate([(-4.0, 5.6), (-3.2, 6.2), (4.0, 6.0)]):
    q = l2w(sx_, sy_, sr_, lx, ly)
    P(BARREL, f"PROP_Barrel_{i:02d}", *q, z=H(sx_, sy_) + .4)
for i, (x, y, z) in enumerate([(3.5, main_end[1] + 2.5, 1.05), (4.2, main_end[1] + 2.0, 1.05),
                               (-3.8, main_end[1] + 3, 1.05)]):
    P(BARREL if i < 2 else CRATE, f"PROP_DockClutter_{i:02d}", x, y, z=z)
wx0, wy0, wr0 = BLD["ware"]
for i, (lx, ly, s) in enumerate([(-3, 6.5, 0), (-1.9, 6.6, 0), (-3, 6.5, .8), (3.5, 6.2, 0), (4.4, 7.0, 0)]):
    q = l2w(wx0, wy0, wr0, lx, ly)
    if s and bpy.data.objects.get("PROP_Crate_00") is None:
        continue                     # no crate to stack on
    P(CRATE, f"PROP_Crate_{i:02d}", *q, rotz=wr0 + rng.uniform(-.3, .3), z=H(*q) + s)
for i, (lx, ly) in enumerate([(5.5, 5.0), (6.3, 4.2)]):
    q = l2w(wx0, wy0, wr0, lx, ly)
    P(BARREL, f"PROP_Barrel_W{i:02d}", *q)
P(BARREL, "PROP_Barrel_W02", -30.5, by - 6.5)
P(NETRACK, "PROP_NetRack_00", -33.5, by - 3.5, rotz=-.12)        # net rack right beside the boathouse
P(NETRACK, "PROP_NetRack_01", 12, SY - 5, rotz=-.25)
P(NETRACK, "PROP_NetRack_02", 44, SY - 4, rotz=-.6)
P(SIGN, "PROP_Signpost_West", -72, SY - 26.5, rotz=.4)
P(SIGN, "PROP_Signpost_East", 74, SY - 31, rotz=-.6)
P(SIGN, "PROP_Signpost_Square", SQ[0] - 8, SQ[1] - 6, rotz=.9)
P(SIGN, "PROP_Signpost_North", -150, 86, rotz=1.2)
inst(BOATS[0], "BOAT_Rowboat_Red", C_VPROP, (3.1, my + 12, .05), 0.02)
for dname, items in (("DOCK_Main", ((ROPE, -1.8, 32.8), (BASKET, 2.0, 33.6), (CRATE, -1.0, 30.6))),
                     ("DOCK_West", ((ROPE, -.6, 10.0), (BASKET, .6, 12.5))),
                     ("DOCK_East", ((ROPE, .5, 9.0), (CRATE, -.5, 11.4)))):
    do_ = bpy.data.objects[dname]
    for k, (me_, lx, ly) in enumerate(items):
        q = l2w(do_.location.x, do_.location.y, do_.rotation_euler.z, lx, ly)
        inst(me_, f"PROP_DockGear_{dname[5:]}_{k}", C_VPROP, (q[0], q[1], 1.05), do_.rotation_euler.z + k)
inst(BOATS[1], "BOAT_Rowboat_Blue", C_VPROP, (-46 + 2.2, wy_ + 6, .05), .2)
inst(BOATS[2], "BOAT_Rowboat_Green", C_VPROP, (14, SY - 1.5, H(14, SY - 1.5) + .05), 1.35, 1.0, (.08, .05))
for i, (bxx, rz_) in enumerate(((-39.0, 1.75), (-15.0, 1.45))):    # rowboats pulled up on the beach
    _, byy = shore_point(bxx, SY - 12, 0, 1); byy -= 3.0
    if GROUND.free(bxx, byy, 1.6) and path_dist(bxx, byy, 4) > 1.6:
        inst(BOATS[i], f"BOAT_Rowboat_Shore_{i}", C_VPROP, (bxx, byy, H(bxx, byy) + .05), rz_, 1.0, (.08, -.05))
        GROUND.add(bxx, byy, 1.6)

# --- village logic (plan/LAYOUT_RULES.md): woodsheds by the cottages, a shore sauna, a smokehouse downwind
def log_walls(mb, w, d, z0, z1, m, m2=None, door_w=1.0, door_h=1.95, lh=.24, T=.26):
    """Round log courses with crossed corner ends (Nordic log building). Door in the +Y wall."""
    n = int((z1 - z0) / lh); r_ = lh * .52; ov = .3
    for k in range(n):
        zc = z0 + (k + .5) * lh
        mk = m2 if (m2 is not None and k % 3 == 1) else m          # an occasional slightly different log
        for sy in (-1, 1):                                            # walls along X
            y_ = sy * (d / 2 - T / 2)
            if sy > 0 and zc < z0 + door_h:
                for sx in (-1, 1):
                    a, b = door_w / 2, w / 2 + ov
                    mb.cone_dir((sx * a, y_, zc), (sx, 0, 0), b - a, r_, r_, mk, seg=6)
            else:
                mb.cone_dir((-w / 2 - ov, y_, zc), (1, 0, 0), w + 2 * ov, r_, r_, mk, seg=6)
        for sx in (-1, 1):                                            # walls along Y, half a log higher
            mb.cone_dir((sx * (w / 2 - T / 2), -d / 2 - ov, zc + lh * .5), (0, 1, 0), d + 2 * ov, r_, r_, mk, seg=6)


def firewood(mb, cx, cy, z, w, rows, depth=.5, r_=.11, seed=0):
    """Stacked split logs seen end-on (round ends facing local -Y/+Y)."""
    rr = random.Random(seed); n = max(1, int(w / (2 * r_ + .02)))
    for row in range(rows):
        off = r_ if row % 2 else 0
        for i in range(n - (1 if row % 2 else 0)):
            x = cx - w / 2 + r_ + off + i * (2 * r_ + .02)
            rad = r_ * rr.uniform(.85, 1.1)
            mb.cone((x, cy, z + r_ + row * (2 * r_ * .9)), rad, rad, depth, M["log_end"], seg=6,
                    rot=(math.pi / 2, rr.uniform(0, 1), 0))


def woodshed(name, x, y, rot):
    """Open-front woodshed: board walls, corner posts, a stack of split logs, sloping roof."""
    mb = MB(); w, d, h0, h1 = 3.0, 1.7, 2.3, 1.8; rr = random.Random(sum(map(ord, name)))
    bx = -w / 2 + .1
    while bx < w / 2 - .05:                                           # back wall: vertical boards
        bw = rr.uniform(.16, .22)
        mb.box((bx + bw / 2, -d / 2 + .06, h0 / 2), (bw - .025, .08, h0), M["wood_old"] if rr.random() < .7 else M["wood"])
        bx += bw
    for sx in (-1, 1):
        yy = -d / 2 + .1
        while yy < d / 2 - .1:                                        # side walls: boards
            bw = rr.uniform(.16, .22)
            hh = h0 - (h0 - h1) * ((yy + d / 2) / d)
            mb.box((sx * (w / 2 - .04), yy + bw / 2, hh / 2), (.08, bw - .025, hh), M["wood_old"])
            yy += bw
        for sy in (-1, 1):
            hh = h0 if sy < 0 else h1
            mb.box((sx * (w / 2 - .05), sy * (d / 2 - .05), hh / 2), (.14, .14, hh), M["wood_dark"])
    a = math.atan2(h0 - h1, d)
    mb.box((0, 0, (h0 + h1) / 2 + .14), (w + .5, d / math.cos(a) + .6, .2), ROOFS["slate"], rot=(-a, 0, 0))
    mb.box((0, 0, .06), (w - .2, d - .2, .12), M["wood_dark"])          # floor sleepers
    firewood(mb, 0, .05, .12, w - .35, 6, depth=d - .45, seed=len(name))
    z = min(H(*l2w(x, y, rot, ox, oy)) for ox in (-1.5, 1.5) for oy in (-.85, .85))
    mb.box((0, 0, -.5), (w + .1, d + .1, 1.0), M["stone"])
    mb.obj(name, C_VPROP, (x, y, z), rot)
    GROUND.add(x, y, 2.0); EXCL.append((x, y, 2.4))


COTTAGE_SIZE = {"red": (7, 6), "blue": (6.5, 6), "mint": (7.5, 6.5), "ochre": (6, 5.5)}
for key, (cw, cd) in COTTAGE_SIZE.items():
    hx, hy, hr = BLD[key]
    for lx, ly in ((cw / 2 + 3.4, -cd / 2 + 1.0), (-cw / 2 - 3.4, -cd / 2 + 1.0), (cw / 2 + 3.4, cd / 2 - 1.0),
                   (-cw / 2 - 3.4, cd / 2 - 1.0)):
        q = l2w(hx, hy, hr, lx, ly)
        if GROUND.free(q[0], q[1], 2.0) and path_dist(q[0], q[1], 6) > 2.8 and H(*q) > .8 and slope(*q) < .35:
            woodshed(f"STR_Woodshed_{key.capitalize()}", q[0], q[1], hr)
            break


def small_hut(name, x, y, rot, w, d, h, wall, roof, kind):
    """Small walk-in log hut: shore sauna (benches + stove) or smokehouse (fire pit + smoking rods)."""
    mb = MB(); T = .26; f = .3
    wall2 = M["log_sauna2"] if kind == "sauna" else M["soot2"]
    trim = M["wood_dark"]
    mb.box((0, 0, (f - 1.5) / 2), (w - .1, d - .1, f + 1.5), M["rock_dark"])
    mb.box((0, 0, f + .02), (w - 2 * T, d - 2 * T, .04), M["wood"])
    log_walls(mb, w, d, f, f + h, wall, wall2, T=T)
    rh = d * .5
    for sy in (-1, 1):                                                # gable triangles in boards
        mb.prism((0, sy * (d / 2 - T / 2), f + h), (T, w, rh * .98), wall2, rot=(0, 0, math.pi / 2))
    a = math.atan2(rh, w / 2); sw = (w / 2 + .7) / math.cos(a)
    for s_ in (1, -1):
        mb.box((s_ * math.cos(a) * sw / 2, 0, f + h + rh - math.sin(a) * sw / 2 + .17),
               (sw, d + 1.1, .34), roof, rot=(0, s_ * a, 0))
    for sx in (-1, 1):
        mb.box((sx * .58, d / 2 + .02, f + 1.0), (.16, .1, 2.0), trim)
    mb.box((0, d / 2 + .02, f + 2.03), (1.35, .1, .16), trim)
    mb.box((-.48, d / 2 + .5, f + .98), (.06, .9, 1.95), M["door"])                     # door swung open
    mb.box((0, d / 2 + .45, f / 2 - .25), (1.4, .6, f + .5), M["stone"])                 # step
    if kind == "sauna":
        window(mb, w / 2 - T / 2, -.3, f + 1.35, 'x', .45, M["glass"], t=T)            # small window over the benches
        mb.box((0, -d / 2 + .75, f + .45), (w - 2 * T - .1, .9, .1), M["wood"])          # benches
        mb.box((0, -d / 2 + .55, f + 1.0), (w - 2 * T - .1, .6, .1), M["wood"])
        cx, cy = -w / 2 + .75, d / 2 - .85
        mb.box((cx, cy, f + .4), (.7, .7, .8), M["stone"])                                # stove
        mb.box((cx, cy, f + .85), (.6, .6, .1), M["rock_dark"])
        for k_ in range(5):
            mb.ico((cx - .2 + (k_ % 3) * .2, cy - .1 + (k_ // 3) * .2, f + .95), .1, M["rock_dark"], sub=1)
        mb.box((w / 2 + .45, -d / 2 + 1.0, .5), (.12, 1.8, 1.0), M["wood_old"])          # bench by the wall outside
        firewood(mb, 0, -d / 2 - .45, -.05, w - .6, 4, depth=.5, seed=3)              # woodpile at the back wall
    else:
        mb.box((0, 0, f + .15), (.9, .9, .3), M["stone"])                                 # fire pit
        for zz in (1.6, 2.0):
            mb.cone_dir((-w / 2 + T, 0, f + zz), (1, 0, 0), w - 2 * T, .03, .03, M["wood_dark"], seg=5)
        cx, cy = w / 2 - .6, -d / 2 + .6
    mb.box((cx, cy, f + h + rh / 2 + .3), (.6, .6, rh + 1.3), M["rock_dark"])            # chimney
    mb.box((cx, cy, f + h + rh + .98), (.74, .74, .1), M["rock_dark"])
    z = min(H(*l2w(x, y, rot, ox, oy)) for ox in (-w / 2, w / 2) for oy in (-d / 2, d / 2))
    ob = mb.obj(name, C_VBLD, (x, y, z), rot)
    EXCL.append((x, y, max(w, d) * .75 + 2.0)); GROUND.add(x, y, max(w, d) * .75 + .5)
    return ob


# shore sauna west of the creek mouth: 9 m from the water, own small jetty
for sxx in (-74.0, -78.0, -70.0, -82.0):
    _, syy = shore_point(sxx, SY - 14, 0, 1)
    hx, hy = sxx, syy - 9.0
    if CGRID.dist(hx, hy, 12) > 7 and path_dist(hx, hy, 8) > 4.5 and GROUND.free(hx, hy, 4.0) and slope(hx, hy) < .35:
        srot = face(hx, hy, sxx, syy + 20)
        small_hut("BLD_Sauna", hx, hy, srot, 4.0, 3.6, 2.3, M["log_sauna"], ROOFS["slate"], "sauna")
        dock("DOCK_Sauna", sxx, syy - 2.0, srot, 7.0, width=1.6, deck_z=.8)
        print("[logic] sauna at", round(hx, 1), round(hy, 1))
        break

# smokehouse at the east end of the harbour (downwind of the village, prevailing wind from the south-west)
for hx, hy in ((72.0, SY - 6), (74.0, SY - 10), (70.0, SY - 4), (76.0, SY - 6), (68.0, SY - 8)):
    wx_, wy_, _ = BLD["ware"]
    if math.hypot(hx - wx_, hy - wy_) < 16:
        continue
    if (GROUND.free(hx, hy, 3.5) and path_dist(hx, hy, 8) > 3.5 and .6 < H(hx, hy) < 5 and slope(hx, hy) < .35
            and not excluded(hx, hy)):
        small_hut("BLD_Smokehouse", hx, hy, face(hx, hy, hx - 6, SY + 20), 3.2, 3.2, 2.2, M["soot"], ROOFS["slate"], "smoke")
        print("[logic] smokehouse at", hx, hy)
        break

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
progress("village done")

# ---------------------------------------------------------------- Forgotten Isle
progress("Forgotten Isle")
cab_x, cab_y = isle_world(7, -2)
cab_rot = math.atan2(-ISLE_SOUTH[0], ISLE_SOUTH[1]) + .15
house("BLD_AbandonedCabin", cab_x, cab_y, 6, 5, 2.6, WALLS["aban"], ROOFS["aban"], ridge='x',
      tilt=(.035, -.03), rot=cab_rot, glass=M["myst"], coll_=C_ISLE, chimney=True)
dsx, dsy = shore_point(*isle_world(5, -9), *ISLE_SOUTH)
dock_ang = math.atan2(-ISLE_SOUTH[0], ISLE_SOUTH[1])
dock_start = (dsx - ISLE_SOUTH[0] * 2.5, dsy - ISLE_SOUTH[1] * 2.5)
isle_dock_end = dock("DOCK_ForgottenIsle_Broken", dock_start[0], dock_start[1], dock_ang, 11,
                     width=2.2, deck_z=.85, broken=.28, coll_=C_ISLE, wood=M["wood_old"])
inst(LANTERN, "PROP_IsleLantern", C_ISLE, (isle_dock_end[0] + 1.0, isle_dock_end[1], .85), dock_ang, 1.0, (.06, 0))

scx, scy = isle_world(-15, -1); scz = H(scx, scy)
for i in range(7):
    a = i / 7 * 6.283
    st = MB()
    st.ico((0, 0, 1.0), 1.0, M["rock_dark"], sub=1, scale=(.55, .4, 1.4), jitter=.15, seed=i)
    px, py = scx + math.cos(a) * 4.5, scy + math.sin(a) * 4.5
    st.obj(f"ISLE_Stone_{i}", C_ISLE, (px, py, H(px, py) - .3), a, (rng.uniform(-.12, .12), rng.uniform(-.12, .12)))
ob = MB()
ob.cone((0, 0, 1.8), .55, .25, 3.6, M["rock_dark"], seg=4)
for z in (1.2, 2.0, 2.7):
    ob.box((0, .42 - z * .05, z), (.22, .1, .35), M["myst"])
ob.obj("ISLE_Obelisk", C_ISLE, (scx, scy, scz - .2), .3)
EXCL.append((scx, scy, 6.5))
for i in range(6):                      # faint floating lights around the circle
    a = rng.uniform(0, 6.28); d = rng.uniform(1.5, 6)
    px, py = scx + math.cos(a) * d, scy + math.sin(a) * d
    orb = MB(); orb.ico((0, 0, 0), .12, M["myst_soft"], sub=1)
    orb.obj(f"ISLE_Wisp_{i}", C_ISLE, (px, py, H(px, py) + rng.uniform(1.0, 2.4)))


rr = random.Random(77); placed = 0
for i in range(500):                    # dark spruces and snags on the Forgotten Isle
    if placed >= 34:
        break
    u, v = rr.uniform(-34, 24), rr.uniform(-14, 16)
    x, y = isle_world(u, v); h = H(x, y)
    if h < 1.0 or excluded(x, y) or path_dist(x, y, 4) < 2.2 or slope(x, y) > 1.1:
        continue
    dead = rr.random() < .22
    s = rr.uniform(.6, .95); rad = (1.8 if dead else 2.4) * s
    if not CANOPY.free(x, y, rad) or not GROUND.free(x, y, .6):
        continue
    me_ = rr.choice(DEADS) if dead else rr.choice(ISLE_SPRUCE)
    inst(me_, f"TREE_Isle_{placed:02d}", C_ISLE, (x, y, h - .25), rr.uniform(0, 6.28),
         (s, s, s * rr.uniform(.95, 1.15)), (rr.uniform(-.06, .06), rr.uniform(-.06, .06)))
    CANOPY.add(x, y, rad); GROUND.add(x, y, .6); placed += 1
k = 0
for i in range(300):                    # dark rocks on the ridge
    if k >= 24:
        break
    u, v = rr.uniform(-22, 12), rr.uniform(2, 11)
    x, y = isle_world(u, v); h = H(x, y)
    if h < .5 or excluded(x, y) or slope(x, y) < .5:
        continue
    s = rr.uniform(.8, 2.2)
    if path_dist(x, y, 5) < s + .8:
        continue
    if not GROUND.free(x, y, s * 1.1):
        continue
    hs_ = [H(x + dx_ * s, y + dy_ * s) for dx_, dy_ in ((1, 0), (-1, 0), (0, 1), (0, -1), (0, 0))]
    hlow = min(hs_)
    if hlow + 1.3 * s < max(hs_) + .1:
        continue               # too steep: the rock would sink into the slope
    inst(ROCKS[1 + 2 * (k % 2)], f"ROCK_Isle_{k:02d}", C_ISLE, (x, y, hlow + s * .6), rr.uniform(0, 6.28), s,
         (rr.uniform(-.2, .2), rr.uniform(-.2, .2)))
    GROUND.add(x, y, s * 1.1); k += 1
k = 0; kf = 0
for i in range(400):                    # undergrowth: ferns and a few glowing mushrooms
    if k >= 10 and kf >= 22:
        break
    u, v = rr.uniform(-30, 20), rr.uniform(-12, 14)
    x, y = isle_world(u, v); h = H(x, y)
    if h < 1.0 or excluded(x, y) or path_dist(x, y, 3) < 1.0 or slope(x, y) > .8:
        continue
    if k < 10 and rr.random() < .35:
        if not GROUND.free(x, y, .5):
            continue
        inst(SHROOMS[k % 2], f"SHROOM_Isle_{k:02d}", C_ISLE, (x, y, h - .02), rr.uniform(0, 6.28), rr.uniform(.9, 1.4))
        GROUND.add(x, y, .5); k += 1
    elif kf < 22:
        if not GROUND.free(x, y, .9):
            continue
        inst(FERNS[1 + 2 * (kf % 2)], f"FERN_Isle_{kf:02d}", C_ISLE, (x, y, h - .05), rr.uniform(0, 6.28), rr.uniform(.8, 1.2))
        GROUND.add(x, y, .9); kf += 1

# landmark: one huge dead tree on the isle, visible from all around the lake (about 27 m)
best = None
for uu in range(-22, 23, 2):
    for vv in range(-12, 13, 2):
        gx_, gy_ = isle_world(uu, vv)
        if math.hypot(gx_ - cab_x, gy_ - cab_y) < 9 or not GROUND.free(gx_, gy_, 1.6) or path_dist(gx_, gy_, 5) < 2.5:
            continue
        hh = H(gx_, gy_)
        if best is None or hh > best[2]:
            best = (gx_, gy_, hh)
if best:
    # silver dead pine ("kelo"): thick slightly twisted trunk, a few heavy broken limbs turning upward, jagged top
    r_g = random.Random(4242); mb = MB(); pnt = Vector((0, 0, -.6)); dvec = Vector((0, 0, 1)); rad = 1.0
    segs = (6.0, 5.5, 5.0, 4.0)
    for i, L_ in enumerate(segs):
        dvec = (dvec + Vector((r_g.uniform(-.1, .1), r_g.uniform(-.1, .1), 0))).normalized()
        mb.cone_dir(pnt, dvec, L_, rad, rad * .78, M["snag"], seg=8); pnt = pnt + dvec * L_; rad *= .78
    for k_ in range(3):                                               # jagged broken top
        a = k_ * 2.1 + .4
        mb.cone_dir(pnt - dvec * .2, (math.cos(a) * .25, math.sin(a) * .25, 1), r_g.uniform(.8, 1.8), rad * .55, .02,
                    M["snag"], seg=4)
    for j in range(5):                                                # heavy limbs, broken off, bending upward
        hz = r_g.uniform(8, 17); a = j * 1.3 + r_g.uniform(-.3, .3)
        q = Vector((0, 0, hz)); L1 = r_g.uniform(1.6, 3.0)
        d1 = Vector((math.cos(a), math.sin(a), r_g.uniform(.1, .4))).normalized()
        mb.cone_dir(q, d1, L1, .3, .2, M["snag"], seg=6)
        q2 = q + d1 * L1
        mb.cone_dir(q2, (d1.x * .5, d1.y * .5, 1), r_g.uniform(1.0, 2.4), .2, .04, M["snag"], seg=5)
    for k_ in range(4):                                               # root flare
        a = k_ * 1.57 + .3
        mb.cone_dir((math.cos(a) * .5, math.sin(a) * .5, .3), (math.cos(a), math.sin(a), -.35), 1.6, .45, .1,
                    M["snag"], seg=5)
    mb.obj("TREE_IsleDeadGiant", C_ISLE, (best[0], best[1], best[2] - .1), r_g.uniform(0, 6.28))
    GROUND.add(best[0], best[1], 1.8); CANOPY.add(best[0], best[1], 2.5)
    print("[logic] isle dead giant at", round(best[0], 1), round(best[1], 1))

# small islands and skerries: grouped trees on the high part, rock rims along the waterline
ISLE_PLAN = {"Isle_West": ("P", "P", "P", "S", "S"), "Isle_East": ("P", "P", "B"),
             "Isle_NorthEast": ("P",), "Isle_Rock": (), "Skerry_1": ("P",), "Skerry_2": (),
             "Skerry_3": ("P",), "Skerry_4": ()}
for nm, ix, iy, S, top, el, ang, lobes in SMALL_ISLES:
    rr = random.Random(sum(map(ord, nm)))
    c, s_ = math.cos(ang), math.sin(ang)
    plan = ISLE_PLAN.get(nm, ())
    t = 0
    for i in range(80):                 # trees cluster on the island's crown
        if t >= len(plan):
            break
        uu, vv = rr.gauss(0, S * .35 * el), rr.gauss(0, S * .3)
        x, y = ix + uu * c - vv * s_, iy + uu * s_ + vv * c
        h = H(x, y)
        kind = plan[t]
        sc_ = rr.uniform(.55, .8) if kind == "P" else rr.uniform(.5, .7)
        rad = R_KIND[kind] * sc_ * .75
        if h < .7 or not CANOPY.free(x, y, rad) or not GROUND.free(x, y, .6):
            continue
        me_ = rr.choice(KIND_LIST[kind]); rz = rr.uniform(0, 6.28)
        inst(me_, f"TREE_{nm}_{t}", C_ISLANDS, (x, y, h - .25), rz, sc_, lean_tilt(x, y, rz, lake_d(x, y), kind))
        CANOPY.add(x, y, rad); GROUND.add(x, y, .6); t += 1
    k = 0
    for i in range(160):                # rocks along the waterline, a couple of bigger ones
        if k >= 5 + int(S * 1.2):
            break
        a = rr.uniform(0, 6.28); rr_ = S * rr.uniform(.75, 1.15)
        uu, vv = math.cos(a) * rr_ * el, math.sin(a) * rr_
        x, y = ix + uu * c - vv * s_, iy + uu * s_ + vv * c
        h = H(x, y)
        if not (-0.8 < h < 1.2):
            continue
        sz = rr.uniform(.5, 1.4) if k > 1 else rr.uniform(1.4, 2.2)
        if not GROUND.free(x, y, sz * 1.05):
            continue
        inst(ROCKS[(k + i) % 5], f"ROCK_{nm}_{k}", C_ISLANDS, (x, y, h - sz * .35), rr.uniform(0, 6.28), sz,
             (rr.uniform(-.25, .25), rr.uniform(-.25, .25)))
        GROUND.add(x, y, sz * 1.05); k += 1
    k = 0
    for i in range(60):                 # heather / shrubs / ferns on top
        if k >= int(S * .8) + 1:
            break
        uu, vv = rr.gauss(0, S * .4 * el), rr.gauss(0, S * .35)
        x, y = ix + uu * c - vv * s_, iy + uu * s_ + vv * c
        h = H(x, y)
        if h < .5 or not GROUND.free(x, y, .9):
            continue
        me_ = HEATHER[k % 2] if nm.startswith(("Skerry", "Isle_Rock")) else (BUSHES[k % 3] if k % 2 else FERNS[k % 4])
        inst(me_, f"BUSH_{nm}_{k}", C_ISLANDS, (x, y, h - .08), rr.uniform(0, 6.28), rr.uniform(.7, 1.1))
        GROUND.add(x, y, .9); k += 1
progress("Forgotten Isle and islands done")

# ---------------------------------------------------------------- scatter
CNT = {k: 0 for k in ("tree", "sapling", "log", "stump", "fern", "bush", "heather", "shroom",
                      "grass", "flower", "rock", "reed")}
TREE_PTS = []


def sprinkle(n, fn, seed, area=(-196.0, 196.0, -196.0, 196.0)):
    """Uniform random candidates (no grid pattern); fn decides and reserves space."""
    r = random.Random(seed)
    for _ in range(n):
        fn(r.uniform(area[0], area[1]), r.uniform(area[2], area[3]), r)


def ground_ok(x, y, rad, path_pad=1.0, creek_pad=1.6):
    return (not in_island(x, y, 2) and not excluded(x, y) and path_dist(x, y, 4) >= path_pad
            and CGRID.dist(x, y, 4) >= creek_pad and GROUND.free(x, y, rad))


FETCH = {}


def fetch(x, y):
    """Open water upwind (prevailing wind from the SW), in metres: small = sheltered shore."""
    key = (round(x / 4), round(y / 4))
    if key not in FETCH:
        dist = 0.0
        while dist < 150:
            dist += 3.0
            if H(x - .707 * dist, y - .707 * dist) > .05:
                break
        FETCH[key] = dist
    return FETCH[key]


def tree_fn(x, y, r):
    cov = forest_cover(x, y)
    if cov < .02 or r.random() > cov:
        return
    if in_island(x, y, 3) or excluded(x, y):
        return
    h = H(x, y)
    if h < 1.0:
        return
    pd = path_dist(x, y, 8)
    if pd < 2.8 or CGRID.dist(x, y, 4) < 2.4:
        return
    d, sl, moist, dry = site(x, y, h)
    if sl > 1.0:
        return
    edge = 1 - ss(.35, .8, cov)
    w = {"S": max(.02, .35 + .9 * ss(.5, .9, cov) + .4 * moist - .7 * dry + .25 * ss(60, 130, y)),
         "P": .15 + 1.1 * dry + .6 * ss(1.12, 1.0, d),
         "B": .08 + .9 * edge * ss(.1, .3, cov) + .6 * ss(8, 1, CGRID.dist(x, y, 9)) + .3 * village_core(x, y),
         "D": .03 + .05 * edge + .12 * ss(.7, .95, cov)}
    q = r.random() * sum(w.values())
    for kind, wk in w.items():
        q -= wk
        if q <= 0:
            break
    if kind in "SP" and h < 1.6 and dry < .6:
        return                       # no conifers right at the waterline (alders grow there instead)
    maturity = ss(.25, .9, cov) * (.75 + .25 * (.5 + .5 * fbm(x / 20, y / 20, 2, 33)))
    s = lerp(.62, 1.1, maturity) * r.uniform(.88, 1.12)       # young trees at the edges, big inside
    if kind == "S" and (pd < 9 or d < 1.15):
        s *= .85
    rad = R_KIND[kind] * s
    if not CANOPY.free(x, y, rad) or not GROUND.free(x, y, .6):
        return
    me_ = r.choice(KIND_LIST[kind]); rz = r.uniform(0, 6.28)
    CNT["tree"] += 1
    inst(me_, f"TREE_{me_.name}_{CNT['tree']:04d}", C_TREES, (x, y, h - .25), rz,
         (s, s, s * r.uniform(.92, 1.1)), lean_tilt(x, y, rz, d, kind))
    CANOPY.add(x, y, rad); GROUND.add(x, y, .6)
    TREE_PTS.append((x, y, kind, s))


def sapling_fn(x, y, r):
    cov = forest_cover(x, y)
    edge_band = .2 < cov < .5
    if not (cov >= .55 or edge_band) or r.random() > (.45 if edge_band else .3):
        return
    h = H(x, y)
    if h < 1.2 or not CANOPY.free(x, y, .2) or not ground_ok(x, y, .9, 2.0, 2.2):
        return
    s = r.uniform(.7, 1.2)
    CNT["sapling"] += 1
    inst(r.choice(YOUNG), f"TREE_Sapling_{CNT['sapling']:04d}", C_TREES, (x, y, h - .1), r.uniform(0, 6.28), s)
    CANOPY.add(x, y, 1.0 * s); GROUND.add(x, y, .5)


def log_fn(x, y, r):
    cov = forest_cover(x, y)
    if cov < .55 or r.random() > .3:
        return
    h = H(x, y)
    if h < 1.2 or slope(x, y) > .5 or not ground_ok(x, y, 3.6, 2.0, 2.0):
        return
    CNT["log"] += 1
    inst(r.choice(LOGS), f"LOG_{CNT['log']:03d}", C_TREES, (x, y, h - .12), r.uniform(0, 6.28), r.uniform(.8, 1.1))
    GROUND.add(x, y, 3.6)


def stump_fn(x, y, r):
    cov = forest_cover(x, y); vc = village_core(x, y)
    if not (.08 < cov < .7 or .15 < vc < .7) or r.random() > .25:
        return
    h = H(x, y)
    if h < 1.2 or not ground_ok(x, y, .8, 1.5):
        return
    CNT["stump"] += 1
    inst(r.choice(STUMPS), f"STUMP_{CNT['stump']:03d}", C_TREES, (x, y, h - .1), r.uniform(0, 6.28), r.uniform(.8, 1.2))
    GROUND.add(x, y, .8)


def rock_fn(x, y, r):
    h = H(x, y)
    sl = slope(x, y); ew = east_w(x, y); cov = forest_cover(x, y)
    if -0.9 < h < 1.3:
        p, s, mossy = .07 * (1 + fbm(x / 15, y / 15, 2, 17)), r.uniform(.5, 1.5), False
    elif ew > .35 and sl > .45 and h > 1:
        p, s, mossy = .45, r.uniform(1.8, 4.5), False
    elif h > 1.5 and fbm(x / 40, y / 40, 2, 77) > .42 and village_core(x, y) < .3:
        p, s, mossy = .3, r.uniform(1.2, 3.0), cov > .4
    elif h > 18:
        p, s, mossy = .05, r.uniform(1.2, 3.0), False
    elif cov > .45:
        p, s, mossy = .035, r.uniform(.8, 1.8), True
    else:
        return
    if r.random() > p or not ground_ok(x, y, s * 1.05, 1.0, 1.0):
        return
    CNT["rock"] += 1
    me_ = r.choice(MOSSROCKS) if mossy else r.choice(ROCKS)
    inst(me_, f"ROCK_{CNT['rock']:04d}", C_ROCKS, (x, y, h - s * .3), r.uniform(0, 6.28), s,
         (r.uniform(-.2, .2), r.uniform(-.2, .2)))
    GROUND.add(x, y, s * 1.05)


def fern_fn(x, y, r):
    if CNT["fern"] >= 1400:
        return
    cov = forest_cover(x, y)
    if cov < .3:
        return
    h = H(x, y)
    if h < 1.1:
        return
    d, sl, moist, dry = site(x, y, h)
    if sl > .55:
        return
    if r.random() > .55 * ss(.3, .8, cov) * (.35 + .8 * moist) * (1 - .6 * min(1.0, dry)):
        return
    if not ground_ok(x, y, .9, 1.0):
        return
    CNT["fern"] += 1
    inst(r.choice(FERNS), f"FERN_{CNT['fern']:04d}", C_BUSH, (x, y, h - .05), r.uniform(0, 6.28), r.uniform(.8, 1.4))
    GROUND.add(x, y, .9)


def bush_fn(x, y, r):
    cov = forest_cover(x, y); vc = village_core(x, y)
    edge = 1 - ss(.35, .8, cov)
    p = .65 * edge * ss(.05, .3, cov) + .25 * vc * (1 - vc) * 4 + .15 * ss(3, .5, CGRID.dist(x, y, 4))
    if r.random() > p:
        return
    h = H(x, y)
    if h < 1.1 or not ground_ok(x, y, 1.0, 1.0, 1.0):
        return
    CNT["bush"] += 1
    inst(r.choice(BUSHES), f"BUSH_{CNT['bush']:04d}", C_BUSH, (x, y, h - .12), r.uniform(0, 6.28), r.uniform(.7, 1.3))
    GROUND.add(x, y, 1.0)


def heather_fn(x, y, r):
    h = H(x, y)
    if h < 1.5:
        return
    d, sl, moist, dry = site(x, y, h)
    if r.random() > .35 * min(1.0, dry) * ss(.75, .4, forest_cover(x, y)):
        return
    if not ground_ok(x, y, .9, 1.0):
        return
    CNT["heather"] += 1
    inst(r.choice(HEATHER), f"HEATHER_{CNT['heather']:03d}", C_BUSH, (x, y, h - .05), r.uniform(0, 6.28), r.uniform(.8, 1.3))
    GROUND.add(x, y, .9)


def shroom_fn(x, y, r):
    if CNT["shroom"] >= 45:
        return
    cov = forest_cover(x, y)
    if cov < .7 or r.random() > .1:
        return
    h = H(x, y)
    if h < 1.2:
        return
    d, sl, moist, dry = site(x, y, h)
    if moist < .35 or not ground_ok(x, y, .5, 1.5):
        return
    CNT["shroom"] += 1
    inst(r.choice(SHROOMS), f"SHROOM_{CNT['shroom']:03d}", C_BUSH, (x, y, h - .02), r.uniform(0, 6.28), r.uniform(.8, 1.3))
    GROUND.add(x, y, .5)


def grass_fn(x, y, r):
    h = H(x, y)
    if not (1.1 < h < 16):
        return
    cov = forest_cover(x, y); vc = village_core(x, y)
    p = (.6 * ss(0.0, 0.35, fbm(x / 20, y / 20, 2, 91)) + .25 * ss(.2, .8, vc) * ss(.9, .5, vc)) * ss(.45, .15, cov)
    if r.random() > p or slope(x, y) > .5 or not ground_ok(x, y, .8, 1.2):
        return
    CNT["grass"] += 1
    inst(r.choice(TALLGRASS), f"GRASS_{CNT['grass']:04d}", C_BUSH, (x, y, h - .05), r.uniform(0, 6.28), r.uniform(.7, 1.3))
    GROUND.add(x, y, .8)


def flower_fn(x, y, r):
    h = H(x, y)
    if not (1.2 < h < 10):
        return
    meadow = ss(30, 10, math.hypot(x - MEADOW[0], y - MEADOW[1]))
    glade = max(ss(g[2], g[2] * .3, math.hypot(x - g[0], y - g[1])) for g in GLADES)
    p = (.15 * ss(0.05, 0.4, fbm(x / 25, y / 25, 2, 13)) + .5 * meadow + .45 * glade) \
        * ss(.35, .05, forest_cover(x, y) * (1 - glade))
    if r.random() > p or slope(x, y) > .45 or not ground_ok(x, y, .8, .8):
        return
    CNT["flower"] += 1
    inst(r.choice(FLOWERS), f"FLOWERS_{CNT['flower']:04d}", C_BUSH, (x, y, h - .05), r.uniform(0, 6.28), r.uniform(.8, 1.2))
    GROUND.add(x, y, .8)


def reed_fn(x, y, r):
    h = H(x, y)
    if not (-1.4 < h < -0.12) or excluded(x, y, 1.5) or fetch(x, y) > 70:
        return                       # reeds only in sheltered bays
    if r.random() > .6 * ss(.0, .3, fbm(x / 18, y / 18, 2, 11)) or not GROUND.free(x, y, .8):
        return
    CNT["reed"] += 1
    inst(REEDS, f"REEDS_{CNT['reed']:04d}", C_REEDS, (x, y, h), r.uniform(0, 6.28), r.uniform(.75, 1.25))
    GROUND.add(x, y, .8)


# ---------------------------------------------------------------- points of interest (phase B blockout)
progress("points of interest")
import json
PLAN = {it["id"]: it for it in json.load(open(os.path.join(OUT_DIR, "plan", "map_plan.json"), encoding="utf-8"))["items"]}
def PP(i):
    return PLAN[i]["x"], PLAN[i]["y"]

C_POI = coll("PointsOfInterest", ROOT)
C_POI_V = coll("POI_Village", C_POI); C_POI_F = coll("POI_Forest", C_POI); C_POI_G = coll("POI_AncientGrove", C_POI)
C_POI_E = coll("POI_EasternCliffs", C_POI); C_POI_L = coll("POI_Lake", C_POI); C_POI_I = coll("POI_ForgottenIsle", C_POI)
C_NIGHT = coll("NightHooks", C_MARK)

for k_, col_, ro_, em_ in (("sign_paint", C(.86, .83, .74), .9, 0), ("sign_red", C(.62, .18, .14), .9, 0),
                           ("scratch_txt", C(.78, .74, .66), .9, 0), ("paper", C(.86, .82, .68), .95, 0),
                           ("awning", C(.20, .45, .50), .8, 0), ("ice", C(.80, .92, .95), .2, 0),
                           ("fish", C(.70, .74, .78), .35, 0), ("rust", C(.50, .28, .16), .7, 0),
                           ("char", C(.08, .07, .06), .95, 0), ("ash", C(.45, .44, .42), .95, 0),
                           ("gouge", C(.66, .50, .32), .9, 0), ("symbol", C(.35, .85, .75), .6, .35),
                           ("glowplant", C(.45, .65, 1.0), .5, 1.6), ("cloth", C(.35, .32, .22), .95, 0),
                           ("map_blue", C(.12, .25, .38), .9, 0), ("cave", C(.02, .02, .02), 1.0, 0),
                           ("falls", C(.55, .78, .82), .1, 0), ("foam", C(.92, .95, .96), .6, 0),
                           ("pond", C(.10, .22, .24), .05, 0)):
    M[k_] = mat("M_" + "".join(w.capitalize() for w in k_.split("_")), col_, ro_, emit=em_,
                alpha=(.8 if k_ in ("falls", "pond") else 1.0))


def text_mesh(name, body, size, parent, loc, mat_, rot=(math.pi / 2, 0, math.pi)):
    """Real text turned into a mesh (so it exports to Unity), parented to its board."""
    cu = bpy.data.curves.new(name + "_crv", 'FONT'); cu.body = body; cu.size = size
    cu.align_x = 'CENTER'; cu.align_y = 'CENTER'; cu.extrude = .004
    tmp = bpy.data.objects.new(name + "_tmp", cu); scene.collection.objects.link(tmp)
    bpy.context.view_layer.update()
    me_ = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(tmp); bpy.data.curves.remove(cu)
    me_.name = name; me_.materials.clear(); me_.materials.append(mat_)
    ob = bpy.data.objects.new(name, me_); ob.location = loc; ob.rotation_euler = rot
    parent.users_collection[0].objects.link(ob); ob.parent = parent
    return ob


def sign_board(name, coll_, x, y, rot, lines, tilt=(0, 0), size=.13, post_h=1.6, two_posts=True,
               scratched=None, board=None, txt=None, z=None, reserve=True):
    """Old weathered wooden sign: posts, board, moss on top, painted text (and optional scratched text)."""
    zg = H(x, y) if z is None else z
    tw = max(len(l) for l in lines) * size * .62 + .35
    bh = len(lines) * size * 1.7 + .25 + (size * 1.4 if scratched else 0)
    mb = MB()
    for px in ((-tw / 2 + .12, tw / 2 - .12) if two_posts else (0,)):
        mb.box((px, -.07, (post_h + bh / 2 - .4) / 2), (.12, .12, post_h + bh / 2 + .4), M["wood_dark"])
    mb.box((0, 0, post_h), (tw, .06, bh), board or M["wood_old"], rot=(0, .03, 0))
    mb.box((-tw * .2, .0, post_h + bh / 2 + .03), (tw * .45, .09, .06), M["moss_dark"])
    mb.box((tw * .18, .033, post_h - bh * .28), (tw * .45, .005, .014), M["char"], rot=(0, .22, 0))     # crack
    for nx_ in ((-tw / 2 + .12, tw / 2 - .12) if two_posts else (0,)):
        for nz_ in (post_h + bh * .3, post_h - bh * .3):
            mb.box((nx_, .035, nz_), (.03, .01, .03), M["rust"])                                   # rusty nails
    ob = mb.obj(name, coll_, (x, y, zg), rot, tilt)
    top = post_h + bh / 2 - .12 - size * .6
    for i, l in enumerate(lines):
        text_mesh(f"{name}_Text{i}", l, size, ob, (0, .035, top - i * size * 1.7), txt or M["sign_paint"])
    if scratched:
        text_mesh(f"{name}_Scratched", scratched, size * .8, ob, (.08, .035, top - len(lines) * size * 1.7 - .02),
                  M["scratch_txt"], rot=(math.pi / 2, .06, math.pi))
    if reserve:
        GROUND.add(x, y, tw / 2 + .3); EXCL.append((x, y, tw / 2 + .6))
    return ob


ALLPATH = []
for nm_, pts_, w_, k_ in PATHS:
    dn = catmull(pts_, 1.5)
    for i_ in range(len(dn)):
        ALLPATH.append((dn[i_], dn[min(len(dn) - 1, i_ + 1)] - dn[max(0, i_ - 1)], nm_, w_))


def beside_path(x, y, off, path=None):
    """Nearest path point to (x,y), pushed `off` metres to the side (x,y side); returns (px, py, rot facing the path)."""
    best = min((a for a in ALLPATH if path is None or a[2] == path), key=lambda a: (a[0].x - x) ** 2 + (a[0].y - y) ** 2)
    p, t, _, w = best; t = t.normalized() if t.length else Vector((1, 0)); n = Vector((-t.y, t.x))
    if n.dot(Vector((x - p.x, y - p.y))) < 0:
        n = -n
    q = p + n * (w / 2 + off)
    return q.x, q.y, face(q.x, q.y, p.x, p.y)


def proto_old_pine(v, giant=False):
    """Straight old pine (bare tall trunk) - used for marked / poster trees and the grove giants."""
    r = random.Random(3000 + v * 11 + (100 if giant else 0)); mb = MB()
    Ht = r.uniform(17, 21) if giant else r.uniform(13, 16); rad = .9 if giant else .5
    mb.cone((0, 0, Ht * .4), rad, rad * .45, Ht * .8, M["cp_bark"], seg=10)
    d = Vector((r.uniform(-.1, .1), r.uniform(-.1, .1), 1)).normalized()
    top = Vector((0, 0, Ht * .8)) + d * Ht * .2
    mb.cone_dir((0, 0, Ht * .8), d, Ht * .21, rad * .45, rad * .25, M["cp_bark"], seg=8)
    pad = M["cp_pad"]

    def needle_pad(c, R):
        for dz0, dz1, f in ((-.35, .45, 1.0), (.15, .85, .78), (.6, 1.2, .5)):
            star_skirt(mb, c.x + r.uniform(-.15, .15), c.y + r.uniform(-.15, .15), c.z + dz1, c.z + dz0,
                       R * f, 8, r.uniform(0, 6.28), pad, r, inner=.6, jit=.14)

    needle_pad(top, 2.6 if giant else 2.1)
    for j in range(7 if giant else 5):
        a = j * 6.283 / (7 if giant else 5) + r.uniform(-.4, .4)
        base = Vector((0, 0, Ht * r.uniform(.66, .82)))
        e = r.uniform(.2, .55); L = r.uniform(2.0, 3.4) * (1.3 if giant else 1)
        ad = Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e)))
        mb.cone_dir(base, ad, L, rad * .35, rad * .15, M["cp_bark"], seg=5)
        needle_pad(base + ad * L, r.uniform(1.6, 2.3) * (1.2 if giant else 1))
    if giant:
        for k in range(8):
            a = k / 8 * 6.283 + r.uniform(-.2, .2)
            mb.cone_dir((0, 0, .9), (math.cos(a), math.sin(a), -.45), r.uniform(2.6, 3.6), .6, .1, M["cp_bark"], seg=6)
    me_ = keep_proto(mb.mesh(f"OldPine_{'Giant_' if giant else ''}{v}"))
    OLDPINE[me_.name] = (Ht, rad)
    return me_

OLDPINE = {}
OLD_PINES = [proto_old_pine(v) for v in range(2)]
GIANT_PINES = [proto_old_pine(v, True) for v in range(3)]


def trunk_r(me_, s, z):
    Ht, rad = OLDPINE[me_.name]
    return rad * s * (1 - .55 * min(1.0, z / (Ht * s * .8)))


def place_tree_poi(me_, name, coll_, x, y, s=1.0, rz=0.0):
    inst(me_, name, coll_, (x, y, H(x, y) - .3), rz, s)
    CANOPY.add(x, y, 3.0 * s); GROUND.add(x, y, OLDPINE[me_.name][1] * s + .4); EXCL.append((x, y, 1.2 * s))


def marks_on_trunk(name, coll_, x, y, me_, s, toward, z0, z1, n=4, mat_=None, symbol=False):
    """Deep parallel gouges (or a carved symbol) on the side of a trunk facing `toward`."""
    a = math.atan2(toward[1] - y, toward[0] - x); mb = MB(); zc = H(x, y) - .3
    zz = (z0 + z1) / 2; r = trunk_r(me_, s, zz) + .02
    cx, cy = math.cos(a) * r, math.sin(a) * r
    if symbol:
        for k, (dx_, dz_, rr) in enumerate(((0, 0, .0), (0, .18, 1.57), (0, -.18, 1.57), (.0, 0, .785))):
            mb.box((cx, cy, zz + dz_), (.05, .32, .04), mat_ or M["gouge"], rot=(rr, 0, a))
    else:
        for k in range(n):
            off = (k - (n - 1) / 2) * .09
            mb.box((cx - math.sin(a) * off, cy + math.cos(a) * off, zz), (.05, .04, z1 - z0), mat_ or M["gouge"],
                   rot=(0, .12, a))
    mb.obj(name, coll_, (x, y, zc), 0.0)


# ---------------- Village
sx_, sy_, sr_ = BLD["shop"]; shop_z = H(sx_, sy_) - .05
x, y = PP("V1"); r_ = face(x, y, *SQ)
mb = MB()
mb.box((0, .6, .5), (3.0, .8, 1.0), M["wood"]); mb.box((0, .6, 1.02), (3.2, .95, .06), M["wood_dark"])
for px in (-1.6, 1.6):
    for py in (-1.1, 1.1):
        mb.box((px, py, 1.25), (.12, .12, 2.5), M["wood_dark"])
mb.box((0, .2, 2.55), (3.6, 2.9, .08), M["awning"], rot=(-.2, 0, 0))
for k in range(4):
    mb.box((-1.35 + k * .9, .2, 2.6), (.35, 2.9, .03), M["trim"], rot=(-.2, 0, 0))
for k in range(3):
    cx = -1.0 + k * 1.0
    mb.box((cx, .6, 1.12), (.6, .4, .15), M["ice"])
    for f_ in range(3):
        mb.ico((cx - .15 + f_ * .15, .6, 1.22), .06, M["fish"], sub=1, scale=(1, 3, .8))
for k, (lx, ly, lz) in enumerate(((-1.2, -1.6, .15), (-.5, -1.7, .15), (-.85, -1.65, .45))):
    mb.box((lx, ly, lz), (.6, .4, .3), M["wood"])
mb.box((0, 1.16, 2.25), (1.9, .05, .35), M["sign_teal"])
stall = mb.obj("BLD_FishStall", C_POI_V, (x, y, H(x, y)), r_)
text_mesh("BLD_FishStall_Text", "FRESH FISH", .14, stall, (0, 1.2, 2.25), M["sign_paint"])
GROUND.add(x, y, 2.4); EXCL.append((x, y, 2.8))

x, y = PP("V2")
wd = bpy.data.objects["DOCK_West"]; wa = wd.rotation_euler.z
mb = MB()
for t in (4.0, 8.0, 12.0):
    mb.cone((1.35, t, 1.25), .13, .11, .7, M["wood_dark"], seg=10)
    mb.cone((1.35, t, 1.55), .16, .16, .06, M["rust"], seg=10)
mb.obj("PROP_Moorings_West", C_POI_V, tuple(wd.location), wa)
bx_, by_ = l2w(wd.location.x, wd.location.y, wa, 2.6, 9.0)
inst(BOATS[0], "BOAT_Rowboat_Moored", C_POI_V, (bx_, by_, .05), wa + .05)

x, y = PP("V3")
sign_board("SIGN_KeepOffWater", C_POI_V, x, y, face(x, y, x, y - 20), ["KEEP OFF THE WATER", "AFTER SUNSET"],
           tilt=(.02, -.03), txt=M["sign_red"], size=.12)

nbo = bpy.data.objects["STR_NoticeBoard_Square"]
mb = MB(); mb.box((0, 0, 0), (.38, .012, .5), M["paper"], rot=(0, .06, 0))
pos_ = l2w(nbo.location.x, nbo.location.y, nbo.rotation_euler.z, -.05, .09)
poster = mb.obj("NOTE_MissingPoster_Village", C_POI_V, (pos_[0], pos_[1], nbo.location.z + 1.5), nbo.rotation_euler.z)
text_mesh("NOTE_MissingPoster_Village_T0", "MISSING", .07, poster, (0, .008, .14), M["char"])
text_mesh("NOTE_MissingPoster_Village_T1", "Have you seen him?", .03, poster, (0, .008, .02), M["char"])
text_mesh("NOTE_MissingPoster_Village_T2", "Last seen near the lake", .028, poster, (0, .008, -.06), M["char"])

mb = MB()
mb.box((0, 0, 0), (1.5, .03, 1.0), M["paper"])
mb.ico((-.1, .02, 0), .36, M["map_blue"], sub=2, scale=(1.5, .05, 1.0), jitter=.2, seed=5)
mb.ico((.18, .03, .14), .07, M["moss_dark"], sub=1, scale=(1.3, .3, .9))
for k in range(12):
    a = k / 12 * 6.283
    mb.box((.18 + math.cos(a) * .13, .035, .14 + math.sin(a) * .1), (.035, .01, .012), M["sign_red"], rot=(0, -a, 0))
mx_, my_ = l2w(sx_, sy_, sr_, 0, -8 / 2 + WALL_T + .04)
mb.obj("MYST_LakeMap_Shop", C_POI_V, (mx_, my_, shop_z + .45 + 2.8), sr_)

bh = bpy.data.objects["BLD_Boathouse"]
mb = MB()
for k in range(4):
    mb.box((0, k * .12 - .18, 0), (.04, .035, 1.1), M["gouge"], rot=(.25, 0, 0))
gx_, gy_ = l2w(bh.location.x, bh.location.y, bh.rotation_euler.z, -6.5 / 2 - .03, 1.2)
mb.obj("MYST_Scratches_Boathouse", C_POI_V, (gx_, gy_, bh.location.z + 2.2), bh.rotation_euler.z)

x, y = PP("V8"); r_ = face(x, y, x, y + 30)
inst(BENCH, "PROP_Bench_Dock", C_POI_V, (x, y, H(x, y)), r_)
mb = MB()
for k in range(5):
    mb.ico((1.4 + k * .25, -.3 + (k % 2) * .3, .1), .35, M["net"], sub=1, scale=(1, 1, .3), jitter=.3, seed=k)
for k, (lx, ly) in enumerate(((-1.6, -.2), (-2.2, .3), (-1.9, -.1))):
    mb.box((lx, ly, .15 + (.3 if k == 2 else 0)), (.6, .4, .3), M["wood"], rot=(0, 0, k * .3))
mb.obj("PROP_VillageClutter", C_POI_V, (x, y, H(x, y)), r_)
GROUND.add(x, y, 2.6); EXCL.append((x, y, 2.8))

# ---------------- Pinewood Forest
x, y, r_ = beside_path(*PP("F1"), 2.2)
sign_board("SIGN_WoodsAfterDark", C_POI_F, x, y, r_, ["DON'T GO INTO THE WOODS", "AFTER DARK"],
           tilt=(.07, .05), scratched="IT HEARS YOU", size=.12)

cx, cy = PP("F2"); cz = H(cx, cy); mb = MB()
for k in range(9):
    a = k / 9 * 6.283
    mb.ico((math.cos(a) * .6, math.sin(a) * .6, .08), .17, M["rock_dark"], sub=1, jitter=.25, seed=k)
mb.cone((0, 0, .02), .45, .45, .03, M["ash"], seg=12)
for k in range(3):
    a = k * 2.1
    mb.cone_dir((math.cos(a) * .45, math.sin(a) * .45, .06), (-math.cos(a), -math.sin(a), .15), .8, .06, .04, M["char"], seg=5)
ch = (1.6, .3)
mb.box((ch[0], ch[1], .42), (.45, .4, .04), M["cloth"])
mb.box((ch[0] + .2, ch[1], .7), (.04, .4, .5), M["cloth"], rot=(0, -.25, 0))
for lx in (-.2, .2):
    for ly in (-.18, .18):
        mb.box((ch[0] + lx, ch[1] + ly, .21), (.03, .03, .42), M["metal"])
mb.cone_dir((2.3, -.6, 0), (-.25, .2, 1), 2.6, .02, .006, M["wood_dark"], seg=5)
mb.cone((2.2, -.55, .55), .05, .05, .06, M["metal"], seg=8)
mb.box((-.8, 1.2, .1), (.2, .2, .3), M["metal"], rot=(1.25, 0, .4))
mb.box((-.8, 1.2, .1), (.14, .21, .2), M["glass"], rot=(1.25, 0, .4))
mb.box((-1.8, -1.2, .18), (.6, .4, .35), M["wood"]); mb.box((-2.3, -.6, .2), (.6, .4, .35), M["wood"], rot=(0, 1.4, .5))
mb.cone_dir((.9, -1.5, .15), (1, .3, 0), .3, .16, .2, M["metal"], seg=10)
mb.cone_dir((-1.9, .7, .18), (.3, 1, 0), .9, .18, .18, M["cloth"], seg=10)
mb.box((0, -2.6, .8), (2.2, 1.6, .03), M["cloth"], rot=(.9, 0, 0))
for sxx in (-1.05, 1.05):
    mb.cone_dir((sxx, -2.0, 0), (0, -.3, 1), 1.6, .03, .02, M["wood_dark"], seg=4)
mb.box((-1.8, -1.2, .37), (.5, .3, .04), M["moss"]); mb.box((ch[0] + .2, ch[1], .97), (.06, .3, .05), M["moss"])
mb.obj("POI_AbandonedCamp", C_POI_F, (cx, cy, cz), rng.uniform(0, 6.28))
fp = MB(); dirv = Vector((LAKE_C[0] - cx, LAKE_C[1] - cy)).normalized(); side = Vector((-dirv.y, dirv.x))
for k in range(16):                               # long, uneven strides: someone ran toward the lake
    p = Vector((cx, cy)) + dirv * (3.0 + k * 1.25) + side * (.16 if k % 2 else -.16) + side * math.sin(k * .7) * .4
    fp.box((p.x - cx, p.y - cy, H(p.x, p.y) - cz + .006), (.13, .3, .01), M["mud"], rot=(0, 0, math.atan2(dirv.y, dirv.x) - math.pi / 2))
fp.ico((dirv.x * 22.5, dirv.y * 22.5, H(cx + dirv.x * 22.5, cy + dirv.y * 22.5) - cz + .05), .18, M["cloth"], sub=1, scale=(1.3, 1.3, .35))
fp.obj("POI_AbandonedCamp_Footprints", C_POI_F, (cx, cy, cz), 0.0)
GROUND.add(cx, cy, 3.4); EXCL.append((cx, cy, 5.0)); CANOPY.add(cx, cy, 4.0)

x, y, r_ = beside_path(*PP("F3"), 2.6)
tx_, ty_ = x, y; place_tree_poi(OLD_PINES[0], "TREE_PosterPine", C_POI_F, tx_, ty_, 1.0)
px_, py_, pr_ = beside_path(tx_, ty_, 0)
a = math.atan2(py_ - ty_, px_ - tx_); rr_ = trunk_r(OLD_PINES[0], 1.0, 1.6) + .02
mb = MB(); mb.box((0, 0, 0), (.36, .012, .46), M["paper"], rot=(0, -.1, 0))
for k in range(3):
    mb.box((.1 - k * .08, .007, -.2 + k * .02), (.06, .01, .05), M["moss_dark"])
pst = mb.obj("NOTE_MissingPoster_Forest", C_POI_F, (tx_ + math.cos(a) * rr_, ty_ + math.sin(a) * rr_, H(tx_, ty_) + 1.3),
             face(tx_, ty_, px_, py_))
text_mesh("NOTE_MissingPoster_Forest_T0", "MISSING", .065, pst, (0, .008, .13), M["char"])
text_mesh("NOTE_MissingPoster_Forest_T1", "LAST SEEN NEAR THE LAKE", .026, pst, (0, .008, .03), M["char"])

cx, cy = PP("F4")
for k, (dx_, dy_) in enumerate(((0, -4), (7, 3), (-7, 7))):
    x, y = cx + dx_, cy + dy_; s = 1.15
    place_tree_poi(OLD_PINES[k % 2], f"TREE_ClawMarked_{k}", C_POI_F, x, y, s, k * 2.0)
    marks_on_trunk(f"MYST_ClawMarks_{k}", C_POI_F, x, y, OLD_PINES[k % 2], s, (cx, cy - 30), 4.2 + k * .4, 5.6 + k * .4)

x, y, r_ = beside_path(*PP("F5"), 2.4)
mb = MB()
mb.box((0, 0, 1.35), (.2, .2, 3.0), M["wood_old"]); mb.box((.45, 0, 2.7), (1.0, .14, .14), M["wood_old"])
mb.cone((.8, 0, 2.38), .22, .1, .42, M["rust"], seg=12); mb.box((.8, 0, 2.62), (.04, .04, .12), M["metal"])
mb.ico((.8, 0, 2.16), .04, M["metal"], sub=1)
mb.prism((.45, 0, 2.78), (1.2, .5, .3), M["wood_dark"])
bell = mb.obj("POI_WarningBell", C_POI_F, (x, y, H(x, y)), r_, (.04, 0))
mb = MB(); mb.box((0, 0, 0), (1.25, .05, .4), M["wood_old"])
plate = mb.obj("POI_WarningBell_Plate", C_POI_F, (0, .12, 1.25), 0.0)
plate.parent = bell
text_mesh("POI_WarningBell_Text0", "IF YOU HEAR", .08, plate, (0, .03, .08), M["sign_paint"])
text_mesh("POI_WarningBell_Text1", "THREE BELLS, RUN", .08, plate, (0, .03, -.08), M["sign_paint"])
GROUND.add(x, y, 1.2); EXCL.append((x, y, 1.6))

x, y = PP("F6"); rz = 2.3; tl = (.07, -.12); z = H(x, y) + .12
inst(BOATS[2], "POI_ForestBoat", C_POI_F, (x, y, z), rz, 1.0, tl)
BM = Matrix.LocRotScale(Vector((x, y, z)), Euler((tl[0], tl[1], rz)), Vector((1, 1, 1)))
mb = MB()
for k in range(3):
    mb.box((-.22 + k * .22, .1, .645), (.06, 2.1, .02), M["gouge"], rot=(0, 0, .08 * (k - 1)))
for k, (lx, ly) in enumerate(((.4, -1.3), (-.5, .9), (.2, 1.6))):
    mb.ico((lx, ly, .64), .35, M["moss"], sub=1, scale=(1, 1.2, .15), jitter=.3, seed=k)
mo = mb.obj("POI_ForestBoat_Marks", C_POI_F, (x, y, z), rz, tl)
GROUND.add(x, y, 2.6); EXCL.append((x, y, 3.4)); CANOPY.add(x, y, 2.0)
bxc, byc = x, y
for k in range(6):                                # the forest has started to take the boat back
    a = k / 6 * 6.283 + .4; dd = 3.0 + (k % 2) * .8
    x, y = bxc + math.cos(a) * dd, byc + math.sin(a) * dd
    me_ = YOUNG[k % 3] if k == 2 else FERNS[k % 4]
    if GROUND.free(x, y, .8):
        inst(me_, f"{'TREE_Sapling_Boat' if k == 2 else 'FERN_Boat'}_{k}", C_POI_F, (x, y, H(x, y) - .05), a, .9)
        GROUND.add(x, y, .8)

ci = min(range(len(CREEK_D)), key=lambda i: (CREEK_D[i] - Vector((-62.0, -125.0))).length)
cp = CREEK_D[ci]; ct = (CREEK_D[ci + 1] - CREEK_D[ci - 1]).normalized(); cn = Vector((-ct.y, ct.x))
for k in range(5):
    q = cp + cn * (-1.6 + k * .8) + ct * (.25 if k % 2 else -.25)
    inst(ROCKS[k % 5], f"ROCK_SteppingStone_{k}", C_POI_F, (q.x, q.y, H(cp.x, cp.y) + .12), rng.uniform(0, 6.28),
         (.42, .38, .25))
    GROUND.add(q.x, q.y, .4)
for i, p in enumerate(CREEK_D[6:-6:7]):
    if (p - cp).length < 4:
        continue
    q = p + Vector((rng.uniform(-.5, .5), rng.uniform(-.5, .5)))
    if GROUND.free(q.x, q.y, .5):
        inst(ROCKS[i % 5], f"ROCK_Creekbed_{i:02d}", C_POI_F, (q.x, q.y, H(q.x, q.y) + .05), rng.uniform(0, 6.28),
             rng.uniform(.35, .6))
        GROUND.add(q.x, q.y, .5)

hx, hy = PP("F8")
lx_, ly_ = LAKE_C[0] - hx, LAKE_C[1] - hy; L_ = math.hypot(lx_, ly_)
sx2, sy2 = shore_point(hx - lx_ / L_ * 6, hy - ly_ / L_ * 6, lx_ / L_, ly_ / L_)
hang = face(sx2, sy2, sx2 + lx_, sy2 + ly_)
hidden_end = dock("DOCK_HiddenCove", sx2 - lx_ / L_ * 2, sy2 - ly_ / L_ * 2, hang, 6, width=1.6, deck_z=.75,
                  broken=.08, coll_=C_POI_F, wood=M["wood_old"])
inst(BARREL, "PROP_HiddenCove_Bucket", C_POI_F, (sx2 - lx_ / L_ * 3, sy2 - ly_ / L_ * 3 + 1.2,
                                                 H(sx2 - lx_ / L_ * 3, sy2 - ly_ / L_ * 3 + 1.2)), 0, .45)

# ---------------- Ancient Grove
gcx, gcy = PP("G0")
grove_giants = []
for k in range(6):
    a = k / 6 * 6.283 + .5 + rng.uniform(-.25, .25); rr = rng.uniform(13, 17)
    x, y = gcx + math.cos(a) * rr, gcy + math.sin(a) * rr
    if path_dist(x, y, 6) < 3.0:
        a += .5; x, y = gcx + math.cos(a) * rr, gcy + math.sin(a) * rr
    s = rng.uniform(.95, 1.1); me_ = GIANT_PINES[k % 3]
    if k == 0:
        s = 1.5                      # the "elder": rises well above the canopy, seen from the village
    place_tree_poi(me_, f"TREE_GroveGiant_{k}", C_POI_G, x, y, s, rng.uniform(0, 6.28))
    grove_giants.append((x, y, me_, s))
mb = MB()
mb.cone_dir((-7, 3, .55), (1, -.35, .02), 15, .9, .6, M["snag"], seg=10)
mb.cone_dir((-7.05, 3.02, .55), (1, -.35, .02), .05, .88, .88, M["log_end"], seg=10)
for k in range(5):
    mb.ico((-5 + k * 2.6, 2.2 - k * .9, 1.35), .6, M["moss_dark"], sub=1, scale=(1.3, .8, .2), jitter=.25, seed=k)
mb.obj("POI_Grove_FallenGiant", C_POI_G, (gcx, gcy, H(gcx, gcy) - .1), 0.0)
for k in range(8):
    q = Vector((gcx - 7 + k * 2.0, gcy + 3 - k * .7))
    GROUND.add(q.x, q.y, 1.1)
for k in range(5):
    a = k / 5 * 6.283 + 2.4
    x, y = gcx + math.cos(a) * 9.5, gcy + math.sin(a) * 9.5
    if not GROUND.free(x, y, .6) or path_dist(x, y, 3) < 1.0:
        continue
    st = MB(); st.ico((0, 0, .5), .5, M["rock_dark"], sub=1, scale=(.6, .45, 1.2), jitter=.15, seed=k + 20)
    st.obj(f"POI_Grove_StoneMarker_{k}", C_POI_G, (x, y, H(x, y) - .2), a, (rng.uniform(-.1, .1), rng.uniform(-.1, .1)))
    GROUND.add(x, y, .6)
x, y = PP("G2")
st = MB()
st.ico((0, 0, 1.0), 1.0, M["rock_dark"], sub=1, scale=(.5, .35, 1.3), jitter=.12, seed=77)
st.ico((0, 0, 1.75), .6, M["moss_dark"], sub=1, scale=(.75, .55, .3), jitter=.2, seed=78)
st.box((0, .34, 1.15), (.5, .04, .04), M["symbol"]); st.box((0, .34, 1.15), (.04, .04, .5), M["symbol"])
st.ico((0, .35, 1.15), .1, M["symbol"], sub=1, scale=(1, .2, 1))
st.obj("MYST_SymbolStone", C_POI_G, (x, y, H(x, y) - .25), face(x, y, gcx, gcy), (.05, -.04))
GROUND.add(x, y, 1.0)
for k, (x, y, me_, s) in enumerate(grove_giants[:3]):
    marks_on_trunk(f"MYST_MarkedTree_{k}", C_POI_G, x, y, me_, s, (gcx, gcy), 1.5, 1.9, symbol=True)
x, y = PP("G4"); mb = MB()
for k in range(5):
    a = k / 5 * 6.283
    mb.cone_dir((0, 0, 0), (math.cos(a) * .35, math.sin(a) * .35, 1), .45, .015, .006, M["fern2"], seg=4)
    mb.ico((math.cos(a) * .16, math.sin(a) * .16, .46), .05, M["glowplant"], sub=1, scale=(1, 1, 1.4))
mb.obj("MYST_GlowPlant", C_POI_G, (x, y, H(x, y) - .02), 0.0); GROUND.add(x, y, .5)
x, y = PP("G5")
for k in range(24):
    if GROUND.free(x, y, 1.0):
        break
    x, y = PP("G5")[0] + math.cos(k) * (1 + k * .3), PP("G5")[1] + math.sin(k) * (1 + k * .3)
mb = MB()
mb.box((0, 0, .25), (.45, .3, .5), M["cloth"], rot=(0, .25, 0)); mb.box((0, .0, .52), (.47, .32, .12), M["cloth"])
mb.box((.12, .16, .25), (.06, .02, .45), M["wood_dark"]); mb.box((-.12, .16, .25), (.06, .02, .45), M["wood_dark"])
mb.box((.9, .3, .2), (.6, .45, .4), M["wood_old"]); mb.box((.9, .3, .42), (.62, .47, .04), M["wood_dark"], rot=(0, .3, 0))
mb.obj("PROP_AbandonedBackpack", C_POI_G, (x, y, H(x, y)), rng.uniform(0, 6.28)); GROUND.add(x, y, 1.0)
for k in range(8):
    a = rng.uniform(0, 6.28); dd = rng.uniform(3, 12)
    x, y = gcx + math.cos(a) * dd, gcy + math.sin(a) * dd
    orb = MB(); orb.ico((0, 0, 0), .07, M["myst_soft"], sub=1)
    orb.obj(f"MAGIC_Wisp_Grove_{k}", C_POI_G, (x, y, H(x, y) + rng.uniform(.9, 2.8)))
for k in range(16):
    a = rng.uniform(0, 6.28); dd = rng.uniform(4, 14)
    x, y = gcx + math.cos(a) * dd, gcy + math.sin(a) * dd
    if not GROUND.free(x, y, .9) or path_dist(x, y, 3) < 1.0:
        continue
    me_ = FERNS[k % 4] if k % 3 else MOSS[k % 3]
    inst(me_, f"FERN_Grove_{k:02d}" if k % 3 else f"MOSS_Grove_{k:02d}", C_POI_G, (x, y, H(x, y) - .04),
         rng.uniform(0, 6.28), rng.uniform(.9, 1.4))
    GROUND.add(x, y, .9)
x, y, r_ = beside_path(*PP("G1"), 1.8)
sign_board("SIGN_DontFollowLights", C_POI_G, x, y, r_, ["DON'T FOLLOW", "THE LIGHTS"], tilt=(-.06, .08),
           size=.11, two_posts=False)
EXCL.append((gcx, gcy, 6.0))

# ---------------- Eastern Cliffs
px_, py_ = PP("E3"); pr = 5.8
pv = [(px_, py_, POND_Z)]; pf = []
for k in range(24):
    a = k / 24 * 6.283; rr = pr * (1 + .06 * math.sin(3 * a + 1))
    pv.append((px_ + math.cos(a) * rr, py_ + math.sin(a) * rr, POND_Z))
for k in range(24):
    pf.append((0, 1 + k, 1 + (k + 1) % 24))
pme = bpy.data.meshes.new("WATER_HiddenPond"); pme.from_pydata(pv, [], pf); pme.materials.append(M["pond"])
C_POI_E.objects.link(bpy.data.objects.new("WATER_HiddenPond", pme))
EXCL.append((px_, py_, pr + 1.5))
for k in range(5):
    a = rng.uniform(0, 6.28); q = (px_ + math.cos(a) * (pr + .3), py_ + math.sin(a) * (pr + .3))
    if GROUND.free(*q, .8):
        inst(REEDS, f"REEDS_Pond_{k}", C_POI_E, (q[0], q[1], POND_Z - .6), rng.uniform(0, 6.28), .6); GROUND.add(*q, .8)
wf_x, wf_y = PP("E2")
stream = catmull([(px_ - pr * .9, py_ - 2.5), (wf_x + 6, wf_y + 4), (wf_x + 2, wf_y + 1), (wf_x, wf_y)], 1.0)
ribbon("WATER_PondStream", stream, 1.1, M["falls"], C_POI_E, lift=.08)
top = stream[-1]; ztop = H(top.x, top.y) + .1
dirv = Vector((top.x - stream[-3].x, top.y - stream[-3].y)).normalized()
bot = top + dirv * 3.0; zbot = .15
nrm = Vector((-dirv.y, dirv.x)) * .7
fv = [(top.x - nrm.x, top.y - nrm.y, ztop), (top.x + nrm.x, top.y + nrm.y, ztop),
      (bot.x + nrm.x * 1.3, bot.y + nrm.y * 1.3, zbot), (bot.x - nrm.x * 1.3, bot.y - nrm.y * 1.3, zbot)]
fme = bpy.data.meshes.new("WATER_Waterfall"); fme.from_pydata(fv, [], [(0, 1, 2, 3)]); fme.materials.append(M["falls"])
C_POI_E.objects.link(bpy.data.objects.new("WATER_Waterfall", fme))
mb = MB()
for k in range(7):
    mb.ico((rng.uniform(-1.2, 1.2), rng.uniform(-1, 1), .1), rng.uniform(.25, .5), M["foam"], sub=1, scale=(1, 1, .35),
           jitter=.3, seed=k)
mb.obj("POI_Waterfall_Foam", C_POI_E, (bot.x + dirv.x * .4, bot.y + dirv.y * .4, 0), 0.0)
GROUND.add(bot.x, bot.y, 2.0); EXCL.append((bot.x, bot.y, 2.5))
for i, p in enumerate(stream[::4]):
    EXCL.append((p.x, p.y, 1.6))

cvx, cvy = PP("E4"); cr = face(cvx, cvy, cvx - 20, cvy); cz = H(cvx, cvy)
mb = MB()
mb.box((0, -1.4, 1.3), (2.2, 2.6, 2.6), M["cave"])
for k, (lx, lz, s) in enumerate(((-1.5, .8, 1.0), (1.5, .9, 1.1), (-1.2, 2.3, .9), (1.3, 2.4, .9), (0, 3.0, 1.2),
                                 (-1.7, 1.7, .8), (1.8, 1.8, .8))):
    mb.ico((lx, -.2, lz), s, M["rock_dark"], sub=1, scale=(1, .8, 1), jitter=.3, seed=k + 60)
for k, z_ in enumerate((.7, 1.4, 2.0)):
    mb.box((0, .05, z_), (2.6, .08, .25), M["wood_old"], rot=(0, .08 * (k - 1), 0))
for k in range(5):
    mb.ico((-1.0 + k * .5, .7, .15), rng.uniform(.25, .45), M["rock"], sub=1, jitter=.3, seed=k + 70)
cave = mb.obj("POI_CaveMouth", C_POI_E, (cvx, cvy, cz), cr)
mb = MB(); mb.box((0, 0, 0), (1.4, .04, .32), M["wood_old"], rot=(0, -.05, 0))
cs = mb.obj("SIGN_WhistlingCave", C_POI_E, (.2, .12, 1.75), 0.0); cs.parent = cave
text_mesh("SIGN_WhistlingCave_Text0", "DO NOT ANSWER", .075, cs, (0, .025, .06), M["sign_red"])
text_mesh("SIGN_WhistlingCave_Text1", "THE WHISTLING", .075, cs, (0, .025, -.07), M["sign_red"])
GROUND.add(cvx, cvy, 2.5); EXCL.append((cvx, cvy, 3.0))
rc = random.Random(321); kk = 0
for i in range(120):                              # rockier, barer ground around the cave
    if kk >= 16:
        break
    a = rc.uniform(0, 6.28); dd = rc.uniform(3.5, 9)
    x, y = cvx + math.cos(a) * dd, cvy + math.sin(a) * dd
    if path_dist(x, y, 4) < 1.2 or excluded(x, y) or H(x, y) < .2:
        continue
    if kk % 3 == 2:
        me_, sz, nm_ = HEATHER[kk % 2], .9, f"HEATHER_Cave_{kk:02d}"
    else:
        me_, sz, nm_ = ROCKS[1 + 2 * (kk % 2)], rc.uniform(.5, 1.6), f"ROCK_Cave_{kk:02d}"
    if not GROUND.free(x, y, sz):
        continue
    inst(me_, nm_, C_POI_E, (x, y, H(x, y) - (sz * .3 if nm_.startswith("ROCK") else .05)), rc.uniform(0, 6.28), sz)
    GROUND.add(x, y, sz); kk += 1
for k in range(2):
    a = rc.uniform(0, 6.28); x, y = cvx + math.cos(a) * 7, cvy + math.sin(a) * 7
    if GROUND.free(x, y, .8) and path_dist(x, y, 4) > 2:
        inst(DEADS[k], f"TREE_CaveSnag_{k}", C_POI_E, (x, y, H(x, y) - .2), rc.uniform(0, 6.28), .55)
        GROUND.add(x, y, .8)

lkx, lky = PP("E5"); lr = face(lkx, lky, lkx - 20, lky); lz = H(lkx, lky)
mb = MB()
mb.box((0, .8, .25), (3.6, 3.2, .16), M["wood"])
for sx_ in (-1.7, 1.7):
    for sy_ in (-.7, 2.3):
        mb.box((sx_, sy_, -1.3), (.18, .18, 3.2), M["wood_dark"])
for sx_ in (-1.75, 1.75):
    mb.box((sx_, .8, 1.05), (.08, 3.2, .08), M["wood_dark"])
mb.box((0, 2.35, 1.05), (3.6, .08, .08), M["wood_dark"])
for sx_ in (-1.75, 1.75):
    for sy_ in (-.7, 2.35):
        mb.box((sx_, sy_, .7), (.1, .1, .9), M["wood_dark"])
mb.box((0, 0, .7), (1.6, .4, .06), M["wood"])
mb.obj("STR_CliffLookout", C_POI_E, (lkx, lky, lz), lr)
GROUND.add(lkx, lky, 2.4); EXCL.append((lkx, lky, 3.0))
fx_, fy_ = PP("E6")
inst(ROCKS[2], "ROCK_FishingLedge", C_POI_E, (fx_, fy_, H(fx_, fy_) - .5), .4, (2.4, 1.8, .55))
GROUND.add(fx_, fy_, 2.4)

# ---------------- Lake
x, y = PP("L1"); z = H(x, y)
inst(BOATS[1], "BOAT_Wreck_Shallow", C_POI_L, (x, y, z + .22), .9, 1.0, (.28, -.38))
for k in range(3):
    inst(CRATE, f"PROP_Wreck_Debris_{k}", C_POI_L, (x + rng.uniform(-3, 3), y + rng.uniform(-3, 3), z + .05),
         rng.uniform(0, 6.28), (.25, 1.6, .12), (rng.uniform(-.3, .3), rng.uniform(-.3, .3)))
GROUND.add(x, y, 3.0); EXCL.append((x, y, 3.2))

mb = MB()
mb.cone((0, 0, .1), .42, .5, .5, M["rust"], seg=10)
mb.cone((0, 0, .45), .3, .3, .2, M["moss_dark"], seg=10)
for k in range(4):
    a = k / 4 * 6.283
    mb.cone_dir((math.cos(a) * .25, math.sin(a) * .25, .5), (-math.cos(a) * .25, -math.sin(a) * .25, 1), 1.3, .025, .02,
                M["metal"], seg=4)
mb.box((0, .44, .15), (.25, .02, .04), M["symbol"]); mb.box((0, .44, .15), (.04, .02, .25), M["symbol"])
STRANGE_BUOY = mb.mesh("Buoy_Strange")

x, y = PP("L3")
sign_board("SIGN_LakeNotEmpty", C_POI_L, x, y, face(x, y, x - 14, y + 12), ["THE LAKE", "IS NOT EMPTY"],
           tilt=(.1, -.06), size=.11, two_posts=False)

x, y = PP("L4"); r_ = face(x, y, *LAKE_C); z = H(x, y)
mb = MB()
for sx_ in (-1.4, 1.4):
    mb.box((sx_, .9, 1.2), (.14, .14, 2.4), M["wood_dark"]); mb.box((sx_, -.9, .9), (.14, .14, 1.8), M["wood_dark"])
mb.box((0, 0, 2.15), (3.2, 2.4, .1), M["wood_old"], rot=(-.3, 0, 0))
mb.box((0, -.95, .9), (2.9, .08, 1.7), M["wood_old"])
mb.box((0, -.4, .45), (2.2, .4, .06), M["wood"])
for lx in (-.8, .8):
    mb.box((lx, -.4, .22), (.08, .35, .44), M["wood_dark"])
for k in range(3):
    mb.cone_dir((-1.2 + k * .2, -.85, .1), (0, .25, 1), 2.0, .02, .008, M["wood_dark"], seg=4)
mb.box((0, .92, 1.7), (1.8, .05, .45), M["wood_old"])
shel = mb.obj("STR_FisherShelter", C_POI_L, (x, y, z), r_)
text_mesh("STR_FisherShelter_Text0", "IF THE FISH STOP BITING,", .075, shel, (0, .95, 1.78), M["sign_paint"])
text_mesh("STR_FisherShelter_Text1", "LEAVE", .09, shel, (0, .95, 1.6), M["sign_red"])
GROUND.add(x, y, 2.2); EXCL.append((x, y, 2.6))

# ---------------- Forgotten Isle
x, y = PP("I1")
for k in range(30):
    if GROUND.free(x, y, 1.8) and path_dist(x, y, 5) > 2.6 and H(x, y) > .6 and not excluded(x, y):
        break
    x, y = PP("I1")[0] + math.cos(k * 1.3) * (1.5 + k * .3), PP("I1")[1] + math.sin(k * 1.3) * (1.5 + k * .3)
z = H(x, y); mb = MB()
for k in range(2):
    mb.cone_dir((.6 + k * .25, .2, 0), (-.25, .1, 1), 2.4, .02, .006, M["wood_dark"], seg=4)
for k in range(5):
    mb.ico((-.6 + k * .22, -.4 + (k % 2) * .25, .08), .3, M["net"], sub=1, scale=(1, 1, .3), jitter=.3, seed=k + 30)
mb.box((-1.3, .5, .18), (.6, .4, .35), M["wood_old"]); mb.box((-1.2, 1.1, .1), (.6, .4, .2), M["wood_old"], rot=(.4, .2, .3))
mb.cone_dir((.2, -1.1, .12), (1, .4, .1), .3, .15, .18, M["rust"], seg=10)
mb.obj("PROP_IsleFishingGear", C_POI_I, (x, y, z), 1.0)
GROUND.add(x, y, 1.8)
mb = MB()
for i in range(7):
    a = i / 7 * 6.283
    px2, py2 = scx + math.cos(a) * 4.5, scy + math.sin(a) * 4.5
    d2 = Vector((scx - px2, scy - py2)).normalized()
    q = Vector((px2, py2)) + d2 * .42; zq = H(px2, py2) + .9
    fa = math.atan2(d2.y, d2.x)
    mb.box((q.x - scx, q.y - scy, zq - scz), (.03, .26, .03), M["symbol"], rot=(0, 0, fa))
    mb.box((q.x - scx, q.y - scy, zq - scz), (.03, .03, .26), M["symbol"], rot=(0, 0, fa))
mb.obj("MYST_CircleSymbols", C_POI_I, (scx, scy, scz), 0.0)

# ---------------- night hooks and extra markers
for i_, nm_ in (("V7", "MK_Night_WindowLight"), ("N1", "MK_Night_LakeLights"), ("N2", "MK_Night_Bells"),
                ("N3", "MK_Night_Whistling"), ("N4", "MK_Night_ForestListener"), ("N5", "MK_Night_IsleCircle")):
    x, y = PP(i_)
    marker(nm_, C_NIGHT, (x, y, max(H(x, y), 0) + 2.5), 'SPHERE', 1.5)
for k, (x, y) in enumerate((PP("F9"), PP("G0"))):
    marker(f"MK_SunShafts_{k + 1}", C_MARK, (x, y, H(x, y) + 8), 'SINGLE_ARROW', 3)
progress("points of interest done")

progress("forest: trees")
# hand-placed feature trees in the village first (they get their spot before the scatter)
for i, (x, y) in enumerate([(-14, SY - 34), (16, SY - 36), (-52, SY - 30), (36, SY - 40), (-6, SY - 46)]):
    kind = "B" if i % 2 == 0 else "P"
    s = rng.uniform(.85, 1.05); rad = R_KIND[kind] * s
    if excluded(x, y) or not CANOPY.free(x, y, rad) or not GROUND.free(x, y, .6):
        continue
    me_ = KIND_LIST[kind][i % 5]; rz = rng.uniform(0, 6.28)
    inst(me_, f"TREE_Village_{i}", C_TREES, (x, y, H(x, y) - .25), rz, s, lean_tilt(x, y, rz, lake_d(x, y), kind))
    CANOPY.add(x, y, rad); GROUND.add(x, y, .6)
r_e = random.Random(301); ne = 0
for _ in range(4000):                 # glacial erratics: 1 big + 2-3 medium + small ones, on till slopes in the forest
    if ne >= 14:
        break
    x, y = r_e.uniform(-190, 190), r_e.uniform(-190, 190)
    h = H(x, y)
    if h < 2 or forest_cover(x, y) < .3 or slope(x, y) > .45 or village_core(x, y) > .2:
        continue
    d_, sl_, moist_, dry_ = site(x, y, h)
    if dry_ > .9 or not ground_ok(x, y, 4.5, 2.5, 3.0):
        continue
    sb = r_e.uniform(2.8, 4.0); parts = [(0.0, 0.0, sb)]
    for i in range(r_e.randint(2, 3)):
        a = r_e.uniform(0, 6.28); dd = sb + r_e.uniform(.6, 2.5)
        parts.append((math.cos(a) * dd, math.sin(a) * dd, r_e.uniform(1.1, 1.8)))
    for i in range(r_e.randint(4, 6)):
        a = r_e.uniform(0, 6.28); dd = r_e.uniform(1.5, sb + 4)
        parts.append((math.cos(a) * dd, math.sin(a) * dd, r_e.uniform(.35, .7)))
    k = 0
    for ox, oy, sz in parts:
        px, py = x + ox, y + oy
        if k and (not ground_ok(px, py, sz, 1.2, 1.5) or slope(px, py) > .6):
            continue
        me_ = ROCKS[(k + ne) % 5]
        inst(me_, f"ROCK_Erratic_{ne:02d}_{k}", C_ROCKS, (px, py, H(px, py) - sz * .35), r_e.uniform(0, 6.28), sz,
             (r_e.uniform(-.15, .15), r_e.uniform(-.15, .15)))
        GROUND.add(px, py, sz); k += 1
    ne += 1
progress(f"erratic boulder groups: {ne}")
sprinkle(90000, tree_fn, 101)
progress(f"trees: {CNT['tree']}")


def alder_fn(x, y, r):
    h = H(x, y)
    if not (.35 < h < 1.9) or village_core(x, y) > .25 or excluded(x, y, 1.0):
        return
    near_lake = lake_d(x, y) < 1.12 and fetch(x, y) < 80
    near_creek = 2.2 < CGRID.dist(x, y, 8) < 7
    if not (near_lake or near_creek) or r.random() > .5:
        return
    if not CANOPY.free(x, y, 2.0) or not ground_ok(x, y, .9, 1.8, 1.8):
        return
    CNT["alder"] = CNT.get("alder", 0) + 1
    inst(r.choice(ALDERS), f"TREE_Alder_{CNT['alder']:03d}", C_TREES, (x, y, h - .1), r.uniform(0, 6.28),
         r.uniform(.8, 1.15))
    CANOPY.add(x, y, 2.0); GROUND.add(x, y, .9)


sprinkle(30000, alder_fn, 121)
progress(f"alders: {CNT.get('alder', 0)}")
sprinkle(10000, rock_fn, 105)
for gi, (gx, gy, gr) in enumerate(GLADES[:5]):   # each natural glade gets a mossy boulder as a focal point
    x, y = gx + 2, gy - 1; s = rng.uniform(1.8, 2.6)
    if GROUND.free(x, y, s) and path_dist(x, y, 8) > s + 1.2:
        inst(MOSSROCKS[gi % 3], f"ROCK_Glade_{gi}", C_ROCKS, (x, y, H(x, y) - .6), rng.uniform(0, 6.28), s)
        GROUND.add(x, y, s)
sprinkle(6000, log_fn, 103)
sprinkle(5000, stump_fn, 104)
sprinkle(9000, sapling_fn, 102)
sprinkle(25000, fern_fn, 106)
sprinkle(6000, bush_fn, 107)


def juniper_fn(x, y, r):
    if CNT.get("juniper", 0) >= 140:
        return
    cov = forest_cover(x, y)
    if not (.1 < cov < .6) or r.random() > .5:
        return
    h = H(x, y)
    if h < 1.6:
        return
    d_, sl_, moist_, dry_ = site(x, y, h)
    if dry_ < .15 or not ground_ok(x, y, .9, 1.5) or not CANOPY.free(x, y, .4):
        return
    CNT["juniper"] = CNT.get("juniper", 0) + 1
    inst(r.choice(JUNIPERS), f"BUSH_Juniper_{CNT['juniper']:03d}", C_BUSH, (x, y, h - .1), r.uniform(0, 6.28),
         r.uniform(.8, 1.25))
    GROUND.add(x, y, .9)


sprinkle(20000, juniper_fn, 122)
sprinkle(5000, heather_fn, 108)
sprinkle(8000, shroom_fn, 109)
sprinkle(20000, grass_fn, 110)
sprinkle(7500, flower_fn, 111)
sprinkle(12000, reed_fn, 112, area=(-170.0, 170.0, -105.0, 135.0))
for i, p in enumerate(CREEK_D[8:-4:5]):         # reeds along the creek banks
    t = (CREEK_D[min(len(CREEK_D) - 1, 8 + i * 5 + 1)] - p)
    nrm = Vector((-t.y, t.x)).normalized() * (1.9 if i % 2 else -1.9)
    q = p + nrm
    if excluded(q.x, q.y) or path_dist(q.x, q.y, 3) < 1 or not GROUND.free(q.x, q.y, .6):
        continue
    inst(REEDS, f"REEDS_Creek_{i:02d}", C_REEDS, (q.x, q.y, H(q.x, q.y) - .2), rng.uniform(0, 6.28), .55)
    GROUND.add(q.x, q.y, .6)
progress("forest floor details")
DC = {k: 0 for k in ("MOSS", "BRANCH", "PEBBLES", "LEAVES", "FERN", "LOGROCK", "SHORE")}


def flat_z(x, y, r, tol=.12):
    """Height for a flat ground patch, or None if the ground under it is too uneven for a flat patch."""
    hs_ = [H(x + dx_ * r, y + dy_ * r) for dx_, dy_ in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1),
                                                       (.7, .7), (-.7, .7), (.7, -.7), (-.7, -.7))]
    if max(hs_) - min(hs_) > tol:
        return None
    return (max(hs_) + min(hs_)) / 2


def try_place(me, name, coll_, x, y, rad, zoff=-.05, scale=1.0, tilt=(0, 0), rz=None, path_pad=.8):
    if name.startswith(("MOSS", "LEAVES")) and slope(x, y) > .55:
        return False
    if not ground_ok(x, y, rad, path_pad, 1.2):
        return False
    zb = flat_z(x, y, rad * scale) if name.startswith(("MOSS", "LEAVES", "PEBBLES")) else H(x, y)
    if zb is None:
        return False
    inst(me, name, coll_, (x, y, zb + zoff), rng.uniform(0, 6.28) if rz is None else rz, scale, tilt)
    GROUND.add(x, y, rad)
    return True


# 1) small vignettes at tree bases: soften the trunk-to-ground transition
rv = random.Random(201)
for tx, ty, kind, s in TREE_PTS:
    if rv.random() > .45:
        continue
    for k in range(rv.randint(1, 3)):
        a = rv.uniform(0, 6.28); dd = rv.uniform(1.2, 2.4) * max(.8, s)
        x, y = tx + math.cos(a) * dd, ty + math.sin(a) * dd
        q = rv.random()
        if kind == "B" and q < .45:
            me_, pre, rad = rv.choice(LEAVES), "LEAVES", 1.0
        elif q < .35:
            me_, pre, rad = rv.choice(FERNS), "FERN", .9
        elif q < .6:
            me_, pre, rad = rv.choice(MOSS), "MOSS", .8
        elif q < .8:
            me_, pre, rad = rv.choice(BRANCHES), "BRANCH", 1.3
        else:
            me_, pre, rad = rv.choice(PEBBLES), "PEBBLES", .6
        DC[pre] += 1
        try_place(me_, f"{pre}_Base_{DC[pre]:04d}", C_BUSH, x, y, rad, zoff=(.02 if pre in ("LEAVES", "MOSS") else -.04),
                  scale=rv.uniform(.8, 1.2))
# birch litter spreads further from the trunk
for tx, ty, kind, s in TREE_PTS:
    if kind != "B" or rv.random() > .6:
        continue
    a = rv.uniform(0, 6.28); dd = rv.uniform(2.0, 3.5)
    DC["LEAVES"] += 1
    try_place(rv.choice(LEAVES), f"LEAVES_{DC['LEAVES']:04d}", C_BUSH, tx + math.cos(a) * dd, ty + math.sin(a) * dd,
              1.1, zoff=.02, scale=rv.uniform(.9, 1.4))


# 2) moss follows moisture; branches under the canopy; pebbles on bare, sloping ground
def moss_fn(x, y, r):
    if DC["MOSS"] >= 900:
        return
    cov = forest_cover(x, y)
    if cov < .4:
        return
    h = H(x, y)
    if h < 1.1:
        return
    d, sl, moist, dry = site(x, y, h)
    if r.random() > .5 * moist * cov * (1 - .5 * min(1.0, dry)):
        return
    glow = moist > .75 and cov > .8 and r.random() < .06
    DC["MOSS"] += 1
    try_place(MOSS_GLOW if glow else r.choice(MOSS), f"MOSS_{'Glow_' if glow else ''}{DC['MOSS']:04d}", C_BUSH,
              x, y, .8, .0, r.uniform(.8, 1.5), rz=r.uniform(0, 6.28))


def branch_fn(x, y, r):
    if DC["BRANCH"] >= 500 or forest_cover(x, y) < .3 or r.random() > .3:
        return
    DC["BRANCH"] += 1
    try_place(r.choice(BRANCHES), f"BRANCH_{DC['BRANCH']:04d}", C_BUSH, x, y, 1.3, -.03, r.uniform(.8, 1.2),
              rz=r.uniform(0, 6.28))


def pebble_fn(x, y, r):
    if DC["PEBBLES"] >= 300:
        return
    h = H(x, y)
    if h < .3:
        return
    pd = path_dist(x, y, 4)
    if not ((forest_cover(x, y) < .45 and slope(x, y) > .25) or 1.0 < pd < 2.5) or r.random() > .25:
        return
    DC["PEBBLES"] += 1
    try_place(r.choice(PEBBLES), f"PEBBLES_{DC['PEBBLES']:04d}", C_ROCKS, x, y, .6, -.02, r.uniform(.8, 1.3),
              rz=r.uniform(0, 6.28), path_pad=.9)


def logrock_fn(x, y, r):
    if DC["LOGROCK"] >= 14 or forest_cover(x, y) < .5 or r.random() > .15:
        return
    h = H(x, y)
    if h < 1.5 or slope(x, y) > .45:
        return
    DC["LOGROCK"] += 1
    try_place(r.choice(LOGBOULDER), f"ROCK_LogVignette_{DC['LOGROCK']:02d}", C_ROCKS, x, y, 3.2, -.35, 1.0,
              rz=r.uniform(0, 6.28), path_pad=2.0)


def blueberry_fn(x, y, r):
    if DC.setdefault("BLUEBERRY", 0) >= 1500:
        return
    cov = forest_cover(x, y)
    if cov < .35:
        return
    h = H(x, y)
    if h < 1.2:
        return
    d, sl, moist, dry = site(x, y, h)
    if r.random() > .55 * ss(.35, .75, cov) * (1 - .5 * min(1.0, dry)) * ss(-.2, .3, fbm(x / 14, y / 14, 2, 87)):
        return
    DC["BLUEBERRY"] += 1
    try_place(r.choice(BLUEBERRY), f"BLUEBERRY_{DC['BLUEBERRY']:04d}", C_BUSH, x, y, .8, .0, r.uniform(.8, 1.4),
              rz=r.uniform(0, 6.28))


def shore_fn(x, y, r):
    """Lake edge: lily pads and stones in shallow water, driftwood and pebble strips on the beach."""
    h = H(x, y)
    if in_island(x, y, 3) or excluded(x, y, 1.5):
        return
    if -1.2 < h < -.3 and DC.setdefault("LILY", 0) < 90 and fbm(x / 22, y / 22, 2, 88) > .22 and r.random() < .35 and fetch(x, y) < 60:
        if GROUND.free(x, y, 1.2):
            DC["LILY"] += 1
            inst(r.choice(LILIES), f"LILY_{DC['LILY']:03d}", C_REEDS, (x, y, .012), r.uniform(0, 6.28), r.uniform(.8, 1.3))
            GROUND.add(x, y, 1.2)
    elif -1.6 < h < -.3 and DC.setdefault("SUBROCK", 0) < 120 and r.random() < .08:
        sz = r.uniform(.5, 1.3)
        if GROUND.free(x, y, sz):
            DC["SUBROCK"] += 1
            inst(r.choice(ROCKS), f"ROCK_Shallow_{DC['SUBROCK']:03d}", C_ROCKS, (x, y, h - sz * .2), r.uniform(0, 6.28), sz,
                 (r.uniform(-.2, .2), r.uniform(-.2, .2)))
            GROUND.add(x, y, sz)
    elif 0.0 < h < .5 and DC.setdefault("DRIFT", 0) < 50 and r.random() < .05:
        if ground_ok(x, y, 1.4, 1.0, 1.0):
            DC["DRIFT"] += 1
            inst(r.choice(BRANCHES), f"BRANCH_Driftwood_{DC['DRIFT']:03d}", C_ROCKS, (x, y, h - .02), r.uniform(0, 6.28),
                 r.uniform(1.0, 1.5))
            GROUND.add(x, y, 1.4)
    elif -.2 < h < .4 and DC.setdefault("BEACHPEB", 0) < 120 and r.random() < .07:
        zb = flat_z(x, y, .8)
        if zb is not None and GROUND.free(x, y, .6) and path_dist(x, y, 3) > .9:
            DC["BEACHPEB"] += 1
            inst(r.choice(PEBBLES), f"PEBBLES_Beach_{DC['BEACHPEB']:03d}", C_ROCKS, (x, y, zb), r.uniform(0, 6.28),
                 r.uniform(.9, 1.4))
            GROUND.add(x, y, .6)


sprinkle(3000, logrock_fn, 205)
sprinkle(20000, moss_fn, 206)
sprinkle(12000, branch_fn, 207)
sprinkle(9000, pebble_fn, 208)
sprinkle(30000, blueberry_fn, 211)
sprinkle(26000, shore_fn, 212, area=(-170.0, 170.0, -105.0, 135.0))

# 3) the shoreline is dressed with rock clusters (one bigger rock, smaller ones and pebbles around it)
rs = random.Random(209)
for _ in range(9000):
    if DC["SHORE"] >= 160:
        break
    x, y = rs.uniform(-170, 170), rs.uniform(-105, 135)
    h = H(x, y)
    if not (-0.5 < h < 0.7) or rs.random() > .25:
        continue
    big = rs.uniform(1.0, 2.0)
    if not ground_ok(x, y, big * 1.05, 1.0, 1.0):
        continue
    DC["SHORE"] += 1; n = DC["SHORE"]
    inst(ROCKS[n % 5], f"ROCK_Shore_{n:03d}", C_ROCKS, (x, y, h - big * .35), rs.uniform(0, 6.28), big,
         (rs.uniform(-.2, .2), rs.uniform(-.2, .2)))
    GROUND.add(x, y, big * 1.05)
    for k in range(rs.randint(1, 3)):
        a = rs.uniform(0, 6.28); dd = big + rs.uniform(.6, 1.6); sm = rs.uniform(.35, .7)
        px, py = x + math.cos(a) * dd, y + math.sin(a) * dd
        if GROUND.free(px, py, sm) and not excluded(px, py):
            inst(ROCKS[(n + k + 2) % 5], f"ROCK_Shore_{n:03d}_{k}", C_ROCKS, (px, py, H(px, py) - sm * .3),
                 rs.uniform(0, 6.28), sm)
            GROUND.add(px, py, sm)
    a = rs.uniform(0, 6.28); px, py = x + math.cos(a) * (big + .8), y + math.sin(a) * (big + .8)
    if GROUND.free(px, py, .6) and not excluded(px, py):
        inst(PEBBLES[n % 3], f"PEBBLES_Shore_{n:03d}", C_ROCKS, (px, py, H(px, py) - .02), rs.uniform(0, 6.28), 1.0)
        GROUND.add(px, py, .6)

# 4) subtle magic outside the grove: one fairy ring (wisps and the rune stone live in the Ancient Grove)
gx, gy, gr = GLADES[0]
fcx, fcy = gx - 4, gy + 3
for k in range(9):
    a = k / 9 * 2 * math.pi
    x, y = fcx + math.cos(a) * 2.6, fcy + math.sin(a) * 2.6
    if GROUND.free(x, y, .35) and not excluded(x, y):
        inst(SHROOMS[k % 2], f"SHROOM_FairyRing_{k}", C_BUSH, (x, y, H(x, y) - .02), rng.uniform(0, 6.28), .9)
        GROUND.add(x, y, .35)

# 5) the lake: drowned dead trees in the west cove, a faint light far below, a sunken boat
progress("lake horror details")
rd = random.Random(210); nd = 0; nl = 0
for _ in range(4000):
    if nd >= 9 and nl >= 3:
        break
    x, y = rd.uniform(-165, -88), rd.uniform(-45, 65)
    h = H(x, y)
    rad_ = 1.4 if nd < 9 else 3.2
    if not (-2.6 < h < -.5) or in_island(x, y, 4) or excluded(x, y, 2) or not GROUND.free(x, y, rad_):
        continue
    if nd < 9:
        s = rd.uniform(1.0, 1.4)
        inst(DEADS[nd % 3], f"TREE_Drowned_{nd}", C_WATER, (x, y, h - .4), rd.uniform(0, 6.28), s,
             (rd.uniform(-.15, .15), rd.uniform(-.15, .15)))
        nd += 1
    else:
        inst(LOGS[nl % 3], f"LOG_Drowned_{nl}", C_WATER, (x, y, -.28), rd.uniform(0, 6.28), 1.0,
             (rd.uniform(-.08, .08), rd.uniform(-.08, .08)))
        nl += 1
    GROUND.add(x, y, rad_)
mz = H(*MYST_POS)
dl = MB()
dl.ico((0, 0, 0), 1.0, M["deep_glow"], sub=2, scale=(1.0, 1.0, .6))
dl.obj("MYST_DeepLight_Source", C_WATER, (MYST_POS[0], MYST_POS[1], mz + 1.2))
ld = bpy.data.lights.new("MYST_DeepLight", 'POINT'); ld.energy = 350; ld.color = (.35, .95, .82)
ld.shadow_soft_size = 2.0
lo = bpy.data.objects.new("MYST_DeepLight", ld); lo.location = (MYST_POS[0], MYST_POS[1], mz + 2.5)
C_WATER.objects.link(lo)
inst(BOATS[1], "BOAT_Sunken", C_WATER, (MYST_POS[0] + 7, MYST_POS[1] - 4, H(MYST_POS[0] + 7, MYST_POS[1] - 4) + .25),
     2.2, 1.0, (.45, .2))
marker("MK_Mystery_DeepLight", C_MARK, (MYST_POS[0], MYST_POS[1], 0), 'SPHERE', 5)
progress("details: " + ", ".join(f"{k}={v}" for k, v in DC.items()) + f", drowned={nd}+{nl}")
progress("forest done: " + ", ".join(f"{k}={v}" for k, v in CNT.items()))

# ---------------------------------------------------------------- markers
def to_water(x, y, depth=-1.5):
    if H(x, y) < depth and not in_island(x, y, 4):
        return x, y
    for rad in range(3, 45, 3):
        for kk in range(16):
            a = kk / 16 * 2 * math.pi
            xx, yy = x + math.cos(a) * rad, y + math.sin(a) * rad
            if H(xx, yy) < depth and not in_island(xx, yy, 4):
                return xx, yy
    return x, y

marker("MK_PlayerSpawn", C_MARK, (SQ[0] + 2, SQ[1] + 5, H(SQ[0] + 2, SQ[1] + 5) + .1), 'ARROWS', 2)
for nm, (x, y) in {"MK_Zone_SunshoreVillage": SQ, "MK_Zone_PinewoodForest": (-150, 20),
                   "MK_Zone_EastCliffs": (150, 0), "MK_Zone_ForgottenIsle": FI,
                   "MK_Zone_Viewpoint": VIEWPOINT, "MK_Zone_Meadow": MEADOW, "MK_Zone_AncientGrove": PP("G0"),
                   "MK_Zone_Falls": PP("E2"), "MK_Zone_OldCamp": PP("F2"), "MK_Zone_HiddenPond": POND}.items():
    marker(nm, C_MARK, (x, y, H(x, y) + 3), 'SPHERE', 6)
spots = [(0, main_end[1] + 14), (-108, 18), (96, 8), (32, 32), (-62, 62), (-22, -22), (110, 55)]
for k, (x, y) in enumerate(spots):
    x, y = to_water(x, y)
    marker(f"MK_FishingSpot_{k:02d}", C_MARK, (x, y, 0), 'CIRCLE', 4)
    if k == 4:      # the old buoy with a strange symbol replaces the normal one here
        inst(STRANGE_BUOY, "PROP_Buoy_Strange", C_POI_L, (x + 3, y, .0), .7, 1.0, (.12, -.08))
    else:
        inst(BUOY, f"PROP_Buoy_{k:02d}", C_VPROP, (x + 3, y, .05), 0, 1.0)
for k, (x, y) in ((7, hidden_end), (8, PP("E6")), (9, PP("L7"))):
    x, y = to_water(x, y, -1.2)
    marker(f"MK_FishingSpot_{k:02d}", C_MARK, (x, y, 0), 'CIRCLE', 4)
x, y = to_water(0.0, 20.0, -6.0)
marker("MK_FishingSpot_10", C_MARK, (x, y, 0), 'CIRCLE', 4)                    # open deep water (boat)
marker("MK_FishingSpot_11", C_MARK, (POND[0], POND[1], POND_Z), 'CIRCLE', 3)    # hidden pond on the cliffs
# habitat tag per spot -> Unity picks the fish table from it (plan/LAYOUT_RULES.md)
HABITAT = ["dock", "reeds", "rocky_shore", "isle_dropoff", "deep_strange", "shallows", "cove", "hidden_cove",
           "waterfall", "creek_mouth", "deep_open", "pond"]
for k, hab in enumerate(HABITAT):
    ob_ = bpy.data.objects.get(f"MK_FishingSpot_{k:02d}")
    if ob_:
        ob_["habitat"] = hab

def mannequin(name, x, y, z=None, rot=0.0):
    mb = MB()
    mb.cone((0, 0, .45), .11, .1, .9, M["mannequin"], seg=8)
    mb.cone((0, 0, 1.18), .2, .17, .62, M["mannequin"], seg=10)
    mb.ico((0, 0, 1.64), .13, M["mannequin"], sub=2, scale=(1, 1, 1.15))
    for s in (-1, 1):
        mb.cone((s * .26, 0, 1.12), .05, .04, .62, M["mannequin"], seg=6, rot=(0, s * .12, 0))
    return mb.obj(name, C_MARK, (x, y, H(x, y) if z is None else z), rot)

mannequin("REF_Human180_Street", -20, SY - 21.5, rot=.4)
mannequin("REF_Human180_Square", SQ[0] + 1.5, SQ[1] + 1, rot=2.5)
mannequin("REF_Human180_Shop", *l2w(sx_, sy_, sr_, -2.0, 5.4), z=H(sx_, sy_) + .4)
mannequin("REF_Human180_Dock", -.4, main_end[1] - 7, z=1.05, rot=2.8)
mannequin("REF_Human180_Isle", *isle_world(6, -6.5), rot=2.0)
mannequin("REF_Human180_Forest", -146, -10, rot=-.3)

# ---------------------------------------------------------------- light, sky, cameras
w = bpy.data.worlds.new("SkyDay"); scene.world = w
try:
    w.use_nodes = True
except Exception:
    pass
if w.node_tree is not None:
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs[0].default_value = (*C(.64, .78, .93), 1); bg.inputs[1].default_value = 1.0
w.color = C(.62, .80, .98)

def aim(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

sun_d = bpy.data.lights.new("SUN_Day", 'SUN'); sun_d.energy = 3.8; sun_d.color = (1.0, .9, .77)
sun_d.angle = math.radians(7.0)
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

EYE = 1.7
cam("CAM_Overview", (-70, -330, 175), (0, 5, 0), 30)
cam("CAM_Top", (0, 0, 400), None, ortho=405)
cam("CAM_Village", (-36, SY + 44, 14), (2, SY - 22, 3), 26)
fcx, fcy = isle_world(14, -46)
cam("CAM_ForgottenIsle", (fcx, fcy, 7), (*isle_world(-4, 3), 6), 32)
_sp = min(sd, key=lambda p: (p - Vector((-44.0, SY - 22))).length)
cam("CAM_Eye_VillageStreet", (_sp.x, _sp.y, H(_sp.x, _sp.y) + EYE), (SQ[0] + 4, SQ[1] + 2, SQ_H + 2.2), 22)
cam("CAM_Eye_VillageSquare", (SQ[0] - 5, SQ[1] - 7, SQ_H + EYE), (-2, SY + 32, 1.2), 22)
cam("CAM_Eye_MainDock", (1.0, main_end[1] + 3.0, 1.05 + EYE), (-4, SY - 22, 4.0), 22)
cam("CAM_Eye_DockToLake", (0.0, main_end[1] + 3.5, 1.05 + EYE), (*isle_world(-4, 3), 5), 22)
_wp = catmull(PATHS[4][1], 1.5)
_i = min(range(len(_wp)), key=lambda kk: (_wp[kk] - Vector((-146.0, -28.0))).length)
fp = _wp[_i]; fa = _wp[min(len(_wp) - 1, _i + 16)]
cam("CAM_Eye_ForestPath", (fp.x, fp.y, H(fp.x, fp.y) + EYE), (fa.x + 6, fa.y, H(fa.x, fa.y) + 1.2), 22)
cam("CAM_Eye_ForgottenIsle", (isle_dock_end[0] + ISLE_SOUTH[0] * -1.5, isle_dock_end[1] + ISLE_SOUTH[1] * -1.5, .85 + EYE),
    (*isle_world(-1, 2), H(*isle_world(-1, 2)) + 4.5), 24)


def cam_front(name, objname, dist, height=EYE, look_up=1.3, side=0.0, lens=24):
    """Player-eye camera standing in front of an object (its local +Y side), looking at it."""
    o = bpy.data.objects[objname]; rz = o.rotation_euler.z
    fx, fy = -math.sin(rz), math.cos(rz); sxv, syv = math.cos(rz), math.sin(rz)
    px, py = o.location.x + fx * dist + sxv * side, o.location.y + fy * dist + syv * side
    return cam(name, (px, py, max(H(px, py), .3) + height), (o.location.x, o.location.y, o.location.z + look_up), lens)

def cam_from(name, frm, target_xy, tz=1.2, lens=24):
    return cam(name, (frm[0], frm[1], max(H(*frm), .3) + EYE), (target_xy[0], target_xy[1], H(*target_xy) + tz), lens)

cam_from("CAM_POI_Village", (-6, -79), PP("V1"), 1.6)
cam_front("CAM_POI_ForestSign", "SIGN_WoodsAfterDark", 5.0, side=-1.5)
cam_from("CAM_POI_Camp", (PP("F2")[0] + 6, PP("F2")[1] + 4), PP("F2"), .5)
cam_from("CAM_POI_Grove", (-145, -99), (PP("G0")[0] - 2, PP("G0")[1] - 4), 3.0, 22)
cam_from("CAM_POI_ForestBoat", (PP("F6")[0] + 5, PP("F6")[1] - 4), PP("F6"), .5)
cam_front("CAM_POI_Bell", "POI_WarningBell", 4.5, side=1.0)
cam_from("CAM_POI_Cave", (101, -27), PP("E4"), 1.6)
cam_from("CAM_POI_Waterfall", (133, 4), (PP("E2")[0] - 2, PP("E2")[1]), 3.0, 22)
cam_from("CAM_POI_Shelter", (89, -56), PP("L4"), 1.5)
cam_front("CAM_Eye_Shop", "BLD_TackleShop", 13.0, look_up=2.6, side=2.0, lens=22)
scene.camera = CAMS["CAM_Overview"]

try:
    bpy.context.view_layer.layer_collection.children["_Prototypes"].exclude = True
except Exception:
    pass
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

for eng in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try:
        scene.render.engine = eng; break
    except Exception:
        pass
try:
    scene.eevee.taa_render_samples = 32
except Exception:
    pass
for attr, val in (("use_gtao", True), ("use_fast_gi", True), ("fast_gi_method", 'GLOBAL_ILLUMINATION'),
                  ("shadow_ray_count", 2), ("shadow_step_count", 8)):
    try:
        setattr(scene.eevee, attr, val)
    except Exception:
        pass
for look in ('AgX - Medium Contrast', 'Medium Contrast'):
    try:
        scene.view_settings.look = look; break
    except Exception:
        pass
scene.render.resolution_x = 1600; scene.render.resolution_y = 900
scene.render.image_settings.file_format = 'PNG'

progress(f"objects={len(bpy.data.objects)} trees={CNT['tree']} bushes={CNT['bush']} grass={CNT['grass']} "
         f"flowers={CNT['flower']} rocks={CNT['rock']} reeds={CNT['reed']} shoreY={SY:.1f}")
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH, compress=True)
progress(f"saved {BLEND_PATH}")

if DO_RENDER:
    for name in ("CAM_Overview", "CAM_Village", "CAM_ForgottenIsle", "CAM_Eye_VillageStreet",
                 "CAM_Eye_VillageSquare", "CAM_Eye_MainDock", "CAM_Eye_DockToLake",
                 "CAM_Eye_ForestPath", "CAM_Eye_ForgottenIsle", "CAM_POI_Village", "CAM_POI_ForestSign",
                 "CAM_POI_Camp", "CAM_POI_Grove", "CAM_POI_ForestBoat", "CAM_POI_Bell", "CAM_POI_Cave",
                 "CAM_POI_Waterfall", "CAM_POI_Shelter", "CAM_Eye_Shop", "CAM_Top"):
        scene.camera = CAMS[name]
        if name == "CAM_Top":
            scene.render.resolution_x = 1400; scene.render.resolution_y = 1400
        scene.render.filepath = os.path.join(RENDER_DIR, name.replace("CAM_", "SunshoreBay_") + ".png")
        bpy.ops.render.render(write_still=True)
        progress(f"rendered {name}")
    scene.camera = CAMS["CAM_Overview"]
    scene.render.resolution_x = 1600; scene.render.resolution_y = 900
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH, compress=True)
progress("done")
