# Copyright (C) 2025, Relay.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

import base64
import re
from email import message_from_bytes
from email.message import EmailMessage
from email.parser import Parser
from email.utils import parsedate_to_datetime
from functools import reduce
from imaplib import IMAP4, IMAP4_SSL
from socket import gaierror
from typing import Any, cast

from bs4 import BeautifulSoup
from html2text import html2text

from ..exceptions import AuthenticationError, ServerConnectionError, ValidationError
from ..models.account import EmailProvider

EMAIL_PATTERN = r"<[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}>"

__all__ = ["IMAPClient"]

EMAIL_PROVIDERS = {
    EmailProvider.GMAIL: {
        "email_domains": ["gmail.com", "googlemail.com"],
        "server_domains": ["gmail.com"],
        "folders": {
            "inbox": "INBOX",
            "trash": '"[Gmail]/Trash"',
            "spam": '"[Gmail]/Spam"',
            "sent": '"[Gmail]/Sent Mail"',
            "drafts": '"[Gmail]/Drafts"',
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
    def __init__(
        self,
        imap_server: str,
        email_address: str,
        password: str,
        imap_port: int = 993,
        provider: str | EmailProvider | None = None,
        **kwargs,
    ) -> None:
        # Convert string provider to EmailProvider enum
        if isinstance(provider, str):
            provider = EmailProvider(provider)

        # Auto-detect provider if not provided
        if not provider:
            provider = self._detect_provider(imap_server, email_address)

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
        self.config = EMAIL_PROVIDERS.get(provider, {})
        if not self.config:
            # For custom providers, create minimal config
            self.config = {
                "folders": {
                    "inbox": "INBOX",
                    "trash": "Trash",
                    "spam": "Spam",
                    "sent": "Sent",
                    "drafts": "Drafts",
                },
            }

    @staticmethod
    def _detect_provider(imap_server: str, email_address: str) -> EmailProvider:
        """Detect email provider from server address or email domain."""
        # First try to detect by server address
        for provider, config in EMAIL_PROVIDERS.items():
            if any(imap_server.endswith(domain) for domain in config["server_domains"]):
                return provider

        # Fall back to email domain detection
        if "@" in email_address:
            email_domain = email_address.rpartition("@")[-1].lower()
            for provider, config in EMAIL_PROVIDERS.items():
                if email_domain in config["email_domains"]:
                    return provider

        # Default to custom if no match found
        return EmailProvider.CUSTOM

    @staticmethod
    def _parse_date_to_iso(date_str: str) -> str:
        """Parse MIME date format to ISO timestamp."""
        if not date_str:
            return ""

        try:
            # Parse the MIME date using email.utils
            dt = parsedate_to_datetime(date_str)
            # Convert to ISO format
            return dt.isoformat()
        except (ValueError, TypeError):
            # If parsing fails, return original string
            return date_str

    def logout(self) -> None:
        self._imap.logout()

    def _select(self, folder: str = "INBOX", readonly: bool = True) -> None:
        try:
            self._imap.select(folder, readonly=readonly)
        except IMAP4.error:
            raise ValidationError(f"Invalid folder: {folder}")

    def list_flags(self, **kwargs) -> list[str]:
        self._select(readonly=False, **kwargs)
        _, flags = self._imap.response("FLAGS")
        self._imap.close()
        return flags[0].decode().strip("()").split()

    def list_email_uids(self, unseen_only: bool = False, **kwargs) -> list[str]:
        self._select(readonly=True, **kwargs)
        status_, res = self._imap.uid("SEARCH", None, "UNSEEN" if unseen_only else "ALL")
        self._imap.close()
        if status_ != "OK":
            raise ValidationError(status_)
        return res[0].decode().split()

    def search_uid(self, message_id: str, **kwargs) -> str:
        self._select(readonly=True, **kwargs)
        status_, res = self._imap.uid("SEARCH", None, f'HEADER Message-ID "{message_id}"')
        self._imap.close()
        if status_ != "OK":
            raise ValidationError(status_)
        return res[0].decode().split()

    def search_uids(self, message_ids: list[str], **kwargs) -> list[str]:
        if len(message_ids) == 0:
            return []
        if len(message_ids) == 1:
            return [self.search_uid(message_ids[0], **kwargs)]
        queries = [f'HEADER Message-ID "{message_id}"' for message_id in message_ids]
        self._select(readonly=True, **kwargs)
        status_, res = self._imap.uid("SEARCH", None, reduce(lambda acc, q: f"OR ({acc}) ({q})", queries))
        self._imap.close()
        if status_ != "OK":
            raise ValidationError(status_)
        return res[0].decode().split()

    def fetch_message(
        self, uid: str, headers_set: set | None = None, include_quoted_body: bool = False, **kwargs
    ) -> dict[str, Any]:
        self._select(readonly=True, **kwargs)
        status_, content = self._imap.uid("FETCH", uid, "(RFC822)")
        self._imap.close()
        if status_ != "OK":
            raise ValidationError(status_)
        message = cast(EmailMessage, message_from_bytes(content[0][1]))
        return {
            "uid": uid,
            "thread_id": resolve_thread_id(message),
            "date": self._parse_date_to_iso(message.get("Date", "")),
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
        self._select(readonly=True, **kwargs)
        if len(uids) == 0:
            return []

        msg_parts = f"(BODY.PEEK[HEADER.FIELDS ({' '.join(tuple(headers_set))})])"
        status_, content = self._imap.uid("FETCH", ",".join(uids), msg_parts.upper())
        self._imap.close()
        if status_ != "OK":
            raise ValidationError(status_)
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
        self._select(readonly=True, **kwargs)
        if len(uids) == 0:
            return []

        msg_parts = "(RFC822)"
        status_, content = self._imap.uid("FETCH", ",".join(uids), msg_parts.upper())
        self._imap.close()
        if status_ != "OK":
            raise ValidationError(status_)
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
                "date": self._parse_date_to_iso(message.get("Date", "")),
                "headers": {
                    "Message-ID" if k.lower() == "message-id" else k: v.strip()
                    for k, v in message.items()
                    if headers_set is None or k in headers_set
                },
                "body": parse_email_parts(message, include_quoted_body=include_quoted_body),
            }
            for uid, message in zip(uids, email_messages, strict=True)
        ]

    def mark_as_read(self, uid: str) -> None:
        """Mark email as read"""
        self._select("INBOX", readonly=False)
        status_, _ = self._imap.uid("STORE", uid, "+FLAGS", "\\Seen")
        if status_ != "OK":
            self._imap.close()
            raise ValidationError(f"Failed to mark message {uid} as read: {status_}")
        self._imap.close()

    def mark_as_unread(self, uid: str) -> None:
        """Mark email as unread"""
        self._select("INBOX", readonly=False)
        status_, _ = self._imap.uid("STORE", uid, "-FLAGS", "\\Seen")
        if status_ != "OK":
            self._imap.close()
            raise ValidationError(f"Failed to mark message {uid} as unread: {status_}")
        self._imap.close()

    def move_to_trash(self, uid: str) -> None:
        """Move email to trash folder"""
        self._select("INBOX", readonly=False)

        # First copy to trash folder
        status_, _ = self._imap.uid("COPY", uid, self.config["folders"]["trash"])
        if status_ != "OK":
            self._imap.close()
            raise ValidationError(f"Failed to copy message {uid} to trash: {status_}")

        # Then mark as deleted
        status_, _ = self._imap.uid("STORE", uid, "+FLAGS", "\\Deleted")
        if status_ != "OK":
            self._imap.close()
            raise ValidationError(f"Failed to mark message {uid} as deleted: {status_}")

        # Finally expunge
        status_, _ = self._imap.expunge()
        if status_ != "OK":
            self._imap.close()
            raise ValidationError(f"Failed to expunge message {uid}: {status_}")

        self._imap.close()

    def delete_email(self, uid: str) -> None:
        """Delete email permanently"""
        self._select("INBOX", readonly=False)

        # Mark as deleted
        status_, _ = self._imap.uid("STORE", uid, "+FLAGS", "\\Deleted")
        if status_ != "OK":
            self._imap.close()
            raise ValidationError(f"Failed to mark message {uid} as deleted: {status_}")

        # Expunge to permanently delete
        status_, _ = self._imap.expunge()
        if status_ != "OK":
            self._imap.close()
            raise ValidationError(f"Failed to expunge message {uid}: {status_}")

        self._imap.close()

    def mark_as_spam(self, uid: str) -> None:
        """Move email to spam folder"""
        self._select("INBOX", readonly=False)

        # First copy to spam folder
        status_, _ = self._imap.uid("COPY", uid, self.config["folders"]["spam"])
        if status_ != "OK":
            self._imap.close()
            raise ValidationError(f"Failed to copy message {uid} to spam folder: {status_}")

        # Then mark as deleted from inbox
        status_, _ = self._imap.uid("STORE", uid, "+FLAGS", "\\Deleted")
        if status_ != "OK":
            self._imap.close()
            raise ValidationError(f"Failed to mark message {uid} as deleted: {status_}")

        # Finally expunge from inbox
        status_, _ = self._imap.expunge()
        if status_ != "OK":
            self._imap.close()
            raise ValidationError(f"Failed to expunge message {uid}: {status_}")

        self._imap.close()


def resolve_thread_id(email_message: EmailMessage | dict[str, str]) -> str | None:
    """Resolve thread ID from email headers"""
    # Clean resolution
    if isinstance(email_message.get("References"), str) and len(email_message.get("References", "").split()) > 0:
        return email_message.get("References", "").split()[0].strip()
    # Failure (missing references)
    if email_message.get("In-Reply-To") is not None:
        return None
    return email_message.get("Message-ID", email_message.get("Message-Id"))


def parse_email_parts(email_message: EmailMessage, include_quoted_body: bool = False) -> dict[str, Any]:
    """Extract plain text body from email"""
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
    empty_line_idx = next((idx for idx, line in enumerate(reversed(lines[:line_index])) if line.strip() == ""), None)
    line_index = line_index if empty_line_idx is None else line_index - empty_line_idx
    return "\r\n".join(lines[:line_index])
