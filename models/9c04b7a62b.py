import trimesh, numpy as np, math

# Bike Phone Mount dimensions — all in mm
CLAMP_RADIUS = 16         # fits typical handlebar (≈32mm Ø)
CLAMP_THICK  = 4
CLAMP_WIDTH  = 20
ARM_LEN      = 70
ARM_THICK    = 6
HOLDER_W     = 80
HOLDER_H     = 15
HOLDER_D     = 10
WALL         = 3
PAD_RAD      = 6

# --- Handlebar clamp ---
outer = trimesh.creation.cylinder(radius=CLAMP_RADIUS+CLAMP_THICK, height=CLAMP_WIDTH, sections=64)
inner = trimesh.creation.cylinder(radius=CLAMP_RADIUS, height=CLAMP_WIDTH+2, sections=64)
inner.apply_translation([0,0,0])
clamp = trimesh.boolean.difference([outer, inner])
clamp = trimesh.Trimesh(vertices=np.array(clamp.vertices), faces=np.array(clamp.faces), process=False)

# Flatten ends for bolt holes
flat = trimesh.creation.box(extents=[CLAMP_RADIUS*2, CLAMP_WIDTH, CLAMP_THICK])
flat.apply_translation([0, CLAMP_WIDTH/2, CLAMP_RADIUS])
clamp = trimesh.boolean.union([clamp, flat])
clamp = trimesh.Trimesh(vertices=np.array(clamp.vertices), faces=np.array(clamp.faces), process=False)

# --- Bolt holes through clamp ---
for y in [-CLAMP_WIDTH/2+4, CLAMP_WIDTH/2-4]:
    hole = trimesh.creation.cylinder(radius=2.2, height=CLAMP_RADIUS*3, sections=32)
    hole.apply_rotation = None
    hole.apply_translation([0, y, 0])
    clamp = trimesh.boolean.difference([clamp, hole])
    clamp = trimesh.Trimesh(vertices=np.array(clamp.vertices), faces=np.array(clamp.faces), process=False)

clamp.apply_translation([0, 0, CLAMP_RADIUS+CLAMP_THICK/2])

# --- Arm connecting clamp to phone holder ---
arm = trimesh.creation.box(extents=[ARM_LEN, ARM_THICK, ARM_THICK])
arm.apply_translation([ARM_LEN/2 + CLAMP_RADIUS + CLAMP_THICK/2, 0, ARM_THICK/2 + CLAMP_RADIUS])
arm_base_fil = trimesh.creation.cylinder(radius=ARM_THICK/2, height=CLAMP_RADIUS*2, sections=64)
arm_base_fil.apply_translation([CLAMP_RADIUS+CLAMP_THICK/2, 0, ARM_THICK/2 + CLAMP_RADIUS])
arm = trimesh.boolean.union([arm, arm_base_fil])
arm = trimesh.Trimesh(vertices=np.array(arm.vertices), faces=np.array(arm.faces), process=False)

# --- Phone holder plate ---
plate = trimesh.creation.box(extents=[HOLDER_W, HOLDER_D, HOLDER_H])
plate.apply_translation([CLAMP_RADIUS+ARM_LEN, 0, CLAMP_RADIUS+ARM_THICK+HOLDER_H/2])

# --- Side lips for phone ---
lip_left  = trimesh.creation.box(extents=[WALL, HOLDER_D, HOLDER_H+10])
lip_left.apply_translation([CLAMP_RADIUS+ARM_LEN - HOLDER_W/2 - WALL/2, 0, CLAMP_RADIUS+ARM_THICK+(HOLDER_H+10)/2])
lip_right = trimesh.creation.box(extents=[WALL, HOLDER_D, HOLDER_H+10])
lip_right.apply_translation([CLAMP_RADIUS+ARM_LEN + HOLDER_W/2 + WALL/2, 0, CLAMP_RADIUS+ARM_THICK+(HOLDER_H+10)/2])

# --- Rubber pads slots on plate ---
for x in [-HOLDER_W/3, HOLDER_W/3]:
    padcut = trimesh.creation.cylinder(radius=PAD_RAD, height=HOLDER_D+2, sections=64)
    padcut.apply_translation([CLAMP_RADIUS+ARM_LEN + x, 0, CLAMP_RADIUS+ARM_THICK])
    plate = trimesh.boolean.difference([plate, padcut])
    plate = trimesh.Trimesh(vertices=np.array(plate.vertices), faces=np.array(plate.faces), process=False)

# --- Merge all parts ---
model = trimesh.boolean.union([clamp, arm, plate, lip_left, lip_right])
model = trimesh.Trimesh(vertices=np.array(model.vertices), faces=np.array(model.faces), process=False)

# Sit on print bed
bbox = model.bounds
model.apply_translation([0, 0, -bbox[0,2]])