// =======================
// Parameters
// =======================
base_width = 80;
base_depth = 100;
base_thickness = 4;
back_height = 100;
wall_thickness = 3;
tilt_angle = 15;       // degrees
slot_width = 12;
slot_height = 8;
slot_depth = 15;

// =======================
// Modules
// =======================

// Main base and back support plate
module stand_body() {
    // Base platform
    base = cube([base_width, base_depth, base_thickness]);
    
    // Back support angled at tilt_angle
    translate([0, 0, base_thickness])
        rotate([-tilt_angle, 0, 0])
            translate([0, 0, 0])
                cube([base_width, wall_thickness, back_height]);
    
    union() {
        base;
        translate([0, 0, base_thickness])
            rotate([-tilt_angle, 0, 0])
                cube([base_width, wall_thickness, back_height]);
    }
}

// Cable slot at the base front center
module cable_slot() {
    translate([
        (base_width - slot_width)/2,
        -slot_depth/2,
        0
    ])
    cube([slot_width, slot_depth, slot_height]);
}

// =======================
// Assembly
// =======================
difference() {
    // Combine base and angled back
    stand_body();
    // Subtract slot cutout
    cable_slot();
}