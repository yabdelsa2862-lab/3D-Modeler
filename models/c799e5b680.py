import trimesh, numpy as np, math

# Dimensions (all in mm)
PHONE_W, PHONE_H, PHONE_T = 75, 150, 10          # phone size
CLAMP_TH = 5                                      # clamp wall thickness
BASE_LEN = 90
BASE_W = 45
BASE_H = 10
HANDLE_DIAM = 32
HANDLE_CLAMP_WALL = 3
HANDLE_CLAMP_THICK = 10

# --- Base plate ---
base = trimesh.creation.box(extents=[BASE_W, BASE_LEN, BASE_H])
base.apply_translation([0, 0, BASE_H/2])

# --- Chamfer long edges of base ---
for sx in [-1, 1]:
    cutter = trimesh.creation.cylinder(radius=8, height=BASE_H+2, sections=64)
    cutter.apply_translation([sx*BASE_W/2, 0, BASE_H/2])
    base = trimesh.boolean.difference([base, cutter])
    base = trimesh.Trimesh(vertices=np.array(base.vertices), faces=np.array(base.faces), process=False)

# --- Phone cradle back plate ---
cradle_back = trimesh.creation.box(extents=[PHONE_W + 2*CLAMP_TH, CLAMP_TH, PHONE_H])
cradle_back.apply_translation([0, BASE_LEN/2 - CLAMP_TH/2, PHONE_H/2])
cradle_back.apply_transform(trimesh.transformations.rotation_matrix(
    math.radians(-20), [1,0,0], [0, BASE_LEN/2 - CLAMP_TH/2, 0]))

# --- Left and right phone side clamps ---
side_clamp_h = 40
side_clamp_th = CLAMP_TH
side_clamp_d = 20

left_clamp = trimesh.creation.box(extents=[side_clamp_th, side_clamp_d, side_clamp_h])
left_clamp.apply_translation([-PHONE_W/2 - side_clamp_th/2, BASE_LEN/2, side_clamp_h/2 + 10])

right_clamp = left_clamp.copy()
right_clamp.apply_translation([PHONE_W + side_clamp_th, 0, 0])

# --- Bottom support lip ---
bottom_lip = trimesh.creation.box(extents=[PHONE_W, CLAMP_TH, 8])
bottom_lip.apply_translation([0, BASE_LEN/2 + CLAMP_TH/2, 4])

# Combine phone cradle parts
cradle = trimesh.boolean.union([cradle_back, left_clamp, right_clamp, bottom_lip])
cradle = trimesh.Trimesh(vertices=np.array(cradle.vertices), faces=np.array(cradle.faces), process=False)

# --- Handlebar clamp ring (split design) ---
outer_r = HANDLE_DIAM/2 + HANDLE_CLAMP_WALL
ring_part = trimesh.creation.annulus(r_min=HANDLE_DIAM/2, r_max=outer_r, height=HANDLE_CLAMP_THICK)
ring_part.apply_translation([0, -BASE_LEN/2 - HANDLE_CLAMP_THICK/2, HANDLE_DIAM/2])

# Cut flat on top for mounting to base
flat_cut = trimesh.creation.box(extents=[BASE_W+20, HANDLE_CLAMP_THICK, HANDLE_DIAM])
flat_cut.apply_translation([0, -BASE_LEN/2 - HANDLE_CLAMP_THICK/2, HANDLE_DIAM])
ring_part = trimesh.boolean.difference([ring_part, flat_cut])
ring_part = trimesh.Trimesh(vertices=np.array(ring_part.vertices), faces=np.array(ring_part.faces), process=False)

# Create matching clamp segment (for screws)
clamp_seg = trimesh.creation.box(extents=[BASE_W/2, HANDLE_CLAMP_THICK, HANDLE_DIAM/2])
clamp_seg.apply_translation([BASE_W/4, -BASE_LEN/2 - HANDLE_CLAMP_THICK/2, HANDLE_DIAM/2])

# Union all major parts
model = trimesh.boolean.union([base, cradle, ring_part, clamp_seg])
model = trimesh.Trimesh(vertices=np.array(model.vertices), faces=np.array(model.faces), process=False)