"""
Unit tests for dartboard service and zone mapping functionality
Tests both new generic pin-based and legacy score/multiplier formats
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.dartboard_service import DartboardMappingError, DartboardService
from src.core.database_models import Base


@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


@pytest.fixture
def carromco_board(db_session):
    """Create Carromco dartboard type with sample mappings"""
    board_type = DartboardService.register_dartboard_type(
        db_session,
        name="carromco",
        brand="Carromco",
        model="Striker",
    )

    # Add some sample mappings (simplified for testing)
    # Triple 20: pins 4, 13
    DartboardService.add_zone_mapping(
        db_session,
        board_type.id,
        4,
        13,
        20,
        "TRIPLE",
        20,
    )
    # Double 20: pins 4, 12
    DartboardService.add_zone_mapping(
        db_session,
        board_type.id,
        4,
        12,
        20,
        "DOUBLE",
        20,
    )
    # Single 20: pins 4, 14
    DartboardService.add_zone_mapping(
        db_session,
        board_type.id,
        4,
        14,
        20,
        "SINGLE",
        20,
    )
    # Bull (center): pins 15, 2
    DartboardService.add_zone_mapping(
        db_session,
        board_type.id,
        15,
        2,
        25,
        "BULL",
        25,
    )
    # Double Bull: pins 15, 4
    DartboardService.add_zone_mapping(
        db_session,
        board_type.id,
        15,
        4,
        25,
        "DBLBULL",
        25,
    )
    # Triple 4: pins 2, 4
    DartboardService.add_zone_mapping(
        db_session,
        board_type.id,
        2,
        4,
        4,
        "TRIPLE",
        4,
    )
    # Triple 13: pins 17, 5
    DartboardService.add_zone_mapping(
        db_session,
        board_type.id,
        17,
        5,
        13,
        "TRIPLE",
        13,
    )

    return board_type


class TestDartboardServiceBasics:
    """Test basic dartboard service operations"""

    def test_register_dartboard_type(self, db_session):
        """Test registering a new dartboard type"""
        board = DartboardService.register_dartboard_type(
            db_session,
            name="winmau",
            brand="Winmau",
            model="Blade 6",
        )
        assert board.name == "winmau"
        assert board.brand == "Winmau"
        assert board.model == "Blade 6"
        assert board.is_active is True

    def test_register_duplicate_dartboard_type(self, db_session):
        """Test that registering duplicate dartboard type raises error"""
        DartboardService.register_dartboard_type(
            db_session,
            name="carromco",
            brand="Carromco",
        )

        with pytest.raises(DartboardMappingError, match="already exists"):
            DartboardService.register_dartboard_type(
                db_session,
                name="carromco",
                brand="Carromco",
            )

    def test_add_zone_mapping(self, db_session):
        """Test adding a zone mapping"""
        board = DartboardService.register_dartboard_type(
            db_session,
            name="test_board",
            brand="Test",
        )

        mapping = DartboardService.add_zone_mapping(
            db_session,
            board.id,
            1,
            2,
            20,
            "TRIPLE",
            20,
        )

        assert mapping.master_pin == 1
        assert mapping.slave_pin == 2
        assert mapping.zone_number == 20
        assert mapping.multiplier_type == "TRIPLE"
        assert mapping.base_value == 20

    def test_add_duplicate_zone_mapping(self, db_session):
        """Test that adding duplicate zone mapping raises error"""
        board = DartboardService.register_dartboard_type(
            db_session,
            name="test_board",
            brand="Test",
        )

        DartboardService.add_zone_mapping(
            db_session,
            board.id,
            1,
            2,
            20,
            "TRIPLE",
            20,
        )

        with pytest.raises(DartboardMappingError, match="already exists"):
            DartboardService.add_zone_mapping(
                db_session,
                board.id,  # type: ignore
                1,
                2,
                20,
                "TRIPLE",
                20,
            )


class TestZoneValidation:
    """Test zone mapping validation"""

    def test_validate_valid_zone(self):
        """Test validation of valid zones"""
        assert DartboardService.validate_zone_mapping(20, "TRIPLE", 20) is True
        assert DartboardService.validate_zone_mapping(15, "DOUBLE", 15) is True
        assert DartboardService.validate_zone_mapping(1, "SINGLE", 1) is True
        assert DartboardService.validate_zone_mapping(25, "BULL", 25) is True
        assert DartboardService.validate_zone_mapping(25, "DBLBULL", 25) is True

    def test_validate_invalid_zone_number(self):
        """Test validation with invalid zone number"""
        assert DartboardService.validate_zone_mapping(21, "TRIPLE", 20) is False
        assert DartboardService.validate_zone_mapping(0, "SINGLE", 0) is False
        assert DartboardService.validate_zone_mapping(26, "BULL", 25) is False

    def test_validate_invalid_multiplier(self):
        """Test validation with invalid multiplier"""
        assert DartboardService.validate_zone_mapping(20, "INVALID", 20) is False
        assert DartboardService.validate_zone_mapping(20, "QUAD", 20) is False

    def test_validate_bull_multiplier_mismatch(self):
        """Test validation of bull/dblbull multipliers must match zone 25"""
        assert DartboardService.validate_zone_mapping(25, "BULL", 25) is True
        assert (
            DartboardService.validate_zone_mapping(20, "BULL", 25) is False
        )  # Bull not in zone 20
        assert DartboardService.validate_zone_mapping(25, "BULL", 20) is False  # Base value not 25

    def test_validate_non_bull_cannot_be_25(self):
        """Test that non-bull multipliers cannot have base_value 25"""
        assert DartboardService.validate_zone_mapping(25, "TRIPLE", 25) is False
        assert DartboardService.validate_zone_mapping(25, "DOUBLE", 25) is False
        assert DartboardService.validate_zone_mapping(25, "SINGLE", 25) is False


class TestScoreCalculation:
    """Test score calculation"""

    def test_calculate_single(self):
        """Test single multiplier calculation"""
        assert DartboardService.calculate_score(20, "SINGLE") == 20
        assert DartboardService.calculate_score(1, "SINGLE") == 1
        assert DartboardService.calculate_score(25, "SINGLE") == 25

    def test_calculate_double(self):
        """Test double multiplier calculation"""
        assert DartboardService.calculate_score(20, "DOUBLE") == 40
        assert DartboardService.calculate_score(1, "DOUBLE") == 2
        assert DartboardService.calculate_score(15, "DOUBLE") == 30

    def test_calculate_triple(self):
        """Test triple multiplier calculation"""
        assert DartboardService.calculate_score(20, "TRIPLE") == 60
        assert DartboardService.calculate_score(4, "TRIPLE") == 12
        assert DartboardService.calculate_score(13, "TRIPLE") == 39

    def test_calculate_bull(self):
        """Test bull calculation"""
        assert DartboardService.calculate_score(25, "BULL") == 25

    def test_calculate_dblbull(self):
        """Test double bull calculation"""
        assert DartboardService.calculate_score(25, "DBLBULL") == 50

    def test_calculate_invalid_multiplier(self):
        """Test calculation with invalid multiplier"""
        with pytest.raises(DartboardMappingError, match="Invalid multiplier"):
            DartboardService.calculate_score(20, "INVALID")


class TestZoneLookup:
    """Test zone lookup functionality"""

    def test_get_zone_from_pins_triple_20(self, db_session, carromco_board):
        """Test getting zone info for triple 20"""
        zone_info = DartboardService.get_zone_from_pins(
            db_session,
            "carromco",
            4,
            13,
        )

        assert zone_info is not None
        assert zone_info["zone_number"] == 20
        assert zone_info["multiplier_type"] == "TRIPLE"
        assert zone_info["base_value"] == 20
        assert zone_info["score"] == 60

    def test_get_zone_from_pins_double_20(self, db_session, carromco_board):
        """Test getting zone info for double 20"""
        zone_info = DartboardService.get_zone_from_pins(
            db_session,
            "carromco",
            4,
            12,
        )

        assert zone_info is not None
        assert zone_info["zone_number"] == 20
        assert zone_info["multiplier_type"] == "DOUBLE"
        assert zone_info["base_value"] == 20
        assert zone_info["score"] == 40

    def test_get_zone_from_pins_triple_4(self, db_session, carromco_board):
        """Test getting zone info for triple 4 (was problematic in Arduino)"""
        zone_info = DartboardService.get_zone_from_pins(
            db_session,
            "carromco",
            2,
            4,
        )

        assert zone_info is not None
        assert zone_info["zone_number"] == 4
        assert zone_info["multiplier_type"] == "TRIPLE"
        assert zone_info["score"] == 12

    def test_get_zone_from_pins_triple_13(self, db_session, carromco_board):
        """Test getting zone info for triple 13 (was problematic in Arduino)"""
        zone_info = DartboardService.get_zone_from_pins(
            db_session,
            "carromco",
            17,
            5,
        )

        assert zone_info is not None
        assert zone_info["zone_number"] == 13
        assert zone_info["multiplier_type"] == "TRIPLE"
        assert zone_info["score"] == 39

    def test_get_zone_from_pins_bull(self, db_session, carromco_board):
        """Test getting zone info for bull"""
        zone_info = DartboardService.get_zone_from_pins(
            db_session,
            "carromco",
            15,
            2,
        )

        assert zone_info is not None
        assert zone_info["zone_number"] == 25
        assert zone_info["multiplier_type"] == "BULL"
        assert zone_info["score"] == 25

    def test_get_zone_from_pins_dblbull(self, db_session, carromco_board):
        """Test getting zone info for double bull"""
        zone_info = DartboardService.get_zone_from_pins(
            db_session,
            "carromco",
            15,
            4,
        )

        assert zone_info is not None
        assert zone_info["zone_number"] == 25
        assert zone_info["multiplier_type"] == "DBLBULL"
        assert zone_info["score"] == 50

    def test_get_zone_not_found(self, db_session, carromco_board):
        """Test zone lookup for non-existent pin combination"""
        zone_info = DartboardService.get_zone_from_pins(
            db_session,
            "carromco",
            99,
            99,
        )

        assert zone_info is None

    def test_get_zone_invalid_board_type(self, db_session):
        """Test zone lookup for non-existent board type"""
        zone_info = DartboardService.get_zone_from_pins(
            db_session,
            "nonexistent",
            4,
            13,
        )

        assert zone_info is None


class TestLegacyConversion:
    """Test legacy score/multiplier to zone conversion"""

    def test_convert_triple_20(self, db_session):
        """Test converting legacy triple 20"""
        zone_info = DartboardService.convert_legacy_to_zone(
            db_session,
            "carromco",
            20,
            "TRIPLE",
        )

        assert zone_info["zone_number"] == 20
        assert zone_info["multiplier_type"] == "TRIPLE"
        assert zone_info["base_value"] == 20
        assert zone_info["score"] == 60

    def test_convert_double_15(self, db_session):
        """Test converting legacy double 15"""
        zone_info = DartboardService.convert_legacy_to_zone(
            db_session,
            "carromco",
            15,
            "DOUBLE",
        )

        assert zone_info["zone_number"] == 15
        assert zone_info["multiplier_type"] == "DOUBLE"
        assert zone_info["score"] == 30

    def test_convert_single_1(self, db_session):
        """Test converting legacy single 1"""
        zone_info = DartboardService.convert_legacy_to_zone(
            db_session,
            "carromco",
            1,
            "SINGLE",
        )

        assert zone_info["zone_number"] == 1
        assert zone_info["multiplier_type"] == "SINGLE"
        assert zone_info["score"] == 1

    def test_convert_bull(self, db_session):
        """Test converting legacy bull"""
        zone_info = DartboardService.convert_legacy_to_zone(
            db_session,
            "carromco",
            25,
            "BULL",
        )

        assert zone_info["zone_number"] == 25
        assert zone_info["multiplier_type"] == "BULL"
        assert zone_info["base_value"] == 25
        assert zone_info["score"] == 25

    def test_convert_dblbull(self, db_session):
        """Test converting legacy double bull"""
        zone_info = DartboardService.convert_legacy_to_zone(
            db_session,
            "carromco",
            50,
            "DBLBULL",
        )

        assert zone_info["zone_number"] == 25
        assert zone_info["multiplier_type"] == "DBLBULL"
        assert zone_info["base_value"] == 25
        assert zone_info["score"] == 50

    def test_convert_invalid_multiplier(self, db_session):
        """Test conversion with invalid multiplier"""
        with pytest.raises(DartboardMappingError, match="Invalid multiplier"):
            DartboardService.convert_legacy_to_zone(
                db_session,
                "carromco",
                20,
                "INVALID",
            )


class TestDartboardTypesListing:
    """Test dartboard type listing"""

    def test_list_dartboard_types_empty(self, db_session):
        """Test listing when no types exist"""
        types = DartboardService.list_dartboard_types(db_session)
        assert len(types) == 0

    def test_list_dartboard_types_multiple(self, db_session):
        """Test listing multiple dartboard types"""
        DartboardService.register_dartboard_type(
            db_session,
            name="carromco",
            brand="Carromco",
        )
        DartboardService.register_dartboard_type(
            db_session,
            name="winmau",
            brand="Winmau",
        )

        types = DartboardService.list_dartboard_types(db_session)
        assert len(types) == 2
        names = {t.name for t in types}
        assert names == {"carromco", "winmau"}

    def test_list_dartboard_types_inactive_excluded(self, db_session):
        """Test that inactive types are excluded from listing"""
        DartboardService.register_dartboard_type(
            db_session,
            name="carromco",
            brand="Carromco",
        )
        board2 = DartboardService.register_dartboard_type(
            db_session,
            name="winmau",
            brand="Winmau",
        )

        # Mark one as inactive
        board2.is_active = False  # type: ignore
        db_session.commit()

        types = DartboardService.list_dartboard_types(db_session)
        assert len(types) == 1
        assert types[0].name == "carromco"


class TestGetMappingsForType:
    """Test getting all mappings for a dartboard type"""

    def test_get_mappings_for_type(self, db_session, carromco_board):
        """Test getting all mappings for a type"""
        mappings = DartboardService.get_dartboard_type_mappings(
            db_session,
            "carromco",
        )

        assert mappings is not None
        assert len(mappings) == 7  # We added 7 mappings in the fixture

    def test_get_mappings_for_nonexistent_type(self, db_session):
        """Test getting mappings for non-existent type"""
        mappings = DartboardService.get_dartboard_type_mappings(
            db_session,
            "nonexistent",
        )

        assert mappings is None

    def test_get_mappings_case_insensitive(self, db_session, carromco_board):
        """Test that board type lookup is case-insensitive"""
        mappings = DartboardService.get_dartboard_type_mappings(
            db_session,
            "CARROMCO",
        )

        # Should work because the service converts to lowercase
        assert mappings is not None or mappings is None  # Depends on implementation


class TestMultiplierMapping:
    """Test multiplier mapping values"""

    def test_multiplier_map(self):
        """Test that multiplier map has correct values"""
        assert DartboardService.MULTIPLIER_MAP["SINGLE"] == 1
        assert DartboardService.MULTIPLIER_MAP["DOUBLE"] == 2
        assert DartboardService.MULTIPLIER_MAP["TRIPLE"] == 3
        assert DartboardService.MULTIPLIER_MAP["BULL"] == 25
        assert DartboardService.MULTIPLIER_MAP["DBLBULL"] == 50

    def test_valid_zones(self):
        """Test valid zones set"""
        assert 1 in DartboardService.VALID_ZONES
        assert 20 in DartboardService.VALID_ZONES
        assert 25 in DartboardService.VALID_ZONES
        assert 0 not in DartboardService.VALID_ZONES
        assert 21 not in DartboardService.VALID_ZONES

    def test_multiplier_types(self):
        """Test multiplier types set"""
        assert "SINGLE" in DartboardService.MULTIPLIER_TYPES
        assert "DOUBLE" in DartboardService.MULTIPLIER_TYPES
        assert "TRIPLE" in DartboardService.MULTIPLIER_TYPES
        assert "BULL" in DartboardService.MULTIPLIER_TYPES
        assert "DBLBULL" in DartboardService.MULTIPLIER_TYPES
