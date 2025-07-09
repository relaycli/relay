# Copyright (C) 2025, Relay.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

"""Local storage management for account data."""

import base64
import json
from pathlib import Path

from ..exceptions import AccountExistsError, AccountNotFoundError, StorageError
from ..models.account import Account, AccountCreate, AccountInfo
from .credentials import CredentialManager

__all__ = ["AccountStorage"]


class AccountStorage:
    """Manages local storage of account data."""

    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize the account storage.

        Args:
            config_dir: Directory to store account data (defaults to ~/.relay)

        """
        if config_dir is None:
            config_dir = Path.home() / ".relay"

        self.config_dir = config_dir
        self.accounts_file = config_dir / "accounts.json"
        self.credential_manager = CredentialManager(config_dir)

    def _ensure_config_dir(self) -> None:
        """Ensure configuration directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _load_accounts_data(self) -> dict[str, dict]:
        """Load accounts data from file.

        Returns:
            Dictionary of account data

        Raises:
            StorageError: If failed to load accounts data
        """
        if not self.accounts_file.exists():
            return {}

        try:
            with self.accounts_file.open("r") as f:
                data = json.load(f)

            # Decode base64 encrypted passwords
            for account_data in data.values():
                if "encrypted_password" in account_data:
                    account_data["encrypted_password"] = base64.b64decode(account_data["encrypted_password"])

        except (OSError, json.JSONDecodeError, ValueError) as e:
            raise StorageError(f"Failed to load accounts data: {e}")
        else:
            return data

    def _save_accounts_data(self, data: dict[str, dict]) -> None:
        """Save accounts data to file.

        Args:
            data: Dictionary of account data

        Raises:
            StorageError: If failed to save accounts data
        """
        try:
            self._ensure_config_dir()

            # Encode encrypted passwords as base64 for JSON serialization
            json_data = {}
            for name, account_data in data.items():
                json_data[name] = account_data.copy()
                if "encrypted_password" in json_data[name]:
                    json_data[name]["encrypted_password"] = base64.b64encode(
                        json_data[name]["encrypted_password"]
                    ).decode("utf-8")

            with self.accounts_file.open("w") as f:
                json.dump(json_data, f, indent=2)

            # Secure permissions
            self.accounts_file.chmod(0o600)

        except (OSError, ValueError) as e:
            raise StorageError(f"Failed to save accounts data: {e}")

    def add_account(self, account_data: AccountCreate) -> Account:
        """Add a new account.

        Args:
            account_data: Account creation data

        Returns:
            Created account

        Raises:
            AccountExistsError: If account name already exists
        """
        accounts = self._load_accounts_data()

        if account_data.name in accounts:
            raise AccountExistsError(f"Account '{account_data.name}' already exists")

        # Encrypt password
        encrypted_password = self.credential_manager.encrypt_password(account_data.password)

        # Create account
        account = Account(
            name=account_data.name,
            email=account_data.email,
            provider=account_data.provider,
            imap_server=account_data.imap_server,
            imap_port=account_data.imap_port,
            encrypted_password=encrypted_password,
        )

        # Save to storage
        accounts[account.name] = account.model_dump()
        self._save_accounts_data(accounts)

        return account

    def get_account(self, name: str) -> Account:
        """Get an account by name.

        Args:
            name: Account name

        Returns:
            Account data

        Raises:
            AccountNotFoundError: If account doesn't exist
        """
        accounts = self._load_accounts_data()

        if name not in accounts:
            raise AccountNotFoundError(f"Account '{name}' not found")

        return Account.model_validate(accounts[name])

    def list_accounts(self) -> list[AccountInfo]:
        """List all accounts without sensitive data.

        Returns:
            List of account information

        """
        accounts = self._load_accounts_data()

        result = []
        for account_data in accounts.values():
            # Remove sensitive data
            safe_data = {k: v for k, v in account_data.items() if k != "encrypted_password"}
            result.append(AccountInfo.model_validate(safe_data))

        return result

    def remove_account(self, name: str) -> None:
        """Remove an account.

        Args:
            name: Account name

        Raises:
            AccountNotFoundError: If account doesn't exist
        """
        accounts = self._load_accounts_data()

        if name not in accounts:
            raise AccountNotFoundError(f"Account '{name}' not found")

        del accounts[name]
        self._save_accounts_data(accounts)

    def account_exists(self, name: str) -> bool:
        """Check if an account exists.

        Args:
            name: Account name

        Returns:
            True if account exists
        """
        accounts = self._load_accounts_data()
        return name in accounts

    def get_account_password(self, name: str) -> str:
        """Get decrypted password for an account.

        Args:
            name: Account name

        Returns:
            Decrypted password
        """
        account = self.get_account(name)
        return self.credential_manager.decrypt_password(account.encrypted_password)

    def reset_storage(self) -> None:
        """Reset all storage data.

        Warning: This will remove all accounts and encryption keys.
        """
        if self.accounts_file.exists():
            self.accounts_file.unlink()
        self.credential_manager.reset()
