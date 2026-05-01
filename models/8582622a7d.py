import trimesh, numpy as np, math

# ---------- PARAMETERS ----------
L   = 180    # overall banana length
R   = 18     # average radius
CURV = 0.002 # curvature (1/radius of bend)
SEGS = 30    # number of segments for smooth curve

# ---------- CREATE SEGMENTS ALONG CURVED ARC ----------
segments = []
for i in range(SEGS):
    ang = (i - SEGS/2) * CURV * L/SEGS
    cyl = trimesh.creation.cylinder(radius=R, height=L/SEGS, sections=64)
    # position cylinder segment along curved path
    x = math.sin(ang) * (L/SEGS * i)
    y = 0
    z = math.cos(ang) * (L/SEGS * i)
    cyl.apply_translation([x, y, z])
    rot = trimesh.transformations.rotation_matrix(-ang * 180 / math.pi, [0, 1, 0], [x, y, z])
    cyl.apply_transform(rot)
    segments.append(cyl)

banana_body = trimesh.boolean.union(segments)
banana_body = trimesh.Trimesh(vertices=np.array(banana_body.vertices),
                              faces=np.array(banana_body.faces), process=False)

# ---------- TAPER ENDS ----------
cone_tip_1 = trimesh.creation.cone(radius=R, height=20)
cone_tip_1.apply_translation([-L/2, 0, R])
cone_tip_2 = trimesh.creation.cone(radius=R, height=20)
cone_tip_2.apply_transform(trimesh.transformations.rotation_matrix(
    math.radians(180), [0,1,0], [0,0,0]))
cone_tip_2.apply_translation([L/2, 0, R])

banana = trimesh.boolean.union([banana_body, cone_tip_1, cone_tip_2])
banana = trimesh.Trimesh(vertices=np.array(banana.vertices),
                         faces=np.array(banana.faces), process=False)

# Slightly offset so the lowest surface touches z=0
banana.apply_translation([0, 0, R])
model = banana