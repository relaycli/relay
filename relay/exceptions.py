# Copyright (C) 2025, Relay.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

"""Custom exceptions for the Relay library."""

__all__ = [
    "AccountExistsError",
    "AccountNotFoundError",
    "AuthenticationError",
    "RelayError",
    "ServerConnectionError",
    "StorageError",
    "ValidationError",
]


class RelayError(Exception):
    """Base exception for all Relay errors."""


class AuthenticationError(RelayError):
    """Raised when authentication fails."""


class ServerConnectionError(RelayError):
    """Raised when connection to email server fails."""


class ValidationError(RelayError):
    """Raised when data validation fails."""


class AccountNotFoundError(RelayError):
    """Raised when account is not found."""


class AccountExistsError(RelayError):
    """Raised when trying to create an account that already exists."""


class StorageError(RelayError):
    """Raised when storage operations fail."""
