# Copyright (C) 2025, Relay.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

"""Tests for SMTP provider."""

import pytest
from pytest_mock import MockerFixture

from relay.exceptions import AuthenticationError
from relay.models.account import EmailProvider
from relay.providers.smtp import SMTPClient


@pytest.mark.parametrize(
    "email_address,provider,smtp_server,expected_server,expected_provider",
    [
        # Gmail provider detection by email
        ("user@gmail.com", None, None, "smtp.gmail.com", EmailProvider.GMAIL),
        ("user@googlemail.com", None, None, "smtp.gmail.com", EmailProvider.GMAIL),
        # Outlook provider detection by email
        ("user@outlook.com", None, None, "smtp-mail.outlook.com", EmailProvider.OUTLOOK),
        ("user@hotmail.com", None, None, "smtp-mail.outlook.com", EmailProvider.OUTLOOK),
        # Yahoo provider detection by email
        ("user@yahoo.com", None, None, "smtp.mail.yahoo.com", EmailProvider.YAHOO),
        # iCloud provider detection by email
        ("user@icloud.com", None, None, "smtp.mail.me.com", EmailProvider.ICLOUD),
        # Explicit provider
        ("user@example.com", EmailProvider.GMAIL, None, "smtp.gmail.com", EmailProvider.GMAIL),
        ("user@example.com", "gmail", None, "smtp.gmail.com", EmailProvider.GMAIL),
        # Custom SMTP server
        ("user@example.com", None, "smtp.example.com", "smtp.example.com", None),
    ],
)
def test_smtp_client_init_parametrized(
    mocker: MockerFixture,
    email_address: str,
    provider: EmailProvider | str | None,
    smtp_server: str | None,
    expected_server: str,
    expected_provider: EmailProvider | None,
):
    """Test SMTP client initialization with various parameter combinations."""
    mock_smtp_ssl = mocker.patch("relay.providers.smtp.SMTP_SSL")
    mock_smtp_instance = mock_smtp_ssl.return_value
    mock_smtp_instance.login.return_value = (235, b"Authentication successful")
    mock_smtp_instance.user = email_address

    client = SMTPClient(email_address, "password", provider=provider, smtp_server=smtp_server)

    mock_smtp_ssl.assert_called_once_with(expected_server, 465)
    mock_smtp_instance.login.assert_called_once_with(email_address, "password")
    assert client is not None


@pytest.mark.parametrize(
    "email_address,provider,smtp_server,expected_error",
    [
        # Invalid email address
        ("invalid-email", None, None, ValueError),
        # Missing provider and server
        ("user@unknown.com", None, None, ValueError),
        # Invalid provider string
        ("user@example.com", "invalid_provider", None, ValueError),
    ],
)
def test_smtp_client_init_errors(
    mocker: MockerFixture,
    email_address: str,
    provider: str | None,
    smtp_server: str | None,
    expected_error: type[Exception],
):
    """Test SMTP client initialization error cases."""
    mocker.patch("relay.providers.smtp.SMTP_SSL")

    with pytest.raises(expected_error):
        SMTPClient(email_address, "password", provider=provider, smtp_server=smtp_server)


def test_smtp_client_login_failure(mocker: MockerFixture):
    """Test SMTP client login failure."""
    mock_smtp_ssl = mocker.patch("relay.providers.smtp.SMTP_SSL")
    mock_smtp_instance = mock_smtp_ssl.return_value
    mock_smtp_instance.login.return_value = (535, b"Authentication failed")

    with pytest.raises(AuthenticationError, match="Invalid SMTP credentials"):
        SMTPClient("user@gmail.com", "password")


def test_smtp_client_with_sender_name(mocker: MockerFixture):
    """Test SMTP client initialization with sender name."""
    mock_smtp_ssl = mocker.patch("relay.providers.smtp.SMTP_SSL")
    mock_smtp_instance = mock_smtp_ssl.return_value
    mock_smtp_instance.login.return_value = (235, b"Authentication successful")
    mock_smtp_instance.user = "user@gmail.com"

    client = SMTPClient("user@gmail.com", "password", sender_name="John Doe")

    assert client.sender_name == "John Doe"


def test_send_email_basic(mocker: MockerFixture):
    """Test basic email sending."""
    mock_smtp_ssl = mocker.patch("relay.providers.smtp.SMTP_SSL")
    mock_smtp_instance = mock_smtp_ssl.return_value
    mock_smtp_instance.login.return_value = (235, b"Authentication successful")
    mock_smtp_instance.user = "sender@gmail.com"
    mock_smtp_instance.sendmail.return_value = {}

    client = SMTPClient("sender@gmail.com", "password")
    client.send_email("Hello, World!", ["recipient@example.com"], Subject="Test Email")

    # Verify sendmail was called with correct parameters
    mock_smtp_instance.sendmail.assert_called_once()
    call_args = mock_smtp_instance.sendmail.call_args[0]
    assert call_args[0] == "sender@gmail.com"  # from_addr
    assert call_args[1] == ["recipient@example.com"]  # to_addrs

    # Verify the message content
    message_content = call_args[2]
    assert "Hello, World!" in message_content
    assert "Subject: Test Email" in message_content
    assert "From: sender@gmail.com" in message_content


def test_send_email_with_sender_name(mocker: MockerFixture):
    """Test email sending with sender name."""
    mock_smtp_ssl = mocker.patch("relay.providers.smtp.SMTP_SSL")
    mock_smtp_instance = mock_smtp_ssl.return_value
    mock_smtp_instance.login.return_value = (235, b"Authentication successful")
    mock_smtp_instance.user = "sender@gmail.com"
    mock_smtp_instance.sendmail.return_value = {}

    client = SMTPClient("sender@gmail.com", "password", sender_name="John Doe")
    client.send_email("Hello, World!", ["recipient@example.com"], Subject="Test Email")

    # Verify the message includes formatted sender name
    call_args = mock_smtp_instance.sendmail.call_args[0]
    message_content = call_args[2]
    assert "From: John Doe <sender@gmail.com>" in message_content


def test_send_email_html(mocker: MockerFixture):
    """Test HTML email sending."""
    mock_smtp_ssl = mocker.patch("relay.providers.smtp.SMTP_SSL")
    mock_smtp_instance = mock_smtp_ssl.return_value
    mock_smtp_instance.login.return_value = (235, b"Authentication successful")
    mock_smtp_instance.user = "sender@gmail.com"
    mock_smtp_instance.sendmail.return_value = {}

    client = SMTPClient("sender@gmail.com", "password")
    html_content = "<html><body><h1>Hello, World!</h1></body></html>"
    client.send_email(html_content, ["recipient@example.com"], text_subtype="html", Subject="HTML Email")

    # Verify the message content type
    call_args = mock_smtp_instance.sendmail.call_args[0]
    message_content = call_args[2]
    assert "Content-Type: text/html" in message_content
    assert html_content in message_content


def test_send_email_multiple_recipients(mocker: MockerFixture):
    """Test email sending to multiple recipients."""
    mock_smtp_ssl = mocker.patch("relay.providers.smtp.SMTP_SSL")
    mock_smtp_instance = mock_smtp_ssl.return_value
    mock_smtp_instance.login.return_value = (235, b"Authentication successful")
    mock_smtp_instance.user = "sender@gmail.com"
    mock_smtp_instance.sendmail.return_value = {}

    client = SMTPClient("sender@gmail.com", "password")
    recipients = ["recipient1@example.com", "recipient2@example.com", "recipient3@example.com"]
    client.send_email("Hello, World!", recipients, Subject="Test Email")

    # Verify sendmail was called with all recipients
    call_args = mock_smtp_instance.sendmail.call_args[0]
    assert call_args[1] == recipients


def test_send_email_custom_headers(mocker: MockerFixture):
    """Test email sending with custom headers."""
    mock_smtp_ssl = mocker.patch("relay.providers.smtp.SMTP_SSL")
    mock_smtp_instance = mock_smtp_ssl.return_value
    mock_smtp_instance.login.return_value = (235, b"Authentication successful")
    mock_smtp_instance.user = "sender@gmail.com"
    mock_smtp_instance.sendmail.return_value = {}

    client = SMTPClient("sender@gmail.com", "password")
    client.send_email(
        "Hello, World!",
        ["recipient@example.com"],
        Subject="Test Email",
        **{"Reply-To": "noreply@example.com", "X-Priority": "1"},
    )

    # Verify custom headers are included
    call_args = mock_smtp_instance.sendmail.call_args[0]
    message_content = call_args[2]
    assert "Reply-To: noreply@example.com" in message_content
    assert "X-Priority: 1" in message_content


def test_send_email_custom_from_header(mocker: MockerFixture):
    """Test email sending with custom From header."""
    mock_smtp_ssl = mocker.patch("relay.providers.smtp.SMTP_SSL")
    mock_smtp_instance = mock_smtp_ssl.return_value
    mock_smtp_instance.login.return_value = (235, b"Authentication successful")
    mock_smtp_instance.user = "sender@gmail.com"
    mock_smtp_instance.sendmail.return_value = {}

    client = SMTPClient("sender@gmail.com", "password")
    client.send_email(
        "Hello, World!", ["recipient@example.com"], Subject="Test Email", From="Custom Sender <custom@example.com>"
    )

    # Verify custom From header is used
    call_args = mock_smtp_instance.sendmail.call_args[0]
    message_content = call_args[2]
    assert "From: Custom Sender <custom@example.com>" in message_content


def test_quit_smtp_client(mocker: MockerFixture):
    """Test SMTP client quit method."""
    mock_smtp_ssl = mocker.patch("relay.providers.smtp.SMTP_SSL")
    mock_smtp_instance = mock_smtp_ssl.return_value
    mock_smtp_instance.login.return_value = (235, b"Authentication successful")
    mock_smtp_instance.user = "sender@gmail.com"

    client = SMTPClient("sender@gmail.com", "password")
    client.quit()

    mock_smtp_instance.quit.assert_called_once()


def test_password_ascii_encoding_fix(mocker: MockerFixture):
    """Test password ASCII encoding fix."""
    mock_smtp_ssl = mocker.patch("relay.providers.smtp.SMTP_SSL")
    mock_smtp_instance = mock_smtp_ssl.return_value
    mock_smtp_instance.login.return_value = (235, b"Authentication successful")
    mock_smtp_instance.user = "sender@gmail.com"

    # Password with non-breaking space character
    password_with_nbsp = "password\xa0with\xa0nbsp"
    expected_cleaned_password = "password with nbsp"

    client = SMTPClient("sender@gmail.com", password_with_nbsp)

    # Verify the password was cleaned before being passed to login
    mock_smtp_instance.login.assert_called_once_with("sender@gmail.com", expected_cleaned_password)
