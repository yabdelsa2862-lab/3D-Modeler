import trimesh, numpy as np, math

# ---------- PARAMETERS ----------
ARM_LEN = 45        # gripping arm length
ARM_W   = 15
ARM_TH  = 3
BASE_D  = 55        # base diameter around handlebar
BAR_R   = 15        # inner radius for handlebar
CLAMP_TH = 3        # clamp wall thickness
PHONE_W  = 80
PHONE_T  = 10
GRIP_PAD = 2

# ---------- HANDLEBAR CLAMP ----------
outer_r = BAR_R + CLAMP_TH
clamp = trimesh.creation.annulus(r_min=BAR_R, r_max=outer_r, height=20)
clamp.apply_translation([0, 0, 10])  # bottom at z=0

# split open with a slot for tightening
slot = trimesh.creation.box(extents=[10, outer_r*2, 30])
slot.apply_translation([outer_r, 0, 15])
clamp = trimesh.boolean.difference([clamp, slot])
clamp = trimesh.Trimesh(vertices=np.array(clamp.vertices),
                        faces=np.array(clamp.faces), process=False)

# Add bolt holes through clamp ends
for side in [1, -1]:
    hole = trimesh.creation.cylinder(radius=2, height=25, sections=64)
    hole.apply_translation([side*(outer_r+1), 0, 10])
    clamp = trimesh.boolean.difference([clamp, hole])
    clamp = trimesh.Trimesh(vertices=np.array(clamp.vertices),
                            faces=np.array(clamp.faces), process=False)

# ---------- SWIVEL BASE ----------
base_disc = trimesh.creation.cylinder(radius=BASE_D/2, height=4, sections=64)
base_disc.apply_translation([0, 0, 2])  # sit on clamp top
# link clamp to base
connector = trimesh.creation.cylinder(radius=outer_r-1, height=4)
connector.apply_translation([0, 0, 20+2])
mount_base = trimesh.boolean.union([clamp, base_disc, connector])
mount_base = trimesh.Trimesh(vertices=np.array(mount_base.vertices),
                             faces=np.array(mount_base.faces), process=False)

# ---------- ARMS ----------
def make_arm(sign):
    arm = trimesh.creation.box(extents=[ARM_W, ARM_TH, ARM_LEN])
    arm.apply_translation([sign*(PHONE_W/2 - ARM_W/2), 0, 20 + 4 + ARM_LEN/2])
    # round tip with small pad
    pad = trimesh.creation.cylinder(radius=ARM_W/2, height=GRIP_PAD, sections=64)
    pad.apply_translation([sign*(PHONE_W/2 - ARM_W/2), 0, 20 + 4 + ARM_LEN + GRIP_PAD/2])
    return trimesh.boolean.union([arm, pad])

arm_left  = make_arm(-1)
arm_right = make_arm(1)
arm_left  = trimesh.Trimesh(vertices=np.array(arm_left.vertices), faces=np.array(arm_left.faces), process=False)
arm_right = trimesh.Trimesh(vertices=np.array(arm_right.vertices), faces=np.array(arm_right.faces), process=False)

# ---------- BACK PLATE ----------
back_plate = trimesh.creation.box(extents=[PHONE_W, PHONE_T, ARM_TH])
back_plate.apply_translation([0, 0, 20 + 4 + ARM_LEN - ARM_TH/2])

# add small side tabs to hold phone securely
for sx in [-1, 1]:
    tab = trimesh.creation.box(extents=[ARM_TH, PHONE_T + 4, 10])
    tab.apply_translation([sx*(PHONE_W/2 - ARM_TH/2), 0, 20 + 4 + ARM_LEN - 5])
    back_plate = trimesh.boolean.union([back_plate, tab])
    back_plate = trimesh.Trimesh(vertices=np.array(back_plate.vertices),
                                 faces=np.array(back_plate.faces), process=False)

# ---------- FINAL ASSEMBLY ----------
model = trimesh.boolean.union([mount_base, arm_left, arm_right, back_plate])
model = trimesh.Trimesh(vertices=np.array(model.vertices),
                        faces=np.array(model.faces), process=False)