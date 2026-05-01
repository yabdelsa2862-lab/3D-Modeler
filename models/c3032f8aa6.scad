// Phone Stand with 15° tilt and cable slot
// All units in millimeters

// Parameters
phone_width = 75;          // Typical phone width
phone_thickness = 10;      // Typical phone thickness
stand_thickness = 1.5;     // Min wall thickness
base_depth = 90;           // Front-to-back depth
base_width = 90;           // Total width
back_height = 100;         // Support height
tilt_angle = 15;           // Tilt of phone support
lip_height = 8;            // Retaining lip height
cable_slot_width = 12;     // Cable slot width
cable_slot_height = 8;     // Cable slot height
cable_slot_offset = 10;    // Distance from front edge

// Derived
support_thickness = stand_thickness * 2;

// Modules
module base() {
    // Slightly tapered base for rigidity
    hull() {
        translate([0, 0, 0])
            cube([base_width, stand_thickness, stand_thickness]);
        translate([0, base_depth, stand_thickness])
            cube([base_width, stand_thickness, stand_thickness]);
    }
}

module back_support() {
    // Back plate holding the phone at an angle
    rotate([tilt_angle, 0, 0])
        translate([0, -phone_thickness/2, 0])
            cube([base_width, support_thickness, back_height]);
}

module front_lip() {
    // Retaining lip to keep phone from sliding off
    translate([0, cable_slot_offset, 0])
        cube([base_width, stand_thickness * 2, lip_height]);
}

module cable_slot() {
    // Slot for charging cable
    translate([(base_width - cable_slot_width)/2, 0, 0])
        cube([cable_slot_width, stand_thickness * 2, cable_slot_height]);
}

// Assembly
difference() {
    union() {
        base();
        // Create angled support
        translate([0, 0, stand_thickness])
            back_support();
        // Lip offset to align with inclined support
        front_lip();
    }
    // Cutout for cable slot
    cable_slot();
}