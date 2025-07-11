# Copyright (C) 2025, Relay.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

"""Tests for IMAP provider."""

from base64 import b64decode
from email.message import EmailMessage
from imaplib import IMAP4
from socket import gaierror

import pytest
from pytest_mock import MockerFixture

from relay.exceptions import AuthenticationError, ServerConnectionError
from relay.models.account import EmailProvider
from relay.providers.imap import (
    IMAPClient,
    clear_quoted_body,
    parse_email_parts,
    parse_html_body,
    resolve_thread_id,
)


@pytest.fixture
def simple_email() -> EmailMessage:
    """A simple plain text email."""
    msg = EmailMessage()
    msg["Message-ID"] = "<simple@example.com>"
    msg["From"] = "sender@example.com"
    msg["To"] = "receiver@example.com"
    msg["Subject"] = "Simple Email"
    msg["Date"] = "Tue, 15 Nov 2023 09:26:03 +0000"
    msg.set_payload("This is the body of the email.")
    return msg


@pytest.fixture
def multipart_email() -> EmailMessage:
    """A multipart email with text, html, and an attachment."""
    msg = EmailMessage()
    msg["Message-ID"] = "<multipart@example.com>"
    msg["From"] = "sender@example.com"
    msg["To"] = "receiver@example.com"
    msg["Subject"] = "Multipart Email"
    msg["Date"] = "Wed, 16 Nov 2023 10:00:00 +0000"

    msg.set_content("This is the plain text part.")
    msg.add_alternative("<html><body><p>This is the <b>HTML</b> part.</p></body></html>", subtype="html")
    msg.add_attachment(b"attachment content", maintype="application", subtype="octet-stream", filename="test.txt")
    return msg


@pytest.mark.parametrize(
    "email_address,provider,imap_server,expected_server,expected_provider",
    [
        # Gmail provider detection by email
        ("user@gmail.com", None, None, "imap.gmail.com", EmailProvider.GMAIL),
        ("user@googlemail.com", None, None, "imap.gmail.com", EmailProvider.GMAIL),
        # Outlook provider detection by email
        ("user@outlook.com", None, None, "outlook.office365.com", EmailProvider.OUTLOOK),
        ("user@hotmail.com", None, None, "outlook.office365.com", EmailProvider.OUTLOOK),
        # Yahoo provider detection by email
        ("user@yahoo.com", None, None, "imap.mail.yahoo.com", EmailProvider.YAHOO),
        # iCloud provider detection by email
        ("user@icloud.com", None, None, "imap.mail.me.com", EmailProvider.ICLOUD),
        # Explicit provider
        ("user@example.com", EmailProvider.GMAIL, None, "imap.gmail.com", EmailProvider.GMAIL),
        ("user@example.com", "gmail", None, "imap.gmail.com", EmailProvider.GMAIL),
        # Custom IMAP server
        ("user@example.com", None, "imap.example.com", "imap.example.com", EmailProvider.CUSTOM),
        # Provider detection by IMAP server
        ("user@example.com", None, "imap.gmail.com", "imap.gmail.com", EmailProvider.GMAIL),
    ],
)
def test_imap_client_init_parametrized(
    mocker: MockerFixture,
    email_address: str,
    provider: EmailProvider | str | None,
    imap_server: str | None,
    expected_server: str,
    expected_provider: EmailProvider,
):
    """Test IMAP client initialization with various parameter combinations."""
    mock_imap_ssl = mocker.patch("relay.providers.imap.IMAP4_SSL")
    mock_imap_instance = mock_imap_ssl.return_value
    mock_imap_instance.login.return_value = ("OK", [b"Login successful"])

    client = IMAPClient(email_address, "password", provider=provider, imap_server=imap_server)

    mock_imap_ssl.assert_called_once_with(expected_server, 993)
    mock_imap_instance.login.assert_called_once_with(email_address, "password")
    assert client.provider == expected_provider


@pytest.mark.parametrize(
    "email_address,provider,imap_server,expected_error",
    [
        # Invalid email address
        ("invalid-email", None, None, ValueError),
        # Missing provider and server
        ("user@unknown.com", None, None, ValueError),
        # Invalid provider string
        ("user@example.com", "invalid_provider", None, ValueError),
    ],
)
def test_imap_client_init_errors(
    mocker: MockerFixture,
    email_address: str,
    provider: str | None,
    imap_server: str | None,
    expected_error: type[Exception],
):
    """Test IMAP client initialization error cases."""
    mocker.patch("relay.providers.imap.IMAP4_SSL")

    with pytest.raises(expected_error):
        IMAPClient(email_address, "password", provider=provider, imap_server=imap_server)


def test_imap_client_connection_failure(mocker: MockerFixture):
    """Test IMAP client connection failure."""

    mocker.patch("relay.providers.imap.IMAP4_SSL", side_effect=gaierror("Name resolution failed"))

    with pytest.raises(ServerConnectionError, match="Unable to connect to IMAP server"):
        IMAPClient("user@gmail.com", "password")


def test_imap_client_login_failure(mocker: MockerFixture):
    """Test IMAP client login failure."""

    mock_imap_ssl = mocker.patch("relay.providers.imap.IMAP4_SSL")
    mock_imap_instance = mock_imap_ssl.return_value
    mock_imap_instance.login.side_effect = IMAP4.error("Authentication failed")

    with pytest.raises(AuthenticationError, match="Invalid IMAP credentials"):
        IMAPClient("user@gmail.com", "password")


def test_list_email_uids(mocker: MockerFixture):
    """Test listing email UIDs."""
    mock_imap_ssl = mocker.patch("relay.providers.imap.IMAP4_SSL")
    mock_imap_instance = mock_imap_ssl.return_value

    # Simulate login, select, search, and close
    mock_imap_instance.login.return_value = ("OK", [b"Login successful"])
    mock_imap_instance.select.return_value = ("OK", [b"123"])
    mock_imap_instance.uid.return_value = ("OK", [b"1 2 3 4 5"])
    mock_imap_instance.close.return_value = ("OK", [b""])

    client = IMAPClient("user@gmail.com", "password")
    uids = client.list_email_uids()

    mock_imap_instance.select.assert_called_once_with("INBOX", readonly=True)
    mock_imap_instance.uid.assert_called_once_with("SEARCH", None, "ALL")
    assert uids == ["1", "2", "3", "4", "5"]
    assert mock_imap_instance.close.called


def test_list_email_uids_unseen_only(mocker: MockerFixture):
    """Test listing only unseen email UIDs."""
    mock_imap_ssl = mocker.patch("relay.providers.imap.IMAP4_SSL")
    mock_imap_instance = mock_imap_ssl.return_value

    mock_imap_instance.login.return_value = ("OK", [b"Login successful"])
    mock_imap_instance.select.return_value = ("OK", [b"123"])
    mock_imap_instance.uid.return_value = ("OK", [b"4 5"])
    mock_imap_instance.close.return_value = ("OK", [b""])

    client = IMAPClient("user@gmail.com", "password")
    uids = client.list_email_uids(unseen_only=True)

    mock_imap_instance.uid.assert_called_once_with("SEARCH", None, "UNSEEN")
    assert uids == ["4", "5"]


def test_mark_as_read(mocker: MockerFixture):
    """Test marking email as read."""
    mock_imap_ssl = mocker.patch("relay.providers.imap.IMAP4_SSL")
    mock_imap_instance = mock_imap_ssl.return_value

    mock_imap_instance.login.return_value = ("OK", [b"Login successful"])
    mock_imap_instance.select.return_value = ("OK", [b"123"])
    mock_imap_instance.uid.return_value = ("OK", [b"STORE completed"])
    mock_imap_instance.close.return_value = ("OK", [b""])

    client = IMAPClient("user@gmail.com", "password")
    client.mark_as_read("123")

    mock_imap_instance.select.assert_called_once_with("INBOX", readonly=False)
    mock_imap_instance.uid.assert_called_once_with("STORE", "123", "+FLAGS", "\\Seen")


def test_parse_email_parts_simple(simple_email: EmailMessage):
    """Test parse_email_parts with a simple email."""
    parts = parse_email_parts(simple_email)
    assert parts["text_plain"] == "This is the body of the email."
    assert parts["text_html"] is None
    assert parts["parsed_html"] is None
    assert len(parts["attachments"]) == 0


def test_parse_email_parts_multipart(multipart_email: EmailMessage):
    """Test parse_email_parts with a multipart email."""
    parts = parse_email_parts(multipart_email)
    assert parts["text_plain"].strip() == "This is the plain text part."
    assert parts["text_html"].strip() == "<html><body><p>This is the <b>HTML</b> part.</p></body></html>"
    assert "This is the **HTML** part." in parts["parsed_html"]
    assert len(parts["attachments"]) == 1
    attachment = parts["attachments"][0]
    assert attachment["filename"] == "test.txt"
    assert attachment["content_type"] == "application/octet-stream"
    assert b64decode(attachment["content"]) == b"attachment content"


@pytest.mark.parametrize(
    "email_headers,expected_thread_id",
    [
        # With References
        (
            {"References": "<ref1@example.com> <ref2@example.com>", "Message-ID": "<msg@example.com>"},
            "<ref1@example.com>",
        ),
        # With In-Reply-To but no References
        ({"In-Reply-To": "<reply_to@example.com>", "Message-ID": "<msg@example.com>"}, None),
        # With only Message-ID
        ({"Message-ID": "<msg@example.com>"}, "<msg@example.com>"),
        # With Message-Id (alternative casing)
        ({"Message-Id": "<msg@example.com>"}, "<msg@example.com>"),
        # Empty References
        ({"References": "", "Message-ID": "<msg@example.com>"}, "<msg@example.com>"),
    ],
)
def test_resolve_thread_id_parametrized(email_headers: dict[str, str], expected_thread_id: str | None):
    """Test resolve_thread_id with various header combinations."""
    assert resolve_thread_id(email_headers) == expected_thread_id


def test_parse_html_body():
    """Test parse_html_body."""
    html = "<h1>Title</h1><p>Some text with a <a href='#'>link</a>.</p>"
    text = parse_html_body(html)
    assert text.strip() == "# Title\n\nSome text with a link."


@pytest.mark.parametrize(
    "input_text,expected_contains,expected_not_contains",
    [
        # Standard quoted reply
        (
            "This is my reply.\n\nOn Wed, Nov 15, 2023 at 10:00 AM, Sender <sender@example.com> wrote:\n> Original message",
            ["This is my reply."],
            ["On Wed, Nov 15, 2023", "Original message"],
        ),
        # No quoted content
        (
            "This is just a regular email body.",
            ["This is just a regular email body."],
            [],
        ),
        # Multiple email addresses
        (
            "Reply text.\n\nFrom: <first@example.com>\nTo: <second@example.com>\n> Quoted text",
            ["Reply text."],
            ["Quoted text"],
        ),
    ],
)
def test_clear_quoted_body_parametrized(
    input_text: str, expected_contains: list[str], expected_not_contains: list[str]
):
    """Test clear_quoted_body with various input patterns."""
    cleaned_text = clear_quoted_body(input_text)

    for text in expected_contains:
        assert text in cleaned_text

    for text in expected_not_contains:
        assert text not in cleaned_text
