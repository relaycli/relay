# Copyright (C) 2025, Relay.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from email.mime.text import MIMEText
from email.utils import formataddr
from smtplib import SMTP_SSL

from ._utils import resolve_provider

__all__ = ["SMTPClient"]


class SMTPClient:
    def __init__(
        self,
        smtp_server: str,
        email_address: str,
        password: str,
        smtp_port: int = 465,
        sender_name: str | None = None,
        provider: str | None = None,
        **kwargs,
    ) -> None:
        if not provider:
            provider = resolve_provider(smtp_server, email_address)
        # SMTP
        self._smtp = SMTP_SSL(smtp_server, smtp_port, **kwargs)
        # Prevent ASCII encoding errors
        # cf. https://github.com/trac-hacks/tracsql/issues/3
        password = password.replace("\xa0", " ")
        status_, _ = self._smtp.login(email_address, password)
        if status_ != 235:
            raise ValueError("Invalid SMTP credentials")
        self.sender_name = sender_name

    def quit(self) -> None:
        self._smtp.quit()

    def send_email(self, content: str, to_addrs: list[str], text_subtype: str = "plain", **kwargs) -> None:
        msg = MIMEText(content, text_subtype)
        msg["From"] = kwargs.pop(
            "From", formataddr((self.sender_name, self._smtp.user)) if self.sender_name else self._smtp.user
        )
        for k, v in kwargs.items():
            msg.add_header(k, v)

        self._smtp.sendmail(self._smtp.user, to_addrs, msg.as_string())
