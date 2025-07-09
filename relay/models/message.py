# Copyright (C) 2025, Relay.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

"""Message models for the Relay library."""

from typing import Any

from pydantic import BaseModel, Field

__all__ = ["MessageInfo", "MessageSummary"]


class MessageInfo(BaseModel):
    """Complete message information."""

    uid: str = Field(..., description="Message UID")
    subject: str = Field(default="", description="Message subject")
    sender: str = Field(default="", description="Sender email address")
    date: str = Field(default="", description="Message date")
    thread_id: str | None = Field(default=None, description="Thread ID")
    headers: dict[str, Any] = Field(default_factory=dict, description="Message headers")
    body: dict[str, Any] = Field(default_factory=dict, description="Message body")


class MessageSummary(BaseModel):
    """Summary message information for list displays."""

    uid: str = Field(..., description="Message UID")
    subject: str = Field(default="", description="Message subject")
    sender: str = Field(default="", description="Sender email address")
    date: str = Field(default="", description="Message date")
    snippet: str = Field(default="", description="Truncated body snippet")

    @classmethod
    def from_message_data(cls, message_data: dict[str, Any]) -> "MessageSummary":
        """Create MessageSummary from raw IMAP message data.

        Args:
            message_data: Dictionary of email message data

        Returns:
            MessageSummary
        """
        headers = message_data.get("headers", {})
        body = message_data.get("body", {})

        # Extract sender from From header
        sender = headers.get("From", "")
        if "<" in sender and ">" in sender:
            # Extract email from "Name <email@domain.com>" format
            sender = sender.split("<")[-1].split(">")[0]

        # Create snippet from plain text body
        text_plain = body.get("text_plain", "")
        snippet = ""
        if text_plain:
            # Take first 100 characters, remove newlines
            snippet = text_plain.replace("\n", " ").replace("\r", "").strip()[:100]
            if len(text_plain) > 100:
                snippet += "..."

        return cls(
            uid=message_data.get("uid", ""),
            subject=message_data.get("subject", ""),
            sender=sender,
            date=message_data.get("date", ""),
            snippet=snippet,
        )
