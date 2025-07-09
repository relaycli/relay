# Copyright (C) 2025, Relay.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

"""Tests for IMAP provider."""

from base64 import b64decode
from email.message import EmailMessage

import pytest
from pytest_mock import MockerFixture

from relay.exceptions import AuthenticationError, ServerConnectionError
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
    # The expected output from html2text might need adjustment based on its version
    assert "This is the **HTML** part." in parts["parsed_html"]
    assert len(parts["attachments"]) == 1
    attachment = parts["attachments"][0]
    assert attachment["filename"] == "test.txt"
    assert attachment["content_type"] == "application/octet-stream"
    # Content is base64 encoded
    assert b64decode(attachment["content"]) == b"attachment content"


def test_resolve_thread_id():
    """Test resolve_thread_id logic."""
    # With References
    msg_with_refs = {"References": "<ref1@example.com> <ref2@example.com>", "Message-ID": "<msg@example.com>"}
    assert resolve_thread_id(msg_with_refs) == "<ref1@example.com>"

    # With In-Reply-To but no References
    msg_with_in_reply_to = {"In-Reply-To": "<reply_to@example.com>", "Message-ID": "<msg@example.com>"}
    assert resolve_thread_id(msg_with_in_reply_to) is None

    # With only Message-ID
    msg_with_id = {"Message-ID": "<msg@example.com>"}
    assert resolve_thread_id(msg_with_id) == "<msg@example.com>"


def test_parse_html_body():
    """Test parse_html_body."""
    html = "<h1>Title</h1><p>Some text with a <a href='#'>link</a>.</p>"
    text = parse_html_body(html)
    assert text.strip() == "# Title\n\nSome text with a link."


def test_clear_quoted_body():
    """Test clear_quoted_body."""
    original_text = (
        "This is my reply.\n\n"
        "On Wed, Nov 15, 2023 at 10:00 AM, Sender <sender@example.com> wrote:\n"
        "> This is the original message.\n"
        ">\n"
        "> > Quoted text inside."
    )
    cleaned_text = clear_quoted_body(original_text)
    assert "This is my reply." in cleaned_text
    assert "On Wed, Nov 15, 2023" not in cleaned_text
    assert "This is the original message." not in cleaned_text

    text_with_no_quote = "This is just a regular email body."
    assert clear_quoted_body(text_with_no_quote) == text_with_no_quote
