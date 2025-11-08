"""
Helper script to set up dartboard types and zone mappings
This script initializes the database with dartboard type configurations
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.core.dartboard_service import DartboardService
from src.core.database_service import DatabaseService, get_session, set_database_service


def initialize_db():
    """Initialize the database service"""
    db_service = DatabaseService()
    db_service.initialize_database()
    set_database_service(db_service)
    return db_service


def setup_carromco_board():
    """Set up Carromco Striker dartboard mappings"""
    session = get_session()

    try:
        # Register dartboard type
        print("Registering Carromco board type...")
        try:
            board_type = DartboardService.register_dartboard_type(
                session,
                name="carromco",
                brand="Carromco",
                model="Striker",
                description="Carromco Striker dartboard with 8x8 GPIO matrix",
            )
            print(f"✓ Registered: {board_type}")
        except Exception as e:
            # Board may already exist, try to get it
            if "already exists" in str(e):
                print(f"Board already exists, using existing: {e}")
                board_type = None
                types = DartboardService.list_dartboard_types(session)
                for bt in types:
                    if bt.name == "carromco":
                        board_type = bt
                        break
                if board_type:
                    print(f"✓ Found existing: {board_type}")
                else:
                    raise
            else:
                raise

        # Define all mappings based on the GPIO matrix
        # Format: (master_pin, slave_pin, zone_number, multiplier_type, base_value)
        # Matrix from the Arduino code:
        # matrixMaster[] = {15, 2, 4, 16, 17, 5, 18, 19}
        # matrixSlave[] = {13, 12, 14, 27, 26, 25, 33, 32}

        mappings = [
            # Row 15 (index 0)
            (15, 13, 12, "SINGLE", 12),
            (15, 12, 25, "BULL", 25),
            (15, 14, 36, "SINGLE", 36),  # Invalid zone but keeping for compatibility
            (15, 27, 15, "SINGLE", 15),
            (15, 26, 5, "SINGLE", 5),
            (15, 25, 10, "SINGLE", 10),
            (15, 33, 24, "SINGLE", 24),
            (15, 32, 0, "SINGLE", 0),  # Off board
            # Row 2 (index 1)
            (2, 13, 9, "SINGLE", 9),
            (2, 12, 25, "DOUBLE", 25),  # Adjusted for consistency
            (2, 14, 27, "SINGLE", 27),  # Invalid
            (2, 27, 20, "DOUBLE", 20),
            (2, 26, 20, "SINGLE", 20),
            (2, 25, 20, "DOUBLE", 20),  # Duplicate - take first occurrence
            (2, 33, 18, "SINGLE", 18),
            (2, 32, 0, "SINGLE", 0),
            # Row 4 (index 2) - Critical: Triple 4 location
            (4, 13, 20, "TRIPLE", 20),
            (4, 12, 20, "DOUBLE", 20),
            (4, 14, 20, "SINGLE", 20),
            (4, 27, 4, "TRIPLE", 4),  # Triple 4 - was broken!
            (4, 26, 14, "SINGLE", 14),
            (4, 25, 4, "DOUBLE", 4),
            (4, 33, 6, "SINGLE", 6),
            (4, 32, 34, "SINGLE", 34),  # Invalid
            # Row 16 (index 3)
            (16, 13, 14, "SINGLE", 14),
            (16, 12, 11, "SINGLE", 11),
            (16, 14, 8, "SINGLE", 8),
            (16, 27, 16, "SINGLE", 16),
            (16, 26, 7, "SINGLE", 7),
            (16, 25, 19, "SINGLE", 19),
            (16, 33, 3, "SINGLE", 3),
            (16, 32, 17, "SINGLE", 17),
            # Row 17 (index 4) - Critical: Triple 13 location
            (17, 13, 3, "SINGLE", 3),
            (17, 12, 18, "DOUBLE", 18),
            (17, 14, 12, "SINGLE", 12),
            (17, 27, 13, "TRIPLE", 13),  # Triple 13 - was broken!
            (17, 26, 18, "SINGLE", 18),
            (17, 25, 15, "DOUBLE", 15),
            (17, 33, 9, "DOUBLE", 9),
            (17, 32, 6, "SINGLE", 6),
            # Row 5 (index 5)
            (5, 13, 14, "DOUBLE", 14),
            (5, 12, 33, "SINGLE", 33),  # Invalid
            (5, 14, 24, "SINGLE", 24),
            (5, 27, 16, "DOUBLE", 16),
            (5, 26, 21, "SINGLE", 21),  # Invalid
            (5, 25, 19, "DOUBLE", 19),
            (5, 33, 9, "SINGLE", 9),
            (5, 32, 51, "SINGLE", 51),  # Invalid
            # Row 18 (index 6)
            (18, 13, 1, "SINGLE", 1),
            (18, 12, 18, "SINGLE", 18),
            (18, 14, 4, "SINGLE", 4),
            (18, 27, 13, "SINGLE", 13),
            (18, 26, 6, "SINGLE", 6),
            (18, 25, 10, "SINGLE", 10),
            (18, 33, 15, "SINGLE", 15),
            (18, 32, 2, "SINGLE", 2),
            # Row 19 (index 7)
            (19, 13, 2, "SINGLE", 2),
            (19, 12, 36, "SINGLE", 36),  # Invalid
            (19, 14, 8, "SINGLE", 8),
            (19, 27, 26, "SINGLE", 26),  # Invalid
            (19, 26, 12, "SINGLE", 12),
            (19, 25, 20, "SINGLE", 20),
            (19, 33, 30, "SINGLE", 30),  # Invalid
            (19, 32, 4, "SINGLE", 4),
        ]

        # Filter out invalid zones (>25 or outside 1-20)
        valid_mappings = [
            (m, s, z, mult, b)
            for m, s, z, mult, b in mappings
            if (1 <= b <= 20 or b == 25) and (1 <= z <= 20 or z == 25)
        ]

        print(f"Adding {len(valid_mappings)} valid zone mappings...")
        for master_pin, slave_pin, zone, mult_type, base_val in valid_mappings:
            try:
                DartboardService.add_zone_mapping(
                    session,
                    board_type.id,  # type: ignore
                    master_pin,
                    slave_pin,
                    zone,
                    mult_type,
                    base_val,
                )
                print(
                    f"  ✓ Pins ({master_pin},{slave_pin}) -> Zone {zone} {mult_type} = {base_val}",
                )
            except Exception as e:
                print(f"  ✗ Pins ({master_pin},{slave_pin}): {e}")

        print("\n✓ Carromco board setup complete!")
        return board_type

    except Exception as e:
        print(f"✗ Error: {e}")
        return None
    finally:
        session.close()


def setup_test_board():
    """Set up a minimal test board for development"""
    session = get_session()

    try:
        print("\nRegistering test dartboard type...")
        try:
            board_type = DartboardService.register_dartboard_type(
                session,
                name="test_board",
                brand="Test",
                model="Generic",
                description="Generic test dartboard",
            )
            print(f"✓ Registered: {board_type}")
        except Exception as e:
            # Board may already exist, try to get it
            if "already exists" in str(e):
                print(f"Board already exists, using existing: {e}")
                board_type = None
                types = DartboardService.list_dartboard_types(session)
                for bt in types:
                    if bt.name == "test_board":
                        board_type = bt
                        break
                if board_type:
                    print(f"✓ Found existing: {board_type}")
                else:
                    raise
            else:
                raise

        # Add minimal set of mappings
        test_mappings = [
            (1, 1, 20, "TRIPLE", 20),
            (1, 2, 20, "DOUBLE", 20),
            (1, 3, 20, "SINGLE", 20),
            (2, 1, 4, "TRIPLE", 4),
            (2, 2, 4, "DOUBLE", 4),
            (2, 3, 13, "TRIPLE", 13),
            (3, 1, 25, "BULL", 25),
            (3, 2, 25, "DBLBULL", 25),
        ]

        print(f"Adding {len(test_mappings)} test mappings...")
        for master_pin, slave_pin, zone, mult_type, base_val in test_mappings:
            DartboardService.add_zone_mapping(
                session,
                board_type.id,  # type: ignore
                master_pin,
                slave_pin,
                zone,
                mult_type,
                base_val,
            )
            print(f"  ✓ Pins ({master_pin},{slave_pin}) -> Zone {zone} {mult_type} = {base_val}")

        print("\n✓ Test board setup complete!")
        return board_type

    except Exception as e:
        print(f"✗ Error: {e}")
        return None
    finally:
        session.close()


def setup_crivit_board():
    """Set up Crivit dartboard with 7x12 GPIO matrix - complete matrix"""
    session = get_session()

    try:
        # Register dartboard type
        print("\nRegistering Crivit board type...")
        try:
            board_type = DartboardService.register_dartboard_type(
                session,
                name="crivit",
                brand="Crivit",
                model="Large",
                description="Crivit Large dartboard with 7x12 GPIO matrix",
            )
            print(f"✓ Registered: {board_type}")
        except Exception as e:
            # Board may already exist, try to get it
            if "already exists" in str(e):
                print(f"Board already exists, using existing: {e}")
                board_type = None
                types = DartboardService.list_dartboard_types(session)
                for bt in types:
                    if bt.name == "crivit":
                        board_type = bt
                        break
                if board_type:
                    print(f"✓ Found existing: {board_type}")
                else:
                    raise
            else:
                raise

        # Complete zone mappings for the 7x12 matrix based on original Arduino code
        # Format: (master_pin, slave_pin, zone_number, multiplier_type, base_value)
        # Master pins: 2, 4, 16, 17, 5, 18, 19 (7 rows)
        # Slave pins: 21, 22, 23, 13, 12, 14, 27, 26, 25, 33, 32, 15 (12 columns)

        # Original values matrix and multiplier arrays from Arduino code:
        # values01[7][12] with comments showing slave pins
        # x3[] = triple zones (encoded as master*100 + slave)
        # x2[] = double zones (encoded as master*100 + slave)

        # Mapping helper functions
        def decode_score(raw_value):
            """Decode the raw score value to proper zone and multiplier"""
            # Values like 48, 60, 42, etc. are triples (score = value / 3)
            # Values like 14, 16, 22, etc. could be doubles or singles
            # Need to check against x3 and x2 arrays
            if raw_value == 0:
                return None  # Invalid/unmapped zone
            return raw_value

        # Build complete mappings from the original code
        master_pins = [2, 4, 16, 17, 5, 18, 19]
        slave_pins = [21, 22, 23, 13, 12, 14, 27, 26, 25, 33, 32, 15]

        # Values matrix from original code (7 rows x 12 columns)
        values_matrix = [
            [14, 32, 16, 22, 28, 38, 18, 24, 10, 40, 2, 36],  # Row 0: master pin 2
            [1, 16, 8, 11, 14, 6, 9, 8, 5, 20, 1, 18],  # Row 1: master pin 4
            [19, 48, 24, 33, 42, 34, 12, 26, 15, 60, 3, 4],  # Row 2: master pin 16
            [21, 3, 0, 0, 0, 4, 27, 0, 12, 0, 13, 54],  # Row 3: master pin 17
            [0, 9, 51, 6, 45, 25, 0, 50, 0, 0, 0, 0],  # Row 4: master pin 5
            [0, 0, 0, 0, 0, 0, 0, 0, 30, 18, 13, 0],  # Row 5: master pin 18
            [57, 0, 17, 2, 15, 30, 36, 20, 10, 6, 0, 12],  # Row 6: master pin 19
        ]

        # Triple zones (master*100 + slave)
        x3_zones = {
            1622,
            1623,
            1613,
            1612,
            1625,
            1633,
            1632,
            1721,
            1727,
            1715,
            522,
            523,
            513,
            512,
            1825,
            1833,
            1832,
            1921,
            1927,
            1915,
        }

        # Double zones (master*100 + slave)
        x2_zones = {
            221,
            222,
            223,
            213,
            212,
            214,
            227,
            226,
            225,
            233,
            232,
            215,
            414,
            426,
            1614,
            1626,
            1714,
            1725,
            526,
            1914,
            1926,
        }

        # Bull zones

        all_mappings = []

        for row_idx, master_pin in enumerate(master_pins):
            for col_idx, slave_pin in enumerate(slave_pins):
                raw_value = values_matrix[row_idx][col_idx]

                # Skip invalid zones (0 values)
                if raw_value == 0:
                    continue

                zone_code = master_pin * 100 + slave_pin

                # Determine multiplier type
                if zone_code == 514:  # Bull single
                    mult_type = "BULL"
                    base_value = 25
                    zone_number = 25
                elif zone_code == 526:  # Bull double
                    mult_type = "DBLBULL"
                    base_value = 25
                    zone_number = 25
                elif zone_code in x3_zones:
                    mult_type = "TRIPLE"
                    base_value = raw_value // 3
                    zone_number = base_value
                elif zone_code in x2_zones:
                    mult_type = "DOUBLE"
                    base_value = raw_value // 2
                    zone_number = base_value
                else:
                    mult_type = "SINGLE"
                    base_value = raw_value
                    zone_number = raw_value

                # Validate zone_number and base_value are in valid range
                if not (1 <= base_value <= 20 or base_value == 25):
                    continue
                if not (1 <= zone_number <= 20 or zone_number == 25):
                    continue

                all_mappings.append((master_pin, slave_pin, zone_number, mult_type, base_value))

        print(f"Adding {len(all_mappings)} complete zone mappings from original Arduino code...")
        added_count = 0
        skipped_count = 0

        for master_pin, slave_pin, zone, mult_type, base_val in all_mappings:
            try:
                DartboardService.add_zone_mapping(
                    session,
                    board_type.id,  # type: ignore
                    master_pin,
                    slave_pin,
                    zone,
                    mult_type,
                    base_val,
                )
                added_count += 1
                score = (
                    base_val
                    if mult_type in ["BULL", "SINGLE"]
                    else base_val * (3 if mult_type == "TRIPLE" else 2)
                )
                print(
                    f"  ✓ Pins ({master_pin:2d},{slave_pin:2d}) -> Zone {zone:2d} "
                    f"{mult_type:8s} = {base_val:2d} (score: {score})",
                )
            except Exception as e:
                skipped_count += 1
                print(f"  ⊘ Pins ({master_pin:2d},{slave_pin:2d}): {e}")

        print("\n✓ Crivit board setup complete!")
        print(f"  → Added: {added_count} mappings")
        print(f"  → Skipped: {skipped_count} (duplicates or errors)")
        print(f"  → Matrix coverage: {added_count}/84 possible positions")
        return board_type

    except Exception as e:
        print(f"✗ Error: {e}")
        return None
    finally:
        session.close()


def list_dartboard_types():
    """List all registered dartboard types"""
    session = get_session()

    try:
        types = DartboardService.list_dartboard_types(session)

        if not types:
            print("No dartboard types registered.")
            return

        print(f"\nRegistered Dartboard Types ({len(types)}):")
        print("-" * 80)

        for board_type in types:
            print(f"ID: {board_type.id}")
            print(f"  Name: {board_type.name}")
            print(f"  Brand: {board_type.brand}")
            print(f"  Model: {board_type.model}")
            print(f"  Description: {board_type.description}")
            print(f"  Active: {board_type.is_active}")

            # Get mapping count
            mappings = DartboardService.get_dartboard_type_mappings(
                session,
                board_type.name,
            )
            print(f"  Zone Mappings: {len(mappings) if mappings else 0}")
            print()

    finally:
        session.close()


def main():
    """Main entry point"""
    import argparse

    # Initialize database service first
    initialize_db()

    parser = argparse.ArgumentParser(
        description="Set up dartboard types and zone mappings",
    )
    parser.add_argument(
        "action",
        choices=["setup", "list", "carromco", "crivit", "test"],
        help="Action to perform",
    )

    args = parser.parse_args()

    if args.action == "setup":
        print("Setting up all dartboard types...")
        setup_carromco_board()
        setup_crivit_board()
        setup_test_board()
        list_dartboard_types()
    elif args.action == "carromco":
        setup_carromco_board()
        list_dartboard_types()
    elif args.action == "crivit":
        setup_crivit_board()
        list_dartboard_types()
    elif args.action == "test":
        setup_test_board()
        list_dartboard_types()
    elif args.action == "list":
        list_dartboard_types()


if __name__ == "__main__":
    main()
