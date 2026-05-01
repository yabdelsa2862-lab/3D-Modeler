import trimesh, numpy as np, math

# Parameters for the banana shape
L = 180.0     # overall length (mm)
R = 20.0      # approximate mid-radius of curvature
THK = 28.0    # diameter (max thickness)
SECTIONS = 64
SEGMENTS = 18  # number of cylindrical segments forming the curve

# Build the curved banana body by chaining small cylinders at varying angles
segments = []
angle_span = math.radians(60)  # total curvature in radians (~60° bend)
for i in range(SEGMENTS):
    t0 = i / SEGMENTS
    t1 = (i + 1) / SEGMENTS
    a0 = (t0 - 0.5) * angle_span
    a1 = (t1 - 0.5) * angle_span
    # position each segment along an arc
    z_mid = (L * (t0 + t1) / 2.0) - L / 2.0
    y_mid = R * math.sin((a0 + a1) / 2.0)
    x_mid = R * (1 - math.cos((a0 + a1) / 2.0))
    cyl = trimesh.creation.cylinder(radius=THK/2 * (0.9 + 0.1*np.cos(math.pi*t0)), 
                                    height=L / SEGMENTS,
                                    sections=SECTIONS)
    # rotate and translate segment to fit curve
    cyl.apply_transform(trimesh.transformations.rotation_matrix((a1+a0)/2, [0,0,1]))
    cyl.apply_translation([x_mid, y_mid, 0])
    segments.append(cyl)

banana_body = trimesh.boolean.union(segments)
banana_body = trimesh.Trimesh(vertices=np.array(banana_body.vertices),
                              faces=np.array(banana_body.faces), process=False)

# Slight taper towards each end
taper = trimesh.creation.cone(radius=THK/2, height=15, sections=SECTIONS)
taper.apply_translation([0, R*math.sin(-angle_span/2), -L/2-7.5])
banana_body = trimesh.boolean.union([banana_body, taper])
banana_body = trimesh.Trimesh(vertices=np.array(banana_body.vertices),
                              faces=np.array(banana_body.faces), process=False)
taper2 = trimesh.creation.cone(radius=THK/2 * 0.6, height=15, sections=SECTIONS)
taper2.apply_translation([R*(1-math.cos(angle_span/2)), R*math.sin(angle_span/2), L/2+7.5])
banana_body = trimesh.boolean.union([banana_body, taper2])
banana_body = trimesh.Trimesh(vertices=np.array(banana_body.vertices),
                              faces=np.array(banana_body.faces), process=False)

# Add small stem at one end
stem = trimesh.creation.cylinder(radius=5, height=15, sections=SECTIONS)
stem.apply_translation([R*(1-math.cos(angle_span/2)), R*math.sin(angle_span/2), L/2+15])
banana_body = trimesh.boolean.union([banana_body, stem])
banana_body = trimesh.Trimesh(vertices=np.array(banana_body.vertices),
                              faces=np.array(banana_body.faces), process=False)

model = banana_body

# Lift to rest on bed
lo = model.vertices[:,2].min()
if abs(lo) > 0.01:
    model.apply_translation([0,0,-lo])
    model = trimesh.Trimesh(vertices=np.array(model.vertices),
                            faces=np.array(model.faces), process=False)