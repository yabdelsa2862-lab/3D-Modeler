import trimesh, numpy as np, math

# Dimensions (all mm)
PHONE_W, PHONE_D, PHONE_T = 75, 150, 9     # typical smartphone
CLAMP_WALL = 3                             # minimum wall thickness
CLEARANCE = 1.0                            # fitting tolerance
BACK_THICK = 4
ARM_LEN = 90
BASE_H = 8
BASE_W = 70
BASE_D = 60

# --- Base block ---
base = trimesh.creation.box(extents=[BASE_W, BASE_D, BASE_H])
base.apply_translation([0,0,BASE_H/2])

# --- Rotational post ---
post = trimesh.creation.cylinder(radius=10, height=25, sections=64)
post.apply_translation([0,0,BASE_H+12.5])
base = trimesh.boolean.union([base, post])
base = trimesh.Trimesh(vertices=np.array(base.vertices), faces=np.array(base.faces), process=False)

# --- Tilt arm ---
arm_body = trimesh.creation.box(extents=[20, ARM_LEN, CLAMP_WALL*2])
arm_body.apply_translation([0, 10+ARM_LEN/2, BASE_H+CLAMP_WALL])
arm_body.apply_transform(trimesh.transformations.rotation_matrix(
    math.radians(30), [1,0,0], [0, 0, BASE_H]))  # slight tilt upward
arm_joint = trimesh.creation.cylinder(radius=10, height=CLAMP_WALL*4, sections=64)
arm_joint.apply_translation([0,10,BASE_H+CLAMP_WALL*2])
arm = trimesh.boolean.union([arm_body, arm_joint])
arm = trimesh.Trimesh(vertices=np.array(arm.vertices), faces=np.array(arm.faces), process=False)

# --- Back plate that holds the phone ---
plate_h = PHONE_D/2
plate = trimesh.creation.box(extents=[PHONE_W+CLEARANCE*2, BACK_THICK, plate_h])
plate.apply_translation([0, ARM_LEN+BACK_THICK/2, BASE_H+CLAMP_WALL])
plate.apply_transform(trimesh.transformations.rotation_matrix(
    math.radians(30), [1,0,0], [0, ARM_LEN, BASE_H]))

# --- Side clamps ---
clamp_h = PHONE_D/2
clamp_left = trimesh.creation.box(extents=[CLAMP_WALL, BACK_THICK, clamp_h])
clamp_left.apply_translation([-PHONE_W/2-CLAMP_WALL/2, ARM_LEN+BACK_THICK/2, BASE_H+CLAMP_WALL])
clamp_left.apply_transform(trimesh.transformations.rotation_matrix(
    math.radians(30), [1,0,0], [0, ARM_LEN, BASE_H]))
clamp_right = clamp_left.copy()
clamp_right.apply_translation([PHONE_W+CLAMP_WALL,0,0])

# --- Bottom rest ---
rest = trimesh.creation.box(extents=[PHONE_W+CLEARANCE*2, CLAMP_WALL*2, BACK_THICK])
rest.apply_translation([0, ARM_LEN+BACK_THICK/2, BASE_H])
rest.apply_transform(trimesh.transformations.rotation_matrix(
    math.radians(30), [1,0,0], [0, ARM_LEN, BASE_H]))

# --- Assemble ---
model = trimesh.boolean.union([base, arm, plate, clamp_left, clamp_right, rest])
model = trimesh.Trimesh(vertices=np.array(model.vertices), faces=np.array(model.faces), process=False)

# Ensure lowest point sits on print bed
min_z = model.bounds[0,2]
model.apply_translation([0,0,-min_z])