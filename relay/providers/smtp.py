# Copyright (C) 2025, Relay.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from email.mime.text import MIMEText
from email.utils import formataddr
from smtplib import SMTP_SSL

from email_validator import EmailNotValidError, validate_email

from ..exceptions import AuthenticationError
from ..models.account import EmailProvider
from .utils import EMAIL_TO_PROVIDER, PROVIDER_INFO

__all__ = ["SMTPClient"]


class SMTPClient:
    """SMTP client for sending emails."""

    def __init__(
        self,
        email_address: str,
        password: str,
        provider: str | EmailProvider | None = None,
        smtp_server: str | None = None,
        smtp_port: int = 465,
        sender_name: str | None = None,
        **kwargs,
    ) -> None:
        """Initialize the SMTP client.

        Args:
            email_address: Email address
            password: Password
            provider: Email provider
            smtp_server: SMTP server address
            smtp_port: SMTP port
            sender_name: Sender name
            kwargs: Additional SMTP parameters

        Raises:
            AuthenticationError: If SMTP credentials are invalid
            ValueError: If there are missing information
        """
        # Validate email format
        try:
            validate_email(email_address, check_deliverability=False)
        except EmailNotValidError:
            raise ValueError("Invalid email address")

        # Server resolution
        if smtp_server is None:
            if provider is None:
                # Try with email
                email_domain = email_address.rpartition("@")[-1].lower()
                provider = EMAIL_TO_PROVIDER.get(email_domain)
                if provider is None:
                    raise ValueError("Either specify a provider or SMTP server address")
            else:
                provider = EmailProvider(provider)
            smtp_server = smtp_server or PROVIDER_INFO[provider]["smtp"]["server"]
            smtp_port = smtp_port or PROVIDER_INFO[provider]["smtp"]["port"]
        # SMTP
        self._smtp = SMTP_SSL(smtp_server, smtp_port, **kwargs)
        # Prevent ASCII encoding errors
        # cf. https://github.com/trac-hacks/tracsql/issues/3
        password = password.replace("\xa0", " ")
        status_, _ = self._smtp.login(email_address, password)
        if status_ != 235:
            raise AuthenticationError("Invalid SMTP credentials")
        self.sender_name = sender_name

    def quit(self) -> None:
        """Quit the SMTP client."""
        self._smtp.quit()

    def send_email(self, content: str, to_addrs: list[str], text_subtype: str = "plain", **kwargs) -> None:
        """Send an email.

        Args:
            content: Email content
            to_addrs: List of recipient email addresses
            text_subtype: Text subtype
            kwargs: Additional SMTP parameters
        """
        msg = MIMEText(content, text_subtype)
        msg["From"] = kwargs.pop(
            "From", formataddr((self.sender_name, self._smtp.user)) if self.sender_name else self._smtp.user
        )
        for k, v in kwargs.items():
            msg.add_header(k, v)

        self._smtp.sendmail(self._smtp.user, to_addrs, msg.as_string())
