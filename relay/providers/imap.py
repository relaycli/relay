# Copyright (C) 2025, Relay.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

import base64
import re
from email import message_from_bytes
from email.message import EmailMessage
from email.parser import Parser
from email.utils import parsedate_to_datetime
from imaplib import IMAP4, IMAP4_SSL
from socket import gaierror
from typing import Any, cast

from bs4 import BeautifulSoup
from html2text import html2text

from ..exceptions import AuthenticationError, ServerConnectionError, ValidationError
from ..models.account import EmailProvider
from .utils import resolve_provider

EMAIL_PATTERN = r"<[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}>"

__all__ = ["IMAPClient"]

EMAIL_PROVIDERS = {
    EmailProvider.GMAIL: {
        "email_domains": ["gmail.com", "googlemail.com"],
        "server_domains": ["gmail.com"],
        "folders": {
            "inbox": "INBOX",
            "trash": "[Gmail]/Trash",
            "spam": "[Gmail]/Spam",
            "sent": "[Gmail]/Sent Mail",
            "drafts": "[Gmail]/Drafts",
        },
    },
    EmailProvider.OUTLOOK: {
        "email_domains": ["outlook.com", "hotmail.com", "hotmail.fr", "live.com"],
        "server_domains": ["outlook.com", "office365.com"],
        "folders": {
            "inbox": "INBOX",
            "trash": "Deleted Items",
            "spam": "Junk Email",
            "sent": "Sent Items",
            "drafts": "Drafts",
        },
    },
    EmailProvider.YAHOO: {
        "email_domains": ["yahoo.com", "yahoo.co.uk", "yahoo.ca"],
        "server_domains": ["yahoo.com"],
        "folders": {"inbox": "INBOX", "trash": "Trash", "spam": "Bulk Mail", "sent": "Sent", "drafts": "Draft"},
    },
    EmailProvider.ICLOUD: {
        "email_domains": ["icloud.com", "me.com", "mac.com"],
        "server_domains": ["icloud.com", "me.com"],
        "folders": {
            "inbox": "INBOX",
            "trash": "Deleted Messages",
            "spam": "Junk",
            "sent": "Sent Messages",
            "drafts": "Drafts",
        },
    },
}

MIN_HEADERS = {"Message-ID", "Message-Id", "From", "To", "Subject", "Date", "CC", "BCC"}
EXTRA_HEADERS = {"Delivered-To", "Sender", "References", "In-Reply-To", "Thread-Topic"}
SORTING_HEADERS = {"List-Unsubscribe", "List-Id", "Precedence", "Auto-Submitted", "Reply-To", "Return-Path"}


class IMAPClient:
    """IMAP client for managing emails.

    Args:
        imap_server: IMAP server address
        email_address: Email address
        password: Password
        imap_port: IMAP port
        provider: Email provider
        kwargs: Additional IMAP parameters

    Raises:
        ServerConnectionError: If IMAP server is not found
        AuthenticationError: If IMAP credentials are invalid
    """

    def __init__(
        self,
        imap_server: str,
        email_address: str,
        password: str,
        imap_port: int = 993,
        provider: str | EmailProvider | None = None,
        **kwargs,
    ) -> None:
        """Initialize the IMAP client."""
        # Convert string provider to EmailProvider enum
        if isinstance(provider, str):
            provider = EmailProvider(provider)

        # Auto-detect provider if not provided
        if not provider:
            provider = resolve_provider(imap_server, email_address)

        # IMAP
        try:
            self._imap = IMAP4_SSL(imap_server, imap_port, **kwargs)
        except gaierror:
            raise ServerConnectionError("IMAP server not found")
        # Prevent ASCII encoding errors
        # cf. https://github.com/trac-hacks/tracsql/issues/3
        password = password.replace("\xa0", " ")
        try:
            self._imap.login(email_address, password)
        except IMAP4.error:
            raise AuthenticationError("Invalid IMAP credentials")

        self.provider = provider
        self.config = EMAIL_PROVIDERS.get(
            provider,
            {
                "folders": {
                    "inbox": "INBOX",
                    "trash": "Trash",
                    "spam": "Spam",
                    "sent": "Sent",
                },
            },
        )

    def logout(self) -> None:
        """Logout from the IMAP server."""
        self._imap.logout()

    def _select(self, folder: str = "INBOX", readonly: bool = True) -> None:
        try:
            status_, res = self._imap.select(folder, readonly=readonly)
            if status_ != "OK":
                raise ValueError(res[0].decode())
        except IMAP4.error:
            raise ValidationError(f"Invalid folder: {folder}")

    def list_flags(self, **kwargs) -> list[str]:
        """List flags for the selected folder.

        Args:
            kwargs: Additional IMAP parameters

        Returns:
            List of flags
        """
        self._select(readonly=False, **kwargs)
        _, flags = self._imap.response("FLAGS")
        self._imap.close()
        return flags[0].decode().strip("()").split()

    def _uid(self, command: str, *args, **kwargs) -> list[bytes | list[bytes]]:
        try:
            status_, res = self._imap.uid(command, *args, **kwargs)
        except IMAP4.error as e:
            self._imap.close()
            if e.args[0].startswith("Unknown IMAP4 UID command"):
                raise ValueError(e.args[0])
            if e.args[0].endswith("only allowed in states SELECTED"):
                raise AssertionError(e.args[0])
            if e.args[0].startswith("UID command error"):
                raise ValueError(e.args[0])
            raise ValidationError(e)
        if status_ != "OK":
            self._imap.close()
            raise ValidationError(status_)
        return res

    def _search(self, query: str) -> list[bytes]:
        return cast(list[bytes], self._uid("SEARCH", None, query))

    def _flags(self, uid: str, op: str, flags: str) -> None:
        self._uid("STORE", uid, f"{op}FLAGS", flags)

    def _copy(self, uid: str, folder: str) -> None:
        self._uid("COPY", uid, folder)

    def _fetch(self, uid: str, msg_parts: str) -> list[list[bytes]]:
        return cast(list[list[bytes]], self._uid("FETCH", uid, msg_parts))

    def list_email_uids(self, unseen_only: bool = False, **kwargs) -> list[str]:
        """List email UIDs.

        Args:
            unseen_only: Whether to only list unseen emails
            kwargs: Additional IMAP parameters

        Returns:
            List of email UIDs
        """
        self._select(readonly=True, **kwargs)
        res = self._search("UNSEEN" if unseen_only else "ALL")
        self._imap.close()
        return res[0].decode().split()

    def fetch_message(
        self, uid: str, headers_set: set | None = None, include_quoted_body: bool = False, **kwargs
    ) -> dict[str, Any]:
        """Fetch a single email message.

        Args:
            uid: Email UID
            headers_set: Set of headers to include
            include_quoted_body: Whether to include quoted body
            kwargs: Additional IMAP parameters

        Returns:
            Dictionary of email message
        """
        self._select(readonly=True, **kwargs)
        content = self._fetch(uid, "(RFC822)")
        self._imap.close()
        message = cast(EmailMessage, message_from_bytes(content[0][1]))
        return {
            "uid": uid,
            "thread_id": resolve_thread_id(message),
            "date": parsedate_to_datetime(message.get("Date", "")).isoformat(),
            "subject": message.get(
                "Thread-Topic",
                message.get("Subject", "")
                .replace("Re:", "")
                .replace("RE:", "")
                .replace("Fwd:", "")
                .replace("FWD:", "")
                .strip(),
            ),
            "headers": {
                "Message-ID" if k.lower() == "message-id" else k: v.strip()
                for k, v in message.items()
                if headers_set is None or k in headers_set
            },
            "body": parse_email_parts(message, include_quoted_body),
        }

    def fetch_headers(self, uids: list[str], headers_set: set, **kwargs) -> list[dict[str, Any]]:
        """Fetch headers for multiple email messages.

        Args:
            uids: List of email UIDs
            headers_set: Set of headers to include
            kwargs: Additional IMAP parameters

        Returns:
            List of dictionaries of email headers
        """
        self._select(readonly=True, **kwargs)
        if len(uids) == 0:
            return []

        msg_parts = f"(BODY.PEEK[HEADER.FIELDS ({' '.join(tuple(headers_set))})])"
        content = self._fetch(",".join(uids), msg_parts.upper())
        self._imap.close()
        parser_ = Parser()
        return [
            {"uid": uid, "headers": dict(parser_.parsestr(res[1].decode("utf-8"), headersonly=True).items())}
            for uid, res in zip(uids, content[::2], strict=True)
        ]

    def fetch_messages(
        self,
        uids: list[str],
        headers_set: set | None = None,
        include_quoted_body: bool = False,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Fetch multiple email messages.

        Args:
            uids: List of email UIDs
            headers_set: Set of headers to include
            include_quoted_body: Whether to include quoted body
            kwargs: Additional IMAP parameters

        Returns:
            List of dictionaries of email messages
        """
        self._select(readonly=True, **kwargs)
        if len(uids) == 0:
            return []

        content = self._fetch(",".join(uids), "(RFC822)")
        self._imap.close()
        email_messages = [cast(EmailMessage, message_from_bytes(res[1])) for res in content[::2]]
        return [
            {
                "uid": uid,
                "thread_id": resolve_thread_id(message),
                "subject": message.get(
                    "Thread-Topic",
                    message.get("Subject", "")
                    .replace("Re:", "")
                    .replace("RE:", "")
                    .replace("Fwd:", "")
                    .replace("FWD:", "")
                    .strip(),
                ),
                "date": parsedate_to_datetime(message.get("Date", "")).isoformat(),
                "headers": {
                    "Message-ID" if k.lower() == "message-id" else k: v.strip()
                    for k, v in message.items()
                    if headers_set is None or k in headers_set
                },
                "body": parse_email_parts(message, include_quoted_body=include_quoted_body),
            }
            for uid, message in zip(reversed(uids), email_messages, strict=True)
        ]

    def mark_as_read(self, uid: str) -> None:
        """Mark email as read.

        Args:
            uid: Email UID
        """
        self._select("INBOX", readonly=False)
        self._flags(uid, "+", "\\Seen")
        self._imap.close()

    def mark_as_unread(self, uid: str) -> None:
        """Mark email as unread.

        Args:
            uid: Email UID
        """
        self._select("INBOX", readonly=False)
        self._flags(uid, "-", "\\Seen")
        self._imap.close()

    def move_to_trash(self, uid: str) -> None:
        """Move email to trash folder.

        Args:
            uid: Email UID
        """
        self._select("INBOX", readonly=False)

        # First copy to trash folder
        self._copy(uid, self.config["folders"]["trash"])

        # Then mark as deleted
        self._flags(uid, "+", "\\Deleted")

        # Finally expunge
        status_, _ = self._imap.expunge()
        if status_ != "OK":
            self._imap.close()
            raise ValidationError(f"Failed to expunge message {uid}: {status_}")

        self._imap.close()

    def delete_email(self, uid: str) -> None:
        """Delete email permanently.

        Args:
            uid: Email UID
        """
        self._select("INBOX", readonly=False)

        # Mark as deleted
        self._flags(uid, "+", "\\Deleted")
        # Expunge to permanently delete
        status_, _ = self._imap.expunge()
        if status_ != "OK":
            self._imap.close()
            raise ValidationError(f"Failed to expunge message {uid}: {status_}")

        self._imap.close()

    def mark_as_spam(self, uid: str) -> None:
        """Move email to spam folder.

        Args:
            uid: Email UID
        """
        self._select("INBOX", readonly=False)

        # First copy to spam folder
        self._copy(uid, self.config["folders"]["spam"])

        # Then mark as deleted from inbox
        self._flags(uid, "+", "\\Deleted")

        # Finally expunge from inbox
        status_, _ = self._imap.expunge()
        if status_ != "OK":
            self._imap.close()
            raise ValidationError(f"Failed to expunge message {uid}: {status_}")

        self._imap.close()


def resolve_thread_id(email_message: EmailMessage | dict[str, str]) -> str | None:
    """Resolve thread ID from email headers.

    Args:
        email_message: Email message

    Returns:
        Thread ID
    """
    # Clean resolution
    if isinstance(email_message.get("References"), str) and len(email_message.get("References", "").split()) > 0:
        return email_message.get("References", "").split()[0].strip()
    # Failure (missing references)
    if email_message.get("In-Reply-To") is not None:
        return None
    return email_message.get("Message-ID", email_message.get("Message-Id"))


def parse_email_parts(email_message: EmailMessage, include_quoted_body: bool = False) -> dict[str, Any]:
    """Extract plain text body from email.

    Args:
        email_message: Email message
        include_quoted_body: Whether to include quoted body

    Returns:
        Dictionary of email parts
    """
    body_plain = None
    body_html = None
    attachments = []
    if email_message.is_multipart():
        for part in email_message.walk():
            if part.get_content_type() == "text/plain":
                body_plain = part.get_payload(decode=True).decode("utf-8", errors="ignore")
            # Parse HTML
            if part.get_content_type() == "text/html":
                body_html = part.get_payload(decode=True).decode("utf-8", errors="ignore")
            # Parse attachments
            if isinstance(part.get_content_disposition(), str) and part.get_content_disposition() == "attachment":
                attachments.append({
                    "filename": part.get_filename(),
                    "content_type": part.get_content_type(),
                    "content": base64.b64encode(part.get_payload(decode=True) or b"").decode("utf-8"),
                    "size": len(part.get_payload(decode=True)) if part.get_payload(decode=True) else 0,
                })
    else:
        body_plain = email_message.get_payload(decode=True).decode("utf-8", errors="ignore")

    if body_plain and not include_quoted_body:
        body_plain = clear_quoted_body(body_plain)

    return {
        "text_plain": body_plain,
        "text_html": body_html,
        "parsed_html": parse_html_body(body_html) if body_html else None,
        "attachments": attachments,
    }


def parse_html_body(body_html: str) -> str:
    soup = BeautifulSoup(body_html, "html.parser")
    return html2text(str(soup))


def clear_quoted_body(plain_text: str) -> str:
    # Find the closest email address before the quote
    match = re.search(EMAIL_PATTERN, plain_text)
    if not match:
        return plain_text
    match_position = match.start()
    line_index = plain_text[:match_position].count("\n")

    # Find the first empty line before the match line
    lines = plain_text.splitlines()
    empty_line_idx = next((idx for idx, line in enumerate(reversed(lines[:line_index])) if not line.strip()), None)
    line_index = line_index if empty_line_idx is None else line_index - empty_line_idx
    return "\r\n".join(lines[:line_index])
