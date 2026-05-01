//===================================================
// Parametric Spur Gear - 20 Teeth, Module 2
// Designed for FDM printing
//===================================================

//------------- Parameters --------------------------
teeth = 20;
module = 2;
thickness = 10;
pressure_angle = 20; // standard involute gear pressure angle, degrees
resolution = 100;    // curve smoothness

//------------- Derived dimensions ------------------
pitch_dia = teeth * module; // pitch diameter
base_dia = pitch_dia * cos(pressure_angle);
addendum = module;
dedendum = 1.25 * module;
outside_dia = pitch_dia + 2 * addendum;
root_dia = pitch_dia - 2 * dedendum;
tooth_thickness = (pi * module) / 2;

//===================================================
// Generate the gear
//===================================================

module gear() {
    difference() {
        // Main gear body from cylinder
        linear_extrude(height = thickness, center = true) {
            gear2d();
        }
    }
}

// 2D involute gear profile
module gear2d() {
    n = teeth;
    for (i = [0 : n - 1]) {
        rotate(i * 360 / n)
            tooth_profile();
    }
}

// Generate a single tooth using approximate involute flank
module tooth_profile() {
    steps = resolution;
    points = [];
    a_base = base_dia / 2;
    r_out = outside_dia / 2;
    r_root = root_dia / 2;

    // Involute curve points from base circle to outer circle
    for (j = [0 : steps]) {
        t = j / steps * acos(a_base / r_out);
        x = a_base * (cos(t) + t * sin(t));
        y = a_base * (sin(t) - t * cos(t));
        points = concat(points, [[x, y]]);
    }

    // Mirror for other side of tooth
    mirrored = [for (p = reverse(points)) [p[0], -p[1]]];

    // Close the root area
    tooth = concat(points, [[r_out*cos(0), r_out*sin(0)]], mirrored, [[r_root, 0]]);
    
    rotate(-180/teeth)  // Center tooth around Y-axis
        polygon(tooth);
}

//===================================================
gear();