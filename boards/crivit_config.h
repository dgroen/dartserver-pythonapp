/**
 * CRIVIT DARTBOARD CONFIGURATION
 *
 * This header file defines the GPIO pin mappings and board-specific settings
 * for the Crivit dartboard using a 7x12 GPIO matrix.
 *
 * Hardware Configuration:
 * - Master Lines (Rows): 7 GPIO pins that are set to LOW sequentially
 * - Slave Lines (Columns): 12 GPIO pins that are monitored with INPUT_PULLUP
 * - Dart Detection: When dart shorts a pin combination, slave pin is pulled LOW
 *
 * Board Type: crivit
 * Matrix Size: 7x12 = 84 possible zones
 * ESP32 GPIO Pins Used: 2, 4, 16, 17, 5, 18, 19 (master), 21, 22, 23, 13, 12, 14, 27, 26, 25, 33, 32, 15 (slave)
 * Total: 19 GPIO pins
 */

#ifndef CRIVIT_CONFIG_H
#define CRIVIT_CONFIG_H

// ============================================================================
// BOARD IDENTIFICATION
// ============================================================================
/**
 * BOARD_TYPE: Unique identifier matching database dartboard_types.name
 * This is used to look up zone mappings in the database.
 *
 * The server will query: SELECT * FROM dartboard_zone_mappings
 * WHERE dartboard_type_id = (SELECT id FROM dartboard_types WHERE name = BOARD_TYPE)
 * AND master_pin = masterPin AND slave_pin = slavePin
 */
const char* BOARD_TYPE = "crivit";

/**
 * BOARD_NAME: Human-readable name for logging and display
 */
const char* BOARD_NAME = "Crivit Dartboard";

// ============================================================================
// MATRIX DIMENSIONS
// ============================================================================
/**
 * masterLines: Number of GPIO pins used for matrix rows (scanning rows)
 * These pins are set to LOW sequentially to scan for dart presses
 */
const int masterLines = 7;

/**
 * slaveLines: Number of GPIO pins used for matrix columns (sensing columns)
 * These pins are monitored with INPUT_PULLUP and go LOW when dart shorts
 */
const int slaveLines = 12;

// ============================================================================
// GPIO PIN MAPPINGS
// ============================================================================
/**
 * matrixMaster[]: GPIO pins for rows (master/scanning lines)
 *
 * When a row is scanned:
 * 1. This GPIO pin is set to LOW
 * 2. All slave pins (columns) are scanned
 * 3. If any slave pin is LOW, a dart is detected at that (master, slave) intersection
 * 4. The GPIO pin is set back to HIGH
 *
 * Order matters: This maps to the physical row order on your dartboard.
 * Index corresponds to the row number in your GPIO matrix.
 *
 * NOTE: Crivit board uses different pins than Carromco due to physical layout
 */
int matrixMaster[] = {
  2,   // Row 0 (Master Pin 2)
  4,   // Row 1 (Master Pin 4)
  16,  // Row 2 (Master Pin 16)
  17,  // Row 3 (Master Pin 17)
  5,   // Row 4 (Master Pin 5)
  18,  // Row 5 (Master Pin 18)
  19   // Row 6 (Master Pin 19)
};

/**
 * matrixSlave[]: GPIO pins for columns (slave/sensing lines)
 *
 * These pins use INPUT_PULLUP, so they default to HIGH.
 * When a dart shorts a zone, the slave pin is pulled LOW.
 * The throwCheck() function scans these pins while each master row is active.
 *
 * Order matters: This maps to the physical column order on your dartboard.
 * Index corresponds to the column number in your GPIO matrix.
 *
 * NOTE: Crivit uses 12 columns vs Carromco's 8
 */
int matrixSlave[] = {
  21,  // Col 0 (Slave Pin 21)
  22,  // Col 1 (Slave Pin 22)
  23,  // Col 2 (Slave Pin 23)
  13,  // Col 3 (Slave Pin 13)
  12,  // Col 4 (Slave Pin 12)
  14,  // Col 5 (Slave Pin 14)
  27,  // Col 6 (Slave Pin 27)
  26,  // Col 7 (Slave Pin 26)
  25,  // Col 8 (Slave Pin 25)
  33,  // Col 9 (Slave Pin 33)
  32,  // Col 10 (Slave Pin 32)
  15   // Col 11 (Slave Pin 15)
};

// ============================================================================
// ZONE MAPPING REFERENCE
// ============================================================================
/**
 * ZONE MAPPING MATRIX (for reference/debugging)
 *
 * This Crivit board has a much larger 7x12 matrix compared to Carromco's 8x8.
 * The mappings are more complex due to the different physical layout.
 *
 * All zone mappings are stored in the database:
 * - table: dartboard_zone_mappings
 * - filtered by: dartboard_type_id where name = 'crivit'
 *
 * To view the current mappings:
 * 1. Admin panel: https://yourserver/admin/dartboard-testing
 * 2. Select "crivit" from the dartboard type dropdown
 * 3. The GPIO Matrix tab shows all current mappings
 *
 * Or query directly:
 * SELECT master_pin, slave_pin, zone_number, multiplier_type, base_value
 * FROM dartboard_zone_mappings
 * WHERE dartboard_type_id = (SELECT id FROM dartboard_types WHERE name = 'crivit')
 * ORDER BY master_pin, slave_pin;
 */

// ============================================================================
// DIFFERENCES FROM CARROMCO
// ============================================================================
/**
 * Key differences between Crivit and Carromco:
 *
 * 1. MATRIX SIZE:
 *    - Carromco: 8x8 = 64 zones
 *    - Crivit: 7x12 = 84 zones
 *    - Crivit has more columns for finer dartboard resolution
 *
 * 2. GPIO PINS:
 *    - Different physical ESP32 pins used
 *    - Some pins may have different electrical properties
 *    - Pin order may affect scanning speed
 *
 * 3. ZONE COMPLEXITY:
 *    - More zones means more potential configurations
 *    - Admin panel easily handles both via database
 *    - No code changes needed - just different configuration headers
 *
 * 4. HARDWARE DEBOUNCING:
 *    - May need different debounce delays in throwCheck()
 *    - Modify delay(500) in main sketch if needed
 */

// ============================================================================
// CALIBRATION INSTRUCTIONS
// ============================================================================
/**
 * To set up or recalibrate Crivit dartboard zones:
 *
 * FIRST TIME SETUP:
 * 1. Register Crivit board type in database:
 *    python helpers/setup_dartboard_types.py crivit
 *
 * 2. Set up initial zone mappings via admin panel:
 *    - Navigate to https://yourserver/admin/dartboard-testing
 *    - Select "crivit" from dartboard type dropdown
 *    - Use "Manual Mapping" tab to map zones
 *    - Or use "Bulk Import" tab to load from CSV
 *
 * ONGOING MAINTENANCE:
 * 1. If zones change (worn dartboard, physical adjustment):
 *    - Use admin panel to update mappings
 *    - No Arduino reflash needed!
 *    - Changes take effect immediately
 *
 * 2. For periodic calibration:
 *    - Use admin panel to verify zone detection
 *    - Watch real-time message log
 *    - Adjust mappings as needed
 *
 * TROUBLESHOOTING:
 * - Zone not detected: Check physical dartboard wiring
 * - Wrong zone detected: Verify pin mappings in this file
 * - All zones inactive: Check ESP32 GPIO pin connections
 * - WiFi issues: Check network configuration in dartserver_generic.ino
 */

// ============================================================================
// NOTES FOR DEVELOPERS
// ============================================================================
/**
 * Why separate configuration files instead of hardcoding?
 *
 * 1. FLEXIBILITY: Multiple board types without code duplication
 * 2. MAINTAINABILITY: Easy to add new board types
 * 3. CLARITY: Board-specific constants clearly separated
 * 4. EXTENSIBILITY: Can add per-board calibration data
 *
 * To add a new board type:
 * 1. Create newboard_config.h with GPIO mappings
 * 2. Include it in dartserver_generic.ino: #include "newboard_config.h"
 * 3. Define zone mappings in database via admin panel
 * 4. Upload sketch - done! No code recompilation needed for zone changes
 */

// ============================================================================
// VERIFICATION
// ============================================================================
#if masterLines != (sizeof(matrixMaster)/sizeof(matrixMaster[0]))
  #error "masterLines count doesn't match matrixMaster array size"
#endif

#if slaveLines != (sizeof(matrixSlave)/sizeof(matrixSlave[0]))
  #error "slaveLines count doesn't match matrixSlave array size"
#endif

#endif // CRIVIT_CONFIG_H
