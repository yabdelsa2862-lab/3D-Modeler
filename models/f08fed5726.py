import trimesh, numpy as np, math

# Dimensions (all in mm)
BASE_W, BASE_L, BASE_H = 60, 80, 10
WALL = 3
ARM_LEN = 70
CLAMP_RAD = 17      # handlebar radius
CLAMP_W = 20
PHONE_W = 75
PHONE_D = 10
BACK_THICK = 4
SIDE_H = 40
GAP = 1.5           # clearance for phone width

# --- Base Plate ---
base = trimesh.creation.box(extents=[BASE_W, BASE_L, BASE_H])
base.apply_translation([0, 0, BASE_H/2])

# --- Rear Phone Support Plate ---
back = trimesh.creation.box(extents=[PHONE_W+2*WALL, BACK_THICK, PHONE_D+SIDE_H])
back.apply_translation([0, BASE_L/2 - BACK_THICK/2, (PHONE_D+SIDE_H)/2])

# --- Side Walls for Phone ---
sideL = trimesh.creation.box(extents=[WALL,  BACK_THICK + 2*WALL, PHONE_D+SIDE_H])
sideR = sideL.copy()
sideL.apply_translation([-PHONE_W/2 - WALL/2 - GAP/2, BASE_L/2, (PHONE_D+SIDE_H)/2])
sideR.apply_translation([ PHONE_W/2 + WALL/2 + GAP/2, BASE_L/2, (PHONE_D+SIDE_H)/2])

# --- Bottom Lip to stop phone sliding ---
lip = trimesh.creation.box(extents=[PHONE_W+2*WALL, BACK_THICK, WALL * 1.5])
lip.apply_translation([0, BASE_L/2 + BACK_THICK/2, WALL*0.75])

# --- Arm Connecting Base to Clamp ---
arm = trimesh.creation.box(extents=[WALL*2, ARM_LEN, WALL*3])
arm.apply_translation([0, -BASE_L/2 - ARM_LEN/2, WALL*1.5])

# --- Circular Clamp for Handlebar ---
outer = trimesh.creation.annulus(r_min=CLAMP_RAD, r_max=CLAMP_RAD+WALL, height=CLAMP_W)
outer.apply_translation([0, -BASE_L/2 - ARM_LEN - CLAMP_W/2, CLAMP_RAD+WALL/2])

# Add clamping slit
slit = trimesh.creation.box(extents=[WALL, CLAMP_W, 2*(CLAMP_RAD+WALL)])
slit.apply_translation([CLAMP_RAD+WALL/2, -BASE_L/2 - ARM_LEN - CLAMP_W/2, CLAMP_RAD+WALL/2])
outer = trimesh.boolean.difference(outer, [slit])
outer = trimesh.Trimesh(vertices=outer.vertices, faces=outer.faces, process=True)

# --- Screw hole through clamp (cross bolt) ---
bolt_hole = trimesh.creation.cylinder(radius=2, height=CLAMP_RAD*2+WALL*2, sections=64)
bolt_hole.apply_translation([0, -BASE_L/2 - ARM_LEN - CLAMP_W/2, CLAMP_RAD+WALL/2])
bolt_hole.apply_transform(trimesh.transformations.rotation_matrix(
    math.radians(90), [0,1,0], [0, -BASE_L/2 - ARM_LEN - CLAMP_W/2, CLAMP_RAD+WALL/2]))
outer = trimesh.boolean.difference(outer, [bolt_hole])
outer = trimesh.Trimesh(vertices=outer.vertices, faces=outer.faces, process=True)

# --- Combine all parts ---
model = trimesh.boolean.union([base, back, sideL, sideR, lip, arm, outer])
model = trimesh.Trimesh(vertices=model.vertices, faces=model.faces, process=True)

# --- Lift so base sits on bed ---
min_z = model.bounds[0][2]
model.apply_translation([0, 0, -min_z])