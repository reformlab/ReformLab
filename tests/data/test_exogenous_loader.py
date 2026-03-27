# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for exogenous asset loader — Story 21.6, Task 7."""

from __future__ import annotations

import json

import pytest

from reformlab.data import exogenous_loader as loader_module
from reformlab.data import load_exogenous_asset
from reformlab.data.errors import EvidenceAssetError


class TestLoadExogenousAsset:
    """Test load_exogenous_asset() function."""

    def test_load_exogenous_asset_success(self, tmp_path) -> None:
        """Given valid asset folder, when loading, then returns ExogenousAsset."""
        # Arrange - Patch base path to tmp_path
        original_path = loader_module._EXOGENOUS_ASSETS_BASE_PATH
        loader_module._EXOGENOUS_ASSETS_BASE_PATH = tmp_path

        try:
            asset_folder = tmp_path / "test-energy-price"
            asset_folder.mkdir()

            # Write descriptor.json
            descriptor = {
                "asset_id": "test-energy-price",
                "name": "Test Energy Price",
                "description": "Test energy price asset",
                "data_class": "exogenous",
                "origin": "open-official",
                "access_mode": "bundled",
                "trust_status": "production-safe",
                "source_url": "",
                "license": "",
                "version": "",
                "geographic_coverage": [],
                "years": [],
                "intended_use": "",
                "redistribution_allowed": True,
                "redistribution_notes": "",
                "update_cadence": "",
                "quality_notes": "",
                "references": [],
            }
            with (asset_folder / "descriptor.json").open("w") as f:
                json.dump(descriptor, f)

            # Write values.json
            values = {
                "2020": 0.185,
                "2025": 0.195,
                "2030": 0.205,
            }
            with (asset_folder / "values.json").open("w") as f:
                json.dump(values, f)

            # Write metadata.json
            metadata = {
                "unit": "EUR/kWh",
                "frequency": "annual",
                "source": "Test Source",
                "vintage": "2024-Q2",
                "interpolation_method": "linear",
                "aggregation_method": "mean",
                "revision_policy": "latest",
            }
            with (asset_folder / "metadata.json").open("w") as f:
                json.dump(metadata, f)

            # Act
            asset = load_exogenous_asset("test-energy-price")

            # Assert
            assert asset.name == "test-energy-price"
            assert asset.descriptor.asset_id == "test-energy-price"
            assert asset.descriptor.data_class == "exogenous"
            assert asset.unit == "EUR/kWh"
            assert asset.values[2020] == 0.185
            assert asset.values[2025] == 0.195
            assert asset.values[2030] == 0.205
        finally:
            # Restore original path
            loader_module._EXOGENOUS_ASSETS_BASE_PATH = original_path

    def test_load_raises_for_path_traversal_attack(self, tmp_path) -> None:
        """Should reject path traversal attempts."""
        # Arrange - Patch base path
        original_path = loader_module._EXOGENOUS_ASSETS_BASE_PATH
        loader_module._EXOGENOUS_ASSETS_BASE_PATH = tmp_path

        try:
            # Act & Assert
            with pytest.raises(EvidenceAssetError, match="invalid path characters"):
                load_exogenous_asset("../etc/passwd")

            with pytest.raises(EvidenceAssetError, match="invalid path characters"):
                load_exogenous_asset("etc/hosts")

            with pytest.raises(EvidenceAssetError, match="invalid path characters"):
                load_exogenous_asset("foo\\bar")
        finally:
            loader_module._EXOGENOUS_ASSETS_BASE_PATH = original_path

    def test_load_raises_for_nonexistent_asset(self, tmp_path) -> None:
        """Should raise clear error for missing asset folder."""
        # Arrange - Patch base path
        original_path = loader_module._EXOGENOUS_ASSETS_BASE_PATH
        loader_module._EXOGENOUS_ASSETS_BASE_PATH = tmp_path

        try:
            # Act & Assert
            with pytest.raises(EvidenceAssetError, match="does not exist"):
                load_exogenous_asset("nonexistent_asset")
        finally:
            loader_module._EXOGENOUS_ASSETS_BASE_PATH = original_path

    def test_load_raises_for_missing_descriptor_json(self, tmp_path) -> None:
        """Should raise clear error when descriptor.json is missing."""
        # Arrange - Patch base path and create asset folder without descriptor.json
        original_path = loader_module._EXOGENOUS_ASSETS_BASE_PATH
        loader_module._EXOGENOUS_ASSETS_BASE_PATH = tmp_path

        asset_folder = tmp_path / "test-missing-descriptor"
        asset_folder.mkdir()

        # Create minimal values.json
        with (asset_folder / "values.json").open("w") as f:
            json.dump({"2020": 100.0}, f)

        # Create minimal metadata.json
        with (asset_folder / "metadata.json").open("w") as f:
            json.dump({"unit": "EUR"}, f)

        try:
            # Act & Assert
            with pytest.raises(EvidenceAssetError, match="missing required file.*descriptor"):
                load_exogenous_asset("test-missing-descriptor")
        finally:
            loader_module._EXOGENOUS_ASSETS_BASE_PATH = original_path

    def test_load_raises_for_missing_values_json(self, tmp_path) -> None:
        """Should raise clear error when values.json is missing."""
        # Arrange - Patch base path and create asset folder without values.json
        original_path = loader_module._EXOGENOUS_ASSETS_BASE_PATH
        loader_module._EXOGENOUS_ASSETS_BASE_PATH = tmp_path

        asset_folder = tmp_path / "test-missing-values"
        asset_folder.mkdir()

        # Create minimal descriptor.json
        descriptor = {
            "asset_id": "test-missing-values",
            "name": "Test",
            "description": "Test",
            "data_class": "exogenous",
            "origin": "open-official",
            "access_mode": "bundled",
            "trust_status": "production-safe",
            "source_url": "",
            "license": "",
            "version": "",
            "geographic_coverage": [],
            "years": [],
            "intended_use": "",
            "redistribution_allowed": True,
            "redistribution_notes": "",
            "update_cadence": "",
            "quality_notes": "",
            "references": [],
        }
        with (asset_folder / "descriptor.json").open("w") as f:
            json.dump(descriptor, f)

        # Create minimal metadata.json
        with (asset_folder / "metadata.json").open("w") as f:
            json.dump({"unit": "EUR"}, f)

        try:
            # Act & Assert
            with pytest.raises(EvidenceAssetError, match="missing required file.*values"):
                load_exogenous_asset("test-missing-values")
        finally:
            loader_module._EXOGENOUS_ASSETS_BASE_PATH = original_path

    def test_load_raises_for_missing_metadata_json(self, tmp_path) -> None:
        """Should raise clear error when metadata.json is missing."""
        # Arrange - Patch base path and create asset folder without metadata.json
        original_path = loader_module._EXOGENOUS_ASSETS_BASE_PATH
        loader_module._EXOGENOUS_ASSETS_BASE_PATH = tmp_path

        asset_folder = tmp_path / "test-missing-metadata"
        asset_folder.mkdir()

        # Create minimal descriptor.json
        descriptor = {
            "asset_id": "test-missing-metadata",
            "name": "Test",
            "description": "Test",
            "data_class": "exogenous",
            "origin": "open-official",
            "access_mode": "bundled",
            "trust_status": "production-safe",
            "source_url": "",
            "license": "",
            "version": "",
            "geographic_coverage": [],
            "years": [],
            "intended_use": "",
            "redistribution_allowed": True,
            "redistribution_notes": "",
            "update_cadence": "",
            "quality_notes": "",
            "references": [],
        }
        with (asset_folder / "descriptor.json").open("w") as f:
            json.dump(descriptor, f)

        # Create minimal values.json
        with (asset_folder / "values.json").open("w") as f:
            json.dump({"2020": 100.0}, f)

        try:
            # Act & Assert
            with pytest.raises(EvidenceAssetError, match="missing required file.*metadata"):
                load_exogenous_asset("test-missing-metadata")
        finally:
            loader_module._EXOGENOUS_ASSETS_BASE_PATH = original_path

    def test_load_raises_for_invalid_descriptor_json(self, tmp_path) -> None:
        """Should raise clear error when descriptor.json is invalid JSON."""
        # Arrange - Patch base path and create asset folder with invalid descriptor.json
        original_path = loader_module._EXOGENOUS_ASSETS_BASE_PATH
        loader_module._EXOGENOUS_ASSETS_BASE_PATH = tmp_path

        asset_folder = tmp_path / "test-invalid-descriptor"
        asset_folder.mkdir()

        with (asset_folder / "descriptor.json").open("w") as f:
            f.write("invalid json {")

        try:
            # Act & Assert
            with pytest.raises(EvidenceAssetError, match="Failed to load descriptor.json"):
                load_exogenous_asset("test-invalid-descriptor")
        finally:
            loader_module._EXOGENOUS_ASSETS_BASE_PATH = original_path

    def test_load_raises_for_invalid_values_json(self, tmp_path) -> None:
        """Should raise clear error when values.json has invalid structure."""
        # Arrange - Patch base path and create asset folder with invalid values.json
        original_path = loader_module._EXOGENOUS_ASSETS_BASE_PATH
        loader_module._EXOGENOUS_ASSETS_BASE_PATH = tmp_path

        asset_folder = tmp_path / "test-invalid-values"
        asset_folder.mkdir()

        # Create minimal descriptor.json
        descriptor = {
            "asset_id": "test-invalid-values",
            "name": "Test",
            "description": "Test",
            "data_class": "exogenous",
            "origin": "open-official",
            "access_mode": "bundled",
            "trust_status": "production-safe",
            "source_url": "",
            "license": "",
            "version": "",
            "geographic_coverage": [],
            "years": [],
            "intended_use": "",
            "redistribution_allowed": True,
            "redistribution_notes": "",
            "update_cadence": "",
            "quality_notes": "",
            "references": [],
        }
        with (asset_folder / "descriptor.json").open("w") as f:
            json.dump(descriptor, f)

        # Create invalid values.json (not a dict)
        with (asset_folder / "values.json").open("w") as f:
            f.write("not a dict")

        # Create minimal metadata.json
        with (asset_folder / "metadata.json").open("w") as f:
            json.dump({"unit": "EUR"}, f)

        try:
            # Act & Assert
            with pytest.raises(EvidenceAssetError, match="Failed to load values.json|must be an object"):
                load_exogenous_asset("test-invalid-values")
        finally:
            loader_module._EXOGENOUS_ASSETS_BASE_PATH = original_path

    def test_load_raises_for_invalid_metadata_json(self, tmp_path) -> None:
        """Should raise clear error when metadata.json is invalid JSON."""
        # Arrange - Patch base path and create asset folder with invalid metadata.json
        original_path = loader_module._EXOGENOUS_ASSETS_BASE_PATH
        loader_module._EXOGENOUS_ASSETS_BASE_PATH = tmp_path

        asset_folder = tmp_path / "test-invalid-metadata"
        asset_folder.mkdir()

        # Create minimal descriptor.json
        descriptor = {
            "asset_id": "test-invalid-metadata",
            "name": "Test",
            "description": "Test",
            "data_class": "exogenous",
            "origin": "open-official",
            "access_mode": "bundled",
            "trust_status": "production-safe",
            "source_url": "",
            "license": "",
            "version": "",
            "geographic_coverage": [],
            "years": [],
            "intended_use": "",
            "redistribution_allowed": True,
            "redistribution_notes": "",
            "update_cadence": "",
            "quality_notes": "",
            "references": [],
        }
        with (asset_folder / "descriptor.json").open("w") as f:
            json.dump(descriptor, f)

        # Create minimal values.json
        with (asset_folder / "values.json").open("w") as f:
            json.dump({"2020": 100.0}, f)

        # Create invalid metadata.json
        with (asset_folder / "metadata.json").open("w") as f:
            f.write("invalid json {")

        try:
            # Act & Assert
            with pytest.raises(EvidenceAssetError, match="Failed to load metadata.json"):
                load_exogenous_asset("test-invalid-metadata")
        finally:
            loader_module._EXOGENOUS_ASSETS_BASE_PATH = original_path

    def test_load_raises_for_symlink_attack(self, tmp_path) -> None:
        """Should detect and reject symlink attacks."""
        # Arrange - Create a symlink outside the base path
        original_path = loader_module._EXOGENOUS_ASSETS_BASE_PATH
        loader_module._EXOGENOUS_ASSETS_BASE_PATH = tmp_path

        # Create a directory outside tmp_path
        outside_dir = tmp_path.parent / "outside-assets"
        outside_dir.mkdir()

        try:
            # Create symlink pointing outside
            symlink_path = tmp_path / "malicious-symlink"
            try:
                symlink_path.symlink_to(outside_dir)
            except OSError:
                # Symlink creation may fail on some systems; skip test if so
                pytest.skip("Cannot create symlinks on this system")

            # Act & Assert - Should detect the path is outside base
            with pytest.raises(EvidenceAssetError, match="outside base directory"):
                load_exogenous_asset("malicious-symlink")
        finally:
            loader_module._EXOGENOUS_ASSETS_BASE_PATH = original_path
            # Cleanup
            try:
                outside_dir.rmdir()
            except OSError:
                pass
