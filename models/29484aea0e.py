import trimesh, numpy as np, math

# Dimensions (in mm)
BODY_W, BODY_H, BODY_D = 70, 15, 120       # main clamp body
ARM_LEN, ARM_TH = 25, 5                    # phone-holding arms
BAR_DIAM, BAR_CLAMP_W, BAR_CLAMP_T = 25, 20, 4  # bike handlebar clamp basics
SCREW_HOLE_R = 3
WALL = 2

# --- Main clamp body ---
body = trimesh.creation.box(extents=[BODY_W, BODY_D, BODY_H])
body.apply_translation([0, 0, BODY_H/2])

# --- Phone arms (angled, no overhangs) ---
# Left arm
arm_left = trimesh.creation.box(extents=[ARM_TH, BODY_D, ARM_LEN])
arm_left.apply_translation([-BODY_W/2 - ARM_TH/2, 0, BODY_H - 10])
rot_tf = trimesh.transformations.rotation_matrix(math.radians(-15), [0,1,0], [-BODY_W/2,0,BODY_H])
arm_left.apply_transform(rot_tf)

# Right arm
arm_right = trimesh.creation.box(extents=[ARM_TH, BODY_D, ARM_LEN])
arm_right.apply_translation([BODY_W/2 + ARM_TH/2, 0, BODY_H - 10])
rot_tf = trimesh.transformations.rotation_matrix(math.radians(15), [0,1,0], [BODY_W/2,0,BODY_H])
arm_right.apply_transform(rot_tf)

# --- Phone bed plate ---
plate = trimesh.creation.box(extents=[BODY_W-10, WALL, BODY_H])
plate.apply_translation([0, BODY_D/2 + WALL/2, BODY_H/2])

# --- Handlebar clamp halves ---
bar_cyl = trimesh.creation.annulus(r_min=BAR_DIAM/2, r_max=BAR_DIAM/2 + BAR_CLAMP_T, height=BAR_CLAMP_W)
bar_cyl.apply_translation([0, -BODY_D/2 - BAR_CLAMP_W/2, BAR_DIAM/2 + WALL])
bar_cut = trimesh.creation.box(extents=[BODY_W+20, BAR_CLAMP_W, BAR_DIAM])
bar_cut.apply_translation([0, -BODY_D/2 - BAR_CLAMP_W/2, BAR_DIAM/2])
clamp_half = trimesh.boolean.difference(bar_cyl, [bar_cut])
clamp_half = trimesh.Trimesh(vertices=np.array(clamp_half.vertices), faces=np.array(clamp_half.faces), process=False)

# Screw holes for M3 bolts on clamp
for sx in [-10, 10]:
    hole = trimesh.creation.cylinder(radius=SCREW_HOLE_R, height=BAR_CLAMP_W+2, sections=64)
    hole.apply_translation([sx, -BODY_D/2 - BAR_CLAMP_W/2, BAR_DIAM/2 + 2])
    clamp_half = trimesh.boolean.difference(clamp_half, [hole])
    clamp_half = trimesh.Trimesh(vertices=np.array(clamp_half.vertices), faces=np.array(clamp_half.faces), process=False)

# Lower support rib under body
rib = trimesh.creation.box(extents=[BODY_W, BAR_CLAMP_W, WALL])
rib.apply_translation([0, -BODY_D/2 - BAR_CLAMP_W/2, WALL/2])

# --- Combine all parts ---
model = trimesh.boolean.union([body, arm_left, arm_right, plate, clamp_half, rib])
model = trimesh.Trimesh(vertices=np.array(model.vertices), faces=np.array(model.faces), process=False)

# ensure sits on bed level
z_min = model.bounds[0][2]
model.apply_translation([0, 0, -z_min])