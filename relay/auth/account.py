# Copyright (C) 2025, Relay.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

"""Account management operations."""

from pathlib import Path

from ..models.account import Account, AccountCreate, AccountInfo
from ..providers.imap import IMAPClient
from .storage import AccountStorage

__all__ = ["AccountManager"]


class AccountManager:
    """High-level account management operations."""

    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize the account manager.

        Args:
            config_dir: Directory to store account data (defaults to ~/.relay)
        """
        self.storage = AccountStorage(config_dir)

    def add_account(self, account_data: AccountCreate) -> Account:
        """Add a new account with connection testing.

        Args:
            account_data: Account creation data

        Returns:
            Created account
        """
        # Validate account data using Pydantic v2
        account_data = AccountCreate.model_validate(account_data.model_dump())

        # Test connection before saving
        test_connection(
            account_data.email,
            account_data.password,
            account_data.imap_server,
            account_data.imap_port,
            account_data.provider,
        )

        # Add to storage
        return self.storage.add_account(account_data)

    def remove_account(self, name: str) -> None:
        """Remove an account.

        Args:
            name: Account name
        """
        self.storage.remove_account(name)

    def list_accounts(self) -> list[AccountInfo]:
        """List all accounts without sensitive data.

        Returns:
            List of account information
        """
        return self.storage.list_accounts()

    def get_account(self, name: str) -> Account:
        """Get an account by name.

        Args:
            name: Account name

        Returns:
            Account data
        """
        return self.storage.get_account(name)

    def test_account(self, name: str) -> bool:
        """Test connection to an existing account.

        Args:
            name: Account name

        Returns:
            True if connection successful
        """
        account = self.storage.get_account(name)
        password = self.storage.get_account_password(name)

        return test_connection(account.email, password, account.imap_server, account.imap_port, account.provider)

    def account_exists(self, name: str) -> bool:
        """Check if an account exists.

        Args:
            name: Account name

        Returns:
            True if account exists
        """
        return self.storage.account_exists(name)

    def get_imap_client(self, name: str) -> IMAPClient:
        """Get an IMAP client for an account.

        Args:
            name: Account name

        Returns:
            Configured IMAP client
        """
        account = self.storage.get_account(name)
        password = self.storage.get_account_password(name)

        return IMAPClient(
            imap_server=account.imap_server,
            email_address=account.email,
            password=password,
            imap_port=account.imap_port,
            provider=account.provider,
        )


def test_connection(email: str, password: str, imap_server: str, imap_port: int, provider: str | None = None) -> bool:
    """Test IMAP connection with given credentials.

    Args:
        email: Email address
        password: Password
        imap_server: IMAP server address
        imap_port: IMAP port
        provider: Email provider

    Returns:
        True if connection successful
    """
    client = IMAPClient(
        imap_server=imap_server, email_address=email, password=password, imap_port=imap_port, provider=provider
    )
    client.logout()
    return True
