// ==============================
// Parameters
// ==============================
phone_width = 80;           // Standard phone width
phone_thickness = 10;       // Typical phone thickness
stand_height = 100;         // Overall height of stand
base_depth = 80;            // Depth of base platform
base_width = phone_width + 20;  // Add clearance on sides
wall_thickness = 2;         // Minimum wall thickness (>=1.5mm)
tilt_angle = 15;            // Tilt angle of support
cable_slot_width = 12;      // Slot for charging cable
cable_slot_height = 8;      // Height of slot opening
slot_offset = 20;           // Distance from rear edge of base

// ==============================
// Modules
// ==============================

// Main inclined back support
module back_support() {
    tilt_radians = tilt_angle * PI / 180;
    support_thickness = wall_thickness * 2;
    support_height = stand_height;
    support_width = phone_width + 10;
    
    // Rectangular plate for phone rest
    hull() {
        translate([0, 0, 0])
            cube([support_width, support_thickness, support_height], center=false);
        translate([0, support_thickness, support_height*sin(tilt_radians)])
            cube([support_width, support_thickness, support_height], center=false);
    }
}

// Lower lip that holds phone bottom
module bottom_shelf() {
    shelf_depth = 20;
    shelf_height = 10;
    translate([(base_width - phone_width)/2, 0, 0])
        cube([phone_width, shelf_depth, shelf_height]);
}

// Base platform with cable slot cutout
module base_platform() {
    difference() {
        cube([base_width, base_depth, wall_thickness * 4]);
        // Cable slot
        translate([(base_width - cable_slot_width)/2, base_depth - slot_offset, -1])
            cube([cable_slot_width, wall_thickness*6, cable_slot_height + 2]);
    }
}

// ==============================
// Assembly
// ==============================
module phone_stand() {
    base_platform();
    // Position back support at 15° tilt
    translate([(base_width - phone_width)/2, wall_thickness * 4, wall_thickness*4])
        rotate([tilt_angle, 0, 0])
            back_support();
    // Add the bottom shelf in front of the support
    translate([0, 10, wall_thickness*4])
        bottom_shelf();
}

// ==============================
// Render
// ==============================
phone_stand();