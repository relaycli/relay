# Copyright (C) 2025, Relay.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

"""Tests for account storage."""

import pytest

from relay.auth.storage import AccountStorage
from relay.exceptions import AccountExistsError, AccountNotFoundError
from relay.models.account import AccountCreate, EmailProvider

# Sample account data for testing
SAMPLE_ACCOUNT = AccountCreate(
    name="test_account",
    email="test@example.com",
    password="supersecret",  # noqa: S106
    provider=EmailProvider.CUSTOM,
    imap_server="imap.example.com",
)


def test_add_account(account_storage: AccountStorage):
    """Test adding a new account."""
    account = account_storage.add_account(SAMPLE_ACCOUNT)
    assert account.name == SAMPLE_ACCOUNT.name
    assert account_storage.account_exists(SAMPLE_ACCOUNT.name)

    # Verify data is stored
    stored_account = account_storage.get_account(SAMPLE_ACCOUNT.name)
    assert stored_account.email == SAMPLE_ACCOUNT.email


def test_add_existing_account_raises_error(account_storage: AccountStorage):
    """Test that adding an existing account raises AccountExistsError."""
    account_storage.add_account(SAMPLE_ACCOUNT)
    with pytest.raises(AccountExistsError):
        account_storage.add_account(SAMPLE_ACCOUNT)


def test_get_account(account_storage: AccountStorage):
    """Test retrieving an account."""
    account_storage.add_account(SAMPLE_ACCOUNT)
    account = account_storage.get_account(SAMPLE_ACCOUNT.name)
    assert account.name == SAMPLE_ACCOUNT.name


def test_get_nonexistent_account_raises_error(account_storage: AccountStorage):
    """Test that getting a non-existent account raises AccountNotFoundError."""
    with pytest.raises(AccountNotFoundError):
        account_storage.get_account("nonexistent")


def test_list_accounts(account_storage: AccountStorage):
    """Test listing accounts."""
    assert account_storage.list_accounts() == []
    account_storage.add_account(SAMPLE_ACCOUNT)
    accounts_list = account_storage.list_accounts()
    assert len(accounts_list) == 1
    assert accounts_list[0].name == SAMPLE_ACCOUNT.name
    # Ensure password is not in the listed info
    assert not hasattr(accounts_list[0], "encrypted_password")
    assert not hasattr(accounts_list[0], "password")


def test_remove_account(account_storage: AccountStorage):
    """Test removing an account."""
    account_storage.add_account(SAMPLE_ACCOUNT)
    assert account_storage.account_exists(SAMPLE_ACCOUNT.name)
    account_storage.remove_account(SAMPLE_ACCOUNT.name)
    assert not account_storage.account_exists(SAMPLE_ACCOUNT.name)


def test_remove_nonexistent_account_raises_error(account_storage: AccountStorage):
    """Test that removing a non-existent account raises AccountNotFoundError."""
    with pytest.raises(AccountNotFoundError):
        account_storage.remove_account("nonexistent")


def test_get_account_password(account_storage: AccountStorage):
    """Test retrieving a decrypted password."""
    account_storage.add_account(SAMPLE_ACCOUNT)
    password = account_storage.get_account_password(SAMPLE_ACCOUNT.name)
    assert password == SAMPLE_ACCOUNT.password


def test_reset_storage(account_storage: AccountStorage):
    """Test resetting the entire storage."""
    account_storage.add_account(SAMPLE_ACCOUNT)
    assert account_storage.config_dir.exists()
    assert account_storage.accounts_file.exists()
    assert account_storage.credential_manager.is_initialized()

    account_storage.reset_storage()
    assert not account_storage.accounts_file.exists()
    assert not account_storage.credential_manager.is_initialized()
