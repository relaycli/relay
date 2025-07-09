# Copyright (C) 2025, Relay.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

"""Pytest configuration and fixtures."""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from relay.auth.credentials import CredentialManager
from relay.auth.storage import AccountStorage


@pytest.fixture(scope="function")
def config_dir() -> Generator[Path, None, None]:
    """Creates a temporary directory for config files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="function")
def credential_manager(config_dir: Path) -> CredentialManager:
    """Returns a CredentialManager instance with a temporary config dir."""
    return CredentialManager(config_dir)


@pytest.fixture(scope="function")
def account_storage(config_dir: Path) -> AccountStorage:
    """Returns an AccountStorage instance with a temporary config dir."""
    storage = AccountStorage(config_dir)
    # Ensure credential manager is initialized for tests that need it
    storage.credential_manager._ensure_key_exists()
    return storage
