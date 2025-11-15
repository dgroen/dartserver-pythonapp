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
    """Set up Crivit dartboard with 7x12 GPIO matrix"""
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

        # Define sample zone mappings for the 7x12 matrix
        # Format: (master_pin, slave_pin, zone_number, multiplier_type, base_value)
        # Master pins: 2, 4, 16, 17, 5, 18, 19 (7 rows)
        # Slave pins: 21, 22, 23, 13, 12, 14, 27, 26, 25, 33, 32, 15 (12 columns)
        # This provides a template for basic zone detection

        sample_mappings = [
            # Row 2 - Sample zones
            (2, 21, 20, "SINGLE", 20),
            (2, 22, 20, "DOUBLE", 20),
            (2, 23, 20, "TRIPLE", 20),
            # Row 4 - Sample zones
            (4, 21, 4, "SINGLE", 4),
            (4, 22, 4, "DOUBLE", 4),
            (4, 23, 4, "TRIPLE", 4),
            # Row 17 - Sample zones
            (17, 21, 13, "SINGLE", 13),
            (17, 22, 13, "DOUBLE", 13),
            (17, 23, 13, "TRIPLE", 13),
            # Bull zone (typically in the middle)
            (5, 15, 25, "BULL", 25),
            (5, 33, 25, "DBLBULL", 25),
        ]

        print(f"Adding {len(sample_mappings)} sample zone mappings...")
        for master_pin, slave_pin, zone, mult_type, base_val in sample_mappings:
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

        print("\n✓ Crivit board setup complete!")
        print("  → Use admin panel to configure remaining zones")
        print("  → Navigate to: https://yourserver/admin/dartboard-testing")
        print("  → Select 'crivit' from dartboard type dropdown")
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
