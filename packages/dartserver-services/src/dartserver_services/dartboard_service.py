"""
Dartboard service for mapping GPIO pin combinations to game zones
Handles both generic pin-based input and legacy score/multiplier input
"""

from typing import Any, ClassVar, cast

from dartserver_core import DartboardType, DartboardZoneMapping
from sqlalchemy.orm import Session


class DartboardMappingError(Exception):
    """Raised when dartboard mapping fails"""


class DartboardService:
    """Service for dartboard zone mapping and validation"""

    MULTIPLIER_MAP: ClassVar[dict[str, int]] = {
        "SINGLE": 1,
        "DOUBLE": 2,
        "TRIPLE": 3,
        "BULL": 25,
        "DBLBULL": 50,
    }

    VALID_ZONES: ClassVar = set(range(1, 21)) | {25}  # 1-20 and 25 (bull)
    MULTIPLIER_TYPES: ClassVar = {"SINGLE", "DOUBLE", "TRIPLE", "BULL", "DBLBULL"}

    @staticmethod
    def register_dartboard_type(
        session: Session,
        name: str,
        brand: str,
        model: str | None = None,
        description: str | None = None,
    ) -> DartboardType:
        """
        Register a new dartboard type

        Args:
            session: Database session
            name: Unique dartboard type name (e.g., 'carromco')
            brand: Brand name (e.g., 'Carromco')
            model: Model name (optional)
            description: Description (optional)

        Returns:
            DartboardType instance
        """
        existing = session.query(DartboardType).filter_by(name=name).first()
        if existing:
            raise DartboardMappingError(f"Dartboard type '{name}' already exists")

        dartboard_type = DartboardType(
            name=name,
            brand=brand,
            model=model,
            description=description,
        )
        session.add(dartboard_type)
        session.commit()
        return dartboard_type

    @staticmethod
    def add_zone_mapping(
        session: Session,
        dartboard_type_id: int,
        master_pin: int,
        slave_pin: int,
        zone_number: int,
        multiplier_type: str,
        base_value: int,
    ) -> DartboardZoneMapping:
        """
        Add a zone mapping for a dartboard type

        Args:
            session: Database session
            dartboard_type_id: Dartboard type ID
            master_pin: Master (row) GPIO pin
            slave_pin: Slave (column) GPIO pin
            zone_number: Zone number (1-20 or 25)
            multiplier_type: Multiplier type (SINGLE, DOUBLE, TRIPLE, BULL, DBLBULL)
            base_value: Base score value (1-20 or 25)

        Returns:
            DartboardZoneMapping instance
        """
        if not DartboardService.validate_zone_mapping(zone_number, multiplier_type, base_value):
            raise DartboardMappingError(
                f"Invalid zone mapping: zone={zone_number}, mult={multiplier_type}, "
                f"value={base_value}",
            )

        # Check if mapping already exists
        existing = (
            session.query(DartboardZoneMapping)
            .filter_by(
                dartboard_type_id=dartboard_type_id,
                master_pin=master_pin,
                slave_pin=slave_pin,
            )
            .first()
        )
        if existing:
            raise DartboardMappingError(
                f"Mapping for pins ({master_pin}, {slave_pin}) already exists for dartboard "
                f"type {dartboard_type_id}",
            )

        mapping = DartboardZoneMapping(
            dartboard_type_id=dartboard_type_id,
            master_pin=master_pin,
            slave_pin=slave_pin,
            zone_number=zone_number,
            multiplier_type=multiplier_type,
            base_value=base_value,
        )
        session.add(mapping)
        session.commit()
        return mapping

    @staticmethod
    def get_zone_from_pins(
        session: Session,
        dartboard_type_name: str,
        master_pin: int,
        slave_pin: int,
    ) -> dict | None:
        """
        Get zone information from pin combination

        Args:
            session: Database session
            dartboard_type_name: Dartboard type name (e.g., 'carromco')
            master_pin: Master GPIO pin
            slave_pin: Slave GPIO pin

        Returns:
            Dictionary with zone info or None if not found
        """
        dartboard_type = session.query(DartboardType).filter_by(name=dartboard_type_name).first()
        if not dartboard_type:
            return None

        mapping = (
            session.query(DartboardZoneMapping)
            .filter_by(
                dartboard_type_id=dartboard_type.id,
                master_pin=master_pin,
                slave_pin=slave_pin,
            )
            .first()
        )
        if not mapping:
            return None

        return {
            "zone_number": mapping.zone_number,
            "multiplier_type": mapping.multiplier_type,
            "base_value": mapping.base_value,
            "score": DartboardService.calculate_score(mapping.base_value, mapping.multiplier_type),
        }

    @staticmethod
    def calculate_score(base_value: int, multiplier_type: str) -> int:
        """
        Calculate final score from base value and multiplier

        Args:
            base_value: Base score (1-20 or 25)
            multiplier_type: Multiplier type

        Returns:
            Final score
        """
        if multiplier_type not in DartboardService.MULTIPLIER_MAP:
            raise DartboardMappingError(f"Invalid multiplier type: {multiplier_type}")

        # For BULL and DBLBULL, the value is absolute, not a multiplier
        if multiplier_type == "BULL":
            return 25
        if multiplier_type == "DBLBULL":
            return 50
        return int(base_value * DartboardService.MULTIPLIER_MAP[multiplier_type])

    @staticmethod
    def validate_zone_mapping(
        zone_number: int,
        multiplier_type: str,
        base_value: int,
    ) -> bool:
        """
        Validate a zone mapping

        Args:
            zone_number: Zone number (1-20 or 25)
            multiplier_type: Multiplier type
            base_value: Base value

        Returns:
            True if valid, False otherwise
        """
        if zone_number not in DartboardService.VALID_ZONES:
            return False
        if multiplier_type not in DartboardService.MULTIPLIER_TYPES:
            return False
        if base_value not in DartboardService.VALID_ZONES:
            return False

        # Special case: BULL and DBLBULL only for zone 25
        if multiplier_type in {"BULL", "DBLBULL"} and zone_number != 25:
            return False

        # BULL/DBLBULL only for base_value 25
        if multiplier_type in {"BULL", "DBLBULL"} and base_value != 25:
            return False

        # Non-bull multipliers shouldn't have base_value 25
        return not (multiplier_type not in {"BULL", "DBLBULL"} and base_value == 25)

    @staticmethod
    def convert_legacy_to_zone(
        _session: Session,
        _dartboard_type_name: str,
        score: int,
        multiplier: str,
    ) -> dict:
        """
        Convert legacy (score, multiplier) to zone information

        Args:
            _session: Database session (reserved for future use)
            _dartboard_type_name: Dartboard type name (reserved for future use)
            score: Base score value
            multiplier: Multiplier type

        Returns:
            Zone information dictionary
        """
        if multiplier not in DartboardService.MULTIPLIER_MAP:
            raise DartboardMappingError(f"Invalid multiplier: {multiplier}")

        # For bulls, the score is already the final value (25 or 50)
        if multiplier in {"BULL", "DBLBULL"}:
            base_value = 25
            zone_number = 25
        else:
            base_value = score
            zone_number = score

        final_score = DartboardService.calculate_score(base_value, multiplier)

        return {
            "zone_number": zone_number,
            "multiplier_type": multiplier,
            "base_value": base_value,
            "score": final_score,
        }

    @staticmethod
    def list_dartboard_types(session: Session) -> list[Any]:
        """Get all active dartboard types"""
        return cast(list[Any], session.query(DartboardType).filter_by(is_active=True).all())

    @staticmethod
    def get_dartboard_type_mappings(
        session: Session,
        dartboard_type_name: str,
    ) -> list[Any] | None:
        """Get all zone mappings for a dartboard type"""
        dartboard_type = session.query(DartboardType).filter_by(name=dartboard_type_name).first()
        if not dartboard_type:
            return None
        return (
            session.query(DartboardZoneMapping).filter_by(dartboard_type_id=dartboard_type.id).all()
        )

    @staticmethod
    def get_matrix_visualization(
        session: Session,
        dartboard_type_name: str,
    ) -> tuple[dict, list, list, list] | None:
        """
        Get matrix visualization data for a dartboard type

        Args:
            session: Database session
            dartboard_type_name: Dartboard type name

        Returns:
            Tuple of (dartboard_type_dict, all_master_pins, all_slave_pins, matrix_data)
        """
        dartboard_type = session.query(DartboardType).filter_by(name=dartboard_type_name).first()
        if not dartboard_type:
            return None

        mappings = (
            session.query(DartboardZoneMapping).filter_by(dartboard_type_id=dartboard_type.id).all()
        )

        # Get unique master and slave pins, sorted
        master_pins = sorted({m.master_pin for m in mappings})
        slave_pins = sorted({m.slave_pin for m in mappings})

        # Create a lookup dictionary for faster access
        mapping_dict = {
            (m.master_pin, m.slave_pin): {
                "zone_number": m.zone_number,
                "multiplier_type": m.multiplier_type,
                "base_value": m.base_value,
                "id": m.id,
            }
            for m in mappings
        }

        # Build matrix: rows are master_pins, columns are slave_pins
        matrix = []
        for master_pin in master_pins:
            row = []
            for slave_pin in slave_pins:
                cell_data = mapping_dict.get((master_pin, slave_pin))
                row.append(
                    {
                        "master_pin": master_pin,
                        "slave_pin": slave_pin,
                        "mapping": cell_data,
                    },
                )
            matrix.append(
                {
                    "master_pin": master_pin,
                    "cells": row,
                },
            )

        dartboard_type_dict = {
            "id": dartboard_type.id,
            "name": dartboard_type.name,
            "brand": dartboard_type.brand,
            "model": dartboard_type.model,
            "description": dartboard_type.description,
        }

        return dartboard_type_dict, master_pins, slave_pins, matrix

    @staticmethod
    def update_zone_mapping(
        session: Session,
        dartboard_type_name: str,
        master_pin: int,
        slave_pin: int,
        zone_number: int,
        multiplier_type: str,
        base_value: int,
    ) -> DartboardZoneMapping:
        """
        Update an existing zone mapping or create a new one

        Args:
            session: Database session
            dartboard_type_name: Dartboard type name
            master_pin: Master (row) GPIO pin
            slave_pin: Slave (column) GPIO pin
            zone_number: Zone number (1-20 or 25)
            multiplier_type: Multiplier type (SINGLE, DOUBLE, TRIPLE, BULL, DBLBULL)
            base_value: Base score value (1-20 or 25)

        Returns:
            DartboardZoneMapping instance
        """
        if not DartboardService.validate_zone_mapping(zone_number, multiplier_type, base_value):
            raise DartboardMappingError(
                f"Invalid zone mapping: zone={zone_number}, mult={multiplier_type}, "
                f"value={base_value}",
            )

        dartboard_type = session.query(DartboardType).filter_by(name=dartboard_type_name).first()
        if not dartboard_type:
            raise DartboardMappingError(f"Dartboard type '{dartboard_type_name}' not found")

        dartboard_type_id: int = dartboard_type.id

        # Check if mapping already exists
        existing = (
            session.query(DartboardZoneMapping)
            .filter_by(
                dartboard_type_id=dartboard_type_id,
                master_pin=master_pin,
                slave_pin=slave_pin,
            )
            .first()
        )

        if existing:
            # Update existing mapping
            existing.zone_number = zone_number  # type: ignore
            existing.multiplier_type = multiplier_type  # type: ignore
            existing.base_value = base_value  # type: ignore
            session.commit()
            return existing
        # Create new mapping
        return DartboardService.add_zone_mapping(
            session,
            dartboard_type.id,
            master_pin,
            slave_pin,
            zone_number,
            multiplier_type,
            base_value,
        )

    @staticmethod
    def bulk_import_mappings(
        session: Session,
        dartboard_type_name: str,
        mappings_data: list,
    ) -> tuple[int, int]:
        """
        Bulk import zone mappings from CSV data

        Args:
            session: Database session
            dartboard_type_name: Dartboard type name
            mappings_data: List of dicts with keys: master_pin, slave_pin, zone_number,
                multiplier_type, base_value

        Returns:
            Tuple of (created_count, updated_count)
        """
        dartboard_type = session.query(DartboardType).filter_by(name=dartboard_type_name).first()
        if not dartboard_type:
            raise DartboardMappingError(f"Dartboard type '{dartboard_type_name}' not found")

        created_count = 0
        updated_count = 0

        for mapping_data in mappings_data:
            try:
                result = DartboardService.update_zone_mapping(
                    session,
                    dartboard_type_name,
                    int(mapping_data["master_pin"]),
                    int(mapping_data["slave_pin"]),
                    int(mapping_data["zone_number"]),
                    str(mapping_data["multiplier_type"]).upper(),
                    int(mapping_data["base_value"]),
                )

                # Check if it was created or updated
                if result.id:  # If has ID, it was created/updated successfully
                    if session.query(DartboardZoneMapping).filter_by(id=result.id).count() > 0:
                        updated_count += 1
                    else:
                        created_count += 1
            except Exception as e:
                raise DartboardMappingError(
                    f"Error importing mapping {mapping_data}: {e!s}",
                ) from e

        return created_count, updated_count
