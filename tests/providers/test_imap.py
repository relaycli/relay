# Copyright (C) 2025, Relay.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

"""Tests for IMAP provider."""

import pytest
from pytest_mock import MockerFixture

from relay.exceptions import AuthenticationError, ServerConnectionError
from relay.providers.imap import IMAPClient


def test_imap_client_init(mocker: MockerFixture):
    """Test successful IMAP client initialization and login."""
    mock_imap_ssl = mocker.patch("relay.providers.imap.IMAP4_SSL")
    mock_imap_instance = mock_imap_ssl.return_value
    mock_imap_instance.login.return_value = ("OK", [b"Login successful"])

    client = IMAPClient("imap.example.com", "user@example.com", "password")

    mock_imap_ssl.assert_called_once_with("imap.example.com", 993)
    mock_imap_instance.login.assert_called_once_with("user@example.com", "password")
    assert client is not None


def test_imap_client_login_failure(mocker: MockerFixture):
    """Test IMAP client login failure."""
    mock_imap_ssl = mocker.patch("relay.providers.imap.IMAP4_SSL")
    mock_imap_instance = mock_imap_ssl.return_value
    mock_imap_instance.login.side_effect = AuthenticationError("Invalid IMAP credentials")

    with pytest.raises(AuthenticationError):
        IMAPClient("imap.example.com", "user@example.com", "wrong-password")


def test_imap_client_connection_failure(mocker: MockerFixture):
    """Test IMAP client connection failure."""
    mocker.patch("relay.providers.imap.IMAP4_SSL", side_effect=ServerConnectionError("IMAP server not found"))

    with pytest.raises(ServerConnectionError):
        IMAPClient("imap.example.com", "user@example.com", "password")


def test_list_email_uids(mocker: MockerFixture):
    """Test listing email UIDs."""
    mock_imap_ssl = mocker.patch("relay.providers.imap.IMAP4_SSL")
    mock_imap_instance = mock_imap_ssl.return_value

    # Simulate login, select, search, and close
    mock_imap_instance.login.return_value = ("OK", [b"Login successful"])
    mock_imap_instance.select.return_value = ("OK", [b"123"])  # Total messages
    mock_imap_instance.uid.return_value = ("OK", [b"1 2 3 4 5"])
    mock_imap_instance.close.return_value = ("OK", [b""])

    client = IMAPClient("imap.example.com", "user@example.com", "password")
    uids = client.list_email_uids()

    mock_imap_instance.select.assert_called_once_with("INBOX", readonly=True)
    mock_imap_instance.uid.assert_called_once_with("SEARCH", None, "ALL")
    assert uids == ["1", "2", "3", "4", "5"]
    assert mock_imap_instance.close.called
