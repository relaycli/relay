# Copyright (C) 2025, Relay.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

"""Tests for credential management."""

import pytest

from relay.auth.credentials import CredentialManager
from relay.exceptions import StorageError


def test_credential_manager_init(credential_manager: CredentialManager):
    """Test that the key file is created on initialization."""
    assert not credential_manager.key_file.exists()
    credential_manager._ensure_key_exists()
    assert credential_manager.key_file.exists()
    assert credential_manager.key_file.stat().st_mode & 0o777 == 0o600


def test_password_encryption_decryption(credential_manager: CredentialManager):
    """Test that a password can be encrypted and decrypted correctly."""
    password = "my-secret-password"
    encrypted_password = credential_manager.encrypt_password(password)
    assert isinstance(encrypted_password, bytes)
    decrypted_password = credential_manager.decrypt_password(encrypted_password)
    assert decrypted_password == password


def test_decrypt_invalid_token_raises_error(credential_manager: CredentialManager):
    """Test that decrypting an invalid token raises a StorageError."""
    with pytest.raises(StorageError):
        credential_manager.decrypt_password(b"invalid-token")


def test_is_initialized(credential_manager: CredentialManager):
    """Test the is_initialized method."""
    assert not credential_manager.is_initialized()
    credential_manager._ensure_key_exists()
    assert credential_manager.is_initialized()


def test_reset(credential_manager: CredentialManager):
    """Test that reset removes the key file."""
    credential_manager._ensure_key_exists()
    assert credential_manager.key_file.exists()
    credential_manager.reset()
    assert not credential_manager.key_file.exists()
