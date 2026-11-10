"""
Stillwater - lake map generator (Blender 4.x / 5.x).

Builds a low-poly lake map: terrain with a lake basin, a separate flat water
plane, a wooden dock, trees and rocks. Then exports it as FBX for Unity.

Run headless:
    blender -b -P Tools/Blender/generate_map.py
    blender -b -P Tools/Blender/generate_map.py -- --seed 7 --out /some/dir

Run in the Blender GUI: open the Scripting tab, open this file, press Run.
The scene is built so you can edit it by hand; the FBX is exported at the end
(set EXPORT_FBX = False below to skip that).

Units: 1 Blender unit = 1 metre. Water surface is at Z = 0 in Blender, which
becomes Y = 0 in Unity.

Objects exported (names matter in Unity):
    Terrain   - ground mesh, 3 materials (sand / grass / rock), mesh collider
    Water     - flat plane for the Water-tagged trigger / water shader
    Dock      - pier planks + posts
    Trees     - joined low-poly trees
    Rocks     - joined low-poly rocks
"""

import math
import os
import sys

import bpy
import bmesh
from mathutils import Vector, noise

# ----------------------------------------------------------------- settings
EXPORT_FBX = True
FBX_NAME = "LakeMap.fbx"

MAP_SIZE = 120.0        # metres, square
GRID = 80               # quads per side (bigger = smoother, heavier)
LAKE_RADIUS = 28.0      # metres, roughly
LAKE_DEPTH = 6.0        # metres below water at the lake centre
SHORE_HEIGHT = 5.0      # how high land rises around the lake
HILL_HEIGHT = 9.0       # extra height towards the map edge
SAND_MAX = 0.6          # below this height (m) = sand
ROCK_MIN = 6.5          # above this height (m) = rock
TREE_COUNT = 70
ROCK_COUNT = 25
SEED = 1


# ------------------------------------------------------------------ helpers
def parse_args():
    seed, out = SEED, None
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    i = 0
    while i < len(argv):
        if argv[i] == "--seed":
            seed = int(argv[i + 1]); i += 2
        elif argv[i] == "--out":
            out = argv[i + 1]; i += 2
        else:
            i += 1
    return seed, out


def default_out_dir():
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        repo = os.path.abspath(os.path.join(here, "..", ".."))
        path = os.path.join(repo, "Assets", "_Project", "Art", "Maps")
        if os.path.isdir(os.path.join(repo, "Assets")):
            return path
    except NameError:
        pass
    return os.path.join(os.path.expanduser("~"), "StillwaterExport")


def make_material(name, rgb, roughness=0.9):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    mat.diffuse_color = (*rgb, 1.0)
    return mat


def new_object(name, mesh):
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def flat_shade(obj):
    for p in obj.data.polygons:
        p.use_smooth = False


def height_at(x, y, seed):
    """Terrain height in metres at world (x, y)."""
    r = math.hypot(x, y)
    half = MAP_SIZE / 2.0
    # Wobbly lake outline so it is not a perfect circle.
    ang = math.atan2(y, x)
    wobble = 1.0 + 0.25 * noise.noise(Vector((math.cos(ang) * 1.5 + seed, math.sin(ang) * 1.5, 0.0)))
    lake_r = LAKE_RADIUS * wobble

    # Basin: smooth bowl inside the lake, smooth rise outside.
    t = r / lake_r
    if t < 1.0:
        h = -LAKE_DEPTH * (1.0 - t * t)
    else:
        h = SHORE_HEIGHT * (1.0 - math.exp(-(t - 1.0) * 1.6))

    # Rolling hills that grow towards the edge.
    edge = min(1.0, max(0.0, (r - lake_r) / (half - lake_r)))
    hills = noise.fractal(Vector((x * 0.04 + seed, y * 0.04, 0.0)), 0.5, 2.0, 3)
    h += HILL_HEIGHT * (edge ** 1.5) * (0.6 + hills)

    # Small bumps everywhere for a hand-made low-poly look.
    h += 0.35 * noise.noise(Vector((x * 0.25 + seed, y * 0.25, 5.0)))

    # Fade to a high rim at the very edge so players cannot walk off.
    rim = max(0.0, (max(abs(x), abs(y)) - (half - 8.0)) / 8.0)
    h += 6.0 * rim * rim
    return h


# --------------------------------------------------------------------- build
def build_terrain(mats, seed):
    mesh = bpy.data.meshes.new("Terrain")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=GRID, y_segments=GRID, size=MAP_SIZE / 2.0)
    for v in bm.verts:
        v.co.z = height_at(v.co.x, v.co.y, seed)
    for f in bm.faces:
        avg = sum(v.co.z for v in f.verts) / len(f.verts)
        if avg > ROCK_MIN:
            f.material_index = 2
        elif avg > SAND_MAX:
            f.material_index = 1
        else:
            f.material_index = 0
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    obj = new_object("Terrain", mesh)
    for m in mats:
        obj.data.materials.append(m)
    flat_shade(obj)
    return obj


def build_water(mat):
    mesh = bpy.data.meshes.new("Water")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=MAP_SIZE / 2.0 * 0.65)
    bm.to_mesh(mesh)
    bm.free()
    obj = new_object("Water", mesh)
    obj.data.materials.append(mat)
    return obj


def box(bm, center, size):
    return bmesh.ops.create_cube(bm, size=1.0, matrix=_matrix(center, size))


def _matrix(center, size):
    from mathutils import Matrix
    m = Matrix.Translation(center)
    s = Matrix.Diagonal((size[0], size[1], size[2], 1.0))
    return m @ s


def build_dock(mat, seed):
    """Pier reaching from the shore into the lake, along +X from the -X side."""
    # Find where the shore is along the -X axis so the dock starts on land.
    start_x = -LAKE_RADIUS - 4.0
    for i in range(400):
        x = -MAP_SIZE / 2.0 + i * (MAP_SIZE / 400.0)
        if height_at(x, 0.0, seed) < 0.4:
            start_x = x - 3.0
            break
    length = 16.0
    width = 2.6
    deck_z = 0.7
    mesh = bpy.data.meshes.new("Dock")
    bm = bmesh.new()
    plank_len, gap = 0.45, 0.06
    n = int(length / (plank_len + gap))
    for i in range(n):
        x = start_x + i * (plank_len + gap) + plank_len / 2.0
        box(bm, Vector((x, 0.0, deck_z)), (plank_len, width, 0.12))
    for i in range(0, n, 6):
        x = start_x + i * (plank_len + gap) + plank_len / 2.0
        for side in (-1, 1):
            box(bm, Vector((x, side * (width / 2.0 - 0.1), deck_z - 1.6)), (0.25, 0.25, 3.4))
    bm.to_mesh(mesh)
    bm.free()
    obj = new_object("Dock", mesh)
    obj.data.materials.append(mat)
    flat_shade(obj)
    return obj, start_x, length


def cone_mesh(bm, base, radius, height, segs=6):
    return bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=segs,
        radius1=radius, radius2=0.0, depth=height,
        matrix=_matrix(base + Vector((0, 0, height / 2.0)), (1, 1, 1)),
    )


def build_trees(mats, seed, dock_zone):
    trunk_mat, leaf_mat = mats
    mesh = bpy.data.meshes.new("Trees")
    bm = bmesh.new()
    rng = noise  # deterministic via seed offset
    count, tries = 0, 0
    import random
    rnd = random.Random(seed)
    half = MAP_SIZE / 2.0 - 6.0
    while count < TREE_COUNT and tries < TREE_COUNT * 40:
        tries += 1
        x, y = rnd.uniform(-half, half), rnd.uniform(-half, half)
        h = height_at(x, y, seed)
        if h < 1.2 or h > ROCK_MIN:
            continue
        if dock_zone[0] - 3 < x < dock_zone[1] + 3 and abs(y) < 6:
            continue
        s = rnd.uniform(0.8, 1.5)
        base = Vector((x, y, h - 0.1))
        before = len(bm.faces)
        # trunk
        bmesh.ops.create_cone(
            bm, cap_ends=True, segments=5, radius1=0.25 * s, radius2=0.18 * s,
            depth=1.6 * s, matrix=_matrix(base + Vector((0, 0, 0.8 * s)), (1, 1, 1)))
        trunk_faces = list(bm.faces)[before:]
        for f in trunk_faces:
            f.material_index = 0
        # two stacked foliage cones
        before = len(bm.faces)
        cone_mesh(bm, base + Vector((0, 0, 1.2 * s)), 1.3 * s, 2.2 * s)
        cone_mesh(bm, base + Vector((0, 0, 2.3 * s)), 0.95 * s, 1.9 * s)
        for f in list(bm.faces)[before:]:
            f.material_index = 1
        count += 1
    bm.to_mesh(mesh)
    bm.free()
    obj = new_object("Trees", mesh)
    obj.data.materials.append(trunk_mat)
    obj.data.materials.append(leaf_mat)
    flat_shade(obj)
    return obj


def build_rocks(mat, seed):
    import random
    rnd = random.Random(seed + 101)
    mesh = bpy.data.meshes.new("Rocks")
    bm = bmesh.new()
    half = MAP_SIZE / 2.0 - 6.0
    count, tries = 0, 0
    while count < ROCK_COUNT and tries < ROCK_COUNT * 60:
        tries += 1
        x, y = rnd.uniform(-half, half), rnd.uniform(-half, half)
        h = height_at(x, y, seed)
        # Mostly near the waterline, some on hills.
        if not (-2.0 < h < 1.5 or h > 3.5):
            continue
        s = rnd.uniform(0.5, 1.8)
        before = len(bm.verts)
        bmesh.ops.create_icosphere(
            bm, subdivisions=1, radius=s,
            matrix=_matrix(Vector((x, y, h + s * 0.2)), (1, 1, 1)))
        for v in list(bm.verts)[before:]:
            v.co += Vector((rnd.uniform(-0.2, 0.2), rnd.uniform(-0.2, 0.2), rnd.uniform(-0.15, 0.15))) * s
            v.co.z = max(v.co.z, h - 0.2)
        count += 1
    bm.to_mesh(mesh)
    bm.free()
    obj = new_object("Rocks", mesh)
    obj.data.materials.append(mat)
    flat_shade(obj)
    return obj


def add_sun_and_world():
    sun_data = bpy.data.lights.new("Sun", "SUN")
    sun_data.energy = 3.0
    sun = bpy.data.objects.new("Sun", sun_data)
    bpy.context.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(50), 0, math.radians(35))
    # Not exported to Unity (FBX export is limited to MESH below).


def export_fbx(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, FBX_NAME)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            obj.select_set(True)
    bpy.ops.export_scene.fbx(
        filepath=path,
        use_selection=True,
        object_types={"MESH"},
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL",
        bake_space_transform=True,
        axis_forward="-Z",
        axis_up="Y",
        mesh_smooth_type="FACE",
        add_leaf_bones=False,
        path_mode="COPY",
        embed_textures=False,
    )
    return path


def main():
    seed, out = parse_args()
    out_dir = out or default_out_dir()

    # Start from an empty scene.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0

    sand = make_material("Sand", (0.76, 0.69, 0.45))
    grass = make_material("Grass", (0.30, 0.55, 0.22))
    rock = make_material("Rock", (0.42, 0.42, 0.45))
    wood = make_material("Wood", (0.45, 0.30, 0.17))
    trunk = make_material("Trunk", (0.34, 0.22, 0.12))
    leaves = make_material("Leaves", (0.16, 0.42, 0.20))
    water = make_material("Water", (0.12, 0.45, 0.65), roughness=0.1)

    build_terrain([sand, grass, rock], seed)
    build_water(water)
    _, dock_x, dock_len = build_dock(wood, seed)
    build_trees([trunk, leaves], seed, (dock_x, dock_x + dock_len))
    build_rocks(rock, seed)
    add_sun_and_world()

    if EXPORT_FBX:
        path = export_fbx(out_dir)
        print(f"[Stillwater] Exported {path}")
    else:
        print("[Stillwater] Map built (FBX export disabled).")


main()
