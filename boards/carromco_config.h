/**
 * CARROMCO STRIKER DARTBOARD CONFIGURATION
 *
 * This header file defines the GPIO pin mappings and board-specific settings
 * for the Carromco Striker dartboard using an 8x8 GPIO matrix.
 *
 * Hardware Configuration:
 * - Master Lines (Rows): 8 GPIO pins that are set to LOW sequentially
 * - Slave Lines (Columns): 8 GPIO pins that are monitored with INPUT_PULLUP
 * - Dart Detection: When dart shorts a pin combination, slave pin is pulled LOW
 *
 * Board Type: carromco
 * Matrix Size: 8x8 = 64 possible zones
 * ESP32 GPIO Pins Used: 15, 2, 4, 16, 17, 5, 18, 19, 13, 12, 14, 27, 26, 25, 33, 32
 * Total: 16 GPIO pins
 */

#ifndef CARROMCO_CONFIG_H
#define CARROMCO_CONFIG_H

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
const char* BOARD_TYPE = "carromco";

/**
 * BOARD_NAME: Human-readable name for logging and display
 */
const char* BOARD_NAME = "Carromco Striker";

// ============================================================================
// MATRIX DIMENSIONS
// ============================================================================
/**
 * masterLines: Number of GPIO pins used for matrix rows (scanning rows)
 * These pins are set to LOW sequentially to scan for dart presses
 */
const int masterLines = 8;

/**
 * slaveLines: Number of GPIO pins used for matrix columns (sensing columns)
 * These pins are monitored with INPUT_PULLUP and go LOW when dart shorts
 */
const int slaveLines = 8;

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
 */
int matrixMaster[] = {
  15,  // Row 0 (Master Pin 15)
  2,   // Row 1 (Master Pin 2)
  4,   // Row 2 (Master Pin 4) - Triple 4 mapping at row 2, col 3
  16,  // Row 3 (Master Pin 16)
  17,  // Row 4 (Master Pin 17) - Triple 13 mapping at row 4, col 3
  5,   // Row 5 (Master Pin 5)
  18,  // Row 6 (Master Pin 18)
  19   // Row 7 (Master Pin 19)
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
 */
int matrixSlave[] = {
  13,  // Col 0 (Slave Pin 13)
  12,  // Col 1 (Slave Pin 12)
  14,  // Col 2 (Slave Pin 14)
  27,  // Col 3 (Slave Pin 27)
  26,  // Col 4 (Slave Pin 26)
  25,  // Col 5 (Slave Pin 25)
  33,  // Col 6 (Slave Pin 33)
  32   // Col 7 (Slave Pin 32)
};

// ============================================================================
// ZONE MAPPING REFERENCE
// ============================================================================
/**
 * ZONE MAPPING MATRIX (for reference/debugging)
 *
 * This shows which dartboard zones are mapped to each (master, slave) pin combination.
 * Generated from database query:
 * SELECT master_pin, slave_pin, zone_number, multiplier_type, base_value
 * FROM dartboard_zone_mappings
 * WHERE dartboard_type_id = (SELECT id FROM dartboard_types WHERE name = 'carromco')
 * ORDER BY master_pin, slave_pin;
 *
 * Row × Col map:
 *        Col0  Col1  Col2  Col3  Col4  Col5  Col6  Col7
 * Row0:   12    25    36    15     5    10    24     0     (Master Pin 15)
 * Row1:    9  25*    27    20    20    20    18     0     (Master Pin 2)   * DOUBLE BULL
 * Row2:   20    20    20   T4*   14   D4*    6     34     (Master Pin 4)   * TRIPLE 4, DOUBLE 4
 * Row3:   14    11     8    16     7    19     3    17     (Master Pin 16)
 * Row4:    3    18    12   T13*   18   D15*   9     6     (Master Pin 17)  * TRIPLE 13, DOUBLE 15
 * Row5:   D14   33    24   D16   21*  D19*   9    51*    (Master Pin 5)
 * Row6:    1    18     4    13     6    10    15     2     (Master Pin 18)
 * Row7:    2    36*    8   26*   12*   20    30*    4     (Master Pin 19)
 *
 * Legend:
 * Tnumber = Triple zone (3x multiplier)
 * Dnumber = Double zone (2x multiplier)
 * 25* = Bull (25 points)
 * Plain number = Single zone (1x multiplier)
 * 0 = Off board
 *
 * NOTE: Invalid zones (outside 1-20 or 25) are not stored in database
 * but shown here for reference with asterisk (*)
 *
 * CRITICAL ZONES FIXED:
 * - Triple 4 (T4) at Master=4, Slave=27
 * - Triple 13 (T13) at Master=17, Slave=27
 * These were broken in the original Arduino code due to array bounds errors.
 */

// ============================================================================
// CALIBRATION NOTES
// ============================================================================
/**
 * If you need to recalibrate this dartboard:
 *
 * 1. Access the admin panel: https://yourserver/admin/dartboard-testing
 * 2. Select "carromco" from the dartboard type dropdown
 * 3. Use "Manual Mapping" tab to:
 *    a. Press dartboard zones and see the master/slave pins
 *    b. Map each zone to its correct multiplier and value
 * 4. Or use "Bulk Import" tab:
 *    a. Download the CSV template
 *    b. Fill in your mappings
 *    c. Upload to apply all at once
 *
 * All mappings are stored in the database and this Arduino code
 * doesn't need to change - just send raw pins to the server!
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

#endif // CARROMCO_CONFIG_H
