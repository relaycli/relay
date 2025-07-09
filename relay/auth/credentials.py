# Copyright (C) 2025, Relay.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

"""Credential encryption utilities using Fernet."""

from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from ..exceptions import StorageError

__all__ = ["CredentialManager"]


class CredentialManager:
    """Manages encryption and decryption of credentials using Fernet."""

    def __init__(self, config_dir: Path) -> None:
        """Initialize the credential manager.

        Args:
            config_dir: Directory to store the encryption key
        """
        self.config_dir = config_dir
        self.key_file = config_dir / "key"
        self._fernet: Fernet | None = None

    def _ensure_key_exists(self) -> None:
        """Ensure encryption key exists, create if missing."""
        if not self.key_file.exists():
            # Generate a new key
            key = Fernet.generate_key()

            # Ensure config directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # Write key with secure permissions
            self.key_file.write_bytes(key)
            self.key_file.chmod(0o600)  # Owner read/write only

    def _get_fernet(self) -> Fernet:
        if self._fernet is None:
            self._ensure_key_exists()
            try:
                key = self.key_file.read_bytes()
                self._fernet = Fernet(key)
            except (OSError, ValueError) as e:
                raise StorageError(f"Failed to load encryption key: {e}")
        return self._fernet

    def encrypt_password(self, password: str) -> bytes:
        """Encrypt a password.

        Args:
            password: Plain text password

        Returns:
            Encrypted password bytes
        """
        try:
            fernet = self._get_fernet()
            return fernet.encrypt(password.encode("utf-8"))
        except (UnicodeEncodeError, ValueError) as e:
            raise StorageError(f"Failed to encrypt password: {e}")

    def decrypt_password(self, encrypted_password: bytes) -> str:
        """Decrypt a password.

        Args:
            encrypted_password: Encrypted password bytes

        Returns:
            Plain text password
        """
        try:
            fernet = self._get_fernet()
            return fernet.decrypt(encrypted_password).decode("utf-8")
        except (InvalidToken, UnicodeDecodeError, ValueError) as e:
            raise StorageError(f"Failed to decrypt password: {e}")

    def is_initialized(self) -> bool:
        """Check if encryption is initialized.

        Returns:
            True if key file exists and is readable
        """
        return self.key_file.exists() and self.key_file.is_file()

    def reset(self) -> None:
        """Reset encryption by removing the key file.

        Warning: This will make all encrypted data unreadable.
        """
        if self.key_file.exists():
            self.key_file.unlink()
        self._fernet = None
