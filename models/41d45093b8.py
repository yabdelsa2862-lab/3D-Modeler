import trimesh, numpy as np, math

# ━━━ PARAMETERS ━━━
BODY_W, BODY_H, BODY_D = 70, 120, 6       # phone contact plate
CLAMP_TH, CLAMP_WALL = 4, 3               # thicknesses
GRIP_DEPTH, GRIP_HEIGHT = 15, 40          # side grips
HANDLE_R, HANDLE_OFFSET = 16, 10          # handlebar radius and clamp offset
BOLT_R, BOLT_CLR = 2, 4

# ━━━ MAIN BODY ━━━
back_plate = trimesh.creation.box(extents=[BODY_W, BODY_D, BODY_H])
back_plate.apply_translation([0, 0, BODY_H/2])

# Chamfer sides for aesthetics
for sx in (-1, 1):
    chamfer = trimesh.creation.cylinder(radius=10, height=BODY_H)
    chamfer.apply_translation([sx*BODY_W/2, BODY_D/2, BODY_H/2])
    back_plate = trimesh.boolean.difference(back_plate, chamfer)
    back_plate = trimesh.Trimesh(vertices=np.array(back_plate.vertices),
                                 faces=np.array(back_plate.faces), process=False)

# ━━━ SIDE GRIPS ━━━
grip_L = trimesh.creation.box(extents=[CLAMP_TH, GRIP_DEPTH, GRIP_HEIGHT])
grip_R = grip_L.copy()

grip_L.apply_translation([-BODY_W/2 - CLAMP_TH/2, 0, GRIP_HEIGHT/2 + BODY_H - GRIP_HEIGHT])
grip_R.apply_translation([BODY_W/2 + CLAMP_TH/2, 0, GRIP_HEIGHT/2 + BODY_H - GRIP_HEIGHT])

# small angle inward for wedge grip
for g, s in zip([grip_L, grip_R], [-1, 1]):
    tf = trimesh.transformations.rotation_matrix(math.radians(7*s), [0,1,0], [s*(BODY_W/2),0,BODY_H])
    g.apply_transform(tf)

# ━━━ HANDLEBAR CLAMP ━━━
# base block for clamp arms
clamp_base = trimesh.creation.box(extents=[BODY_W/2, CLAMP_TH*3, CLAMP_TH*5])
clamp_base.apply_translation([0, BODY_D/2 + CLAMP_TH*1.5, CLAMP_TH*2.5])

# cylindrical cut-out for handlebar
handle_cut = trimesh.creation.cylinder(radius=HANDLE_R+BOLT_CLR, height=BODY_W*0.8, sections=64)
handle_cut.apply_translation([0, BODY_D/2 + HANDLE_OFFSET, 0])
handle_cut.apply_transform(trimesh.transformations.rotation_matrix(
    math.radians(90), [1,0,0], [0,BODY_D/2+HANDLE_OFFSET,0]))
clamp_base = trimesh.boolean.difference(clamp_base, handle_cut)
clamp_base = trimesh.Trimesh(vertices=np.array(clamp_base.vertices),
                             faces=np.array(clamp_base.faces), process=False)

# bolt holes through clamp
bolt = trimesh.creation.cylinder(radius=BOLT_R, height=BODY_W, sections=32)
bolt.apply_translation([0, BODY_D/2 + HANDLE_OFFSET, CLAMP_TH*2])
for off in [-HANDLE_R, HANDLE_R]:
    hole = bolt.copy()
    hole.apply_translation([off, 0, 0])
    clamp_base = trimesh.boolean.difference(clamp_base, hole)
    clamp_base = trimesh.Trimesh(vertices=np.array(clamp_base.vertices),
                                 faces=np.array(clamp_base.faces), process=False)

# ━━━ FINAL ASSEMBLY ━━━
model = trimesh.boolean.union([back_plate, grip_L, grip_R, clamp_base])
model = trimesh.Trimesh(vertices=np.array(model.vertices), faces=np.array(model.faces), process=False)

# sit flush on print-bed
zmin = model.bounds[0][2]
model.apply_translation([0, 0, -zmin])