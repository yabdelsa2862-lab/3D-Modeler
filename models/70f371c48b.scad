//========================
// Parametric Spur Gear
//========================

teeth = 20;                  // number of teeth
module = 2;                  // module (mm per tooth)
thickness = 10;              // gear thickness (mm)
pressure_angle = 20;         // degrees
clearance = 0.25 * module;   // bottom clearance (standard)
shaft_diameter = 8;          // center hole size (mm)
wall_thickness = 1.5;        // minimum printable wall thickness (mm)

// Derived parameters
pitch_diameter = teeth * module;
addendum = module;
dedendum = module + clearance;
outside_diameter = pitch_diameter + 2 * addendum;
root_diameter = pitch_diameter - 2 * dedendum;

//========================
// Involute tooth profile
//========================

// Reference radii
r_pitch = pitch_diameter / 2;
r_base = r_pitch * cos(pressure_angle);
r_add = outside_diameter / 2;
r_root = root_diameter / 2;

// Function to compute involute point (radius, angle)
function involute_xy(r) =
    let(a = sqrt((r*r)/(r_base*r_base) - 1))
    [(r_base)*(cos(a) + a*sin(a)),
     (r_base)*(sin(a) - a*cos(a))];

// Generate involute curve points
n_points = 10;
involute_pts = [
    for (i = [0:n_points]) involute_xy(r_base + (r_add - r_base) * i / n_points)
];

// Rotate and mirror to form one tooth side
module tooth_profile() {
    p = involute_pts;
    p_mirror = [for (pt = p) [pt[0], -pt[1]]];
    polygon(concat(p_mirror, reverse(p))); // closes tooth profile
}

//========================
// Assemble full gear
//========================
gear_tooth_angle = 360 / teeth;

module gear_body() {
    rotate_extrude(angle = gear_tooth_angle)
        translate([r_root, 0])
            tooth_profile();
}

union() {
    // Combine all teeth
    for (i = [0:teeth-1])
        rotate([0,0,i*gear_tooth_angle]) gear_body();

    // Central hub for strength
    difference() {
        cylinder(h = thickness, d = root_diameter - 2*wall_thickness, center = true);
        cylinder(h = thickness + 1, d = shaft_diameter, center = true);
    }
}