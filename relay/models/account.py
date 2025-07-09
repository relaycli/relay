# Copyright (C) 2025, Relay.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

"""Account models for the Relay library."""

from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, field_validator

from ..providers.utils import resolve_provider
from .base import EmailProvider

__all__ = ["Account", "AccountCreate", "AccountInfo"]


# Common IMAP server configurations
PROVIDER_CONFIGS = {
    EmailProvider.GMAIL: {"imap_server": "imap.gmail.com", "imap_port": 993},
    EmailProvider.OUTLOOK: {"imap_server": "outlook.office365.com", "imap_port": 993},
    EmailProvider.YAHOO: {"imap_server": "imap.mail.yahoo.com", "imap_port": 993},
    EmailProvider.ICLOUD: {"imap_server": "imap.mail.me.com", "imap_port": 993},
}


class AccountBase(BaseModel):
    """Base account model with common fields."""

    name: Annotated[str, Field(min_length=1, max_length=50, description="User-defined account name")]
    email: Annotated[EmailStr, Field(description="Email address")]
    provider: Annotated[EmailProvider, Field(description="Email provider")]
    imap_server: Annotated[str, Field(description="IMAP server address")]
    imap_port: Annotated[int, Field(ge=1, le=65535, description="IMAP port")] = 993

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.replace("-", "").replace("_", "").replace(".", "").isalnum():
            raise ValueError("Account name can only contain letters, numbers, hyphens, underscores, and dots")
        return v


class AccountCreate(AccountBase):
    """Model for creating a new account."""

    password: str = Field(..., min_length=1, description="Account password")

    def __init__(self, **data) -> None:
        """Initialize with auto-detection of provider-specific settings."""
        # Auto-detect provider from email if not set
        if "provider" not in data or data["provider"] == "custom":
            email = data.get("email", "")
            data["provider"] = resolve_provider("", email)

        # Auto-fill server settings based on provider
        provider = data.get("provider", EmailProvider.CUSTOM)
        if isinstance(provider, str):
            provider = EmailProvider(provider)

        if provider in PROVIDER_CONFIGS and not data.get("imap_server"):
            data["imap_server"] = PROVIDER_CONFIGS[provider]["imap_server"]
        if provider in PROVIDER_CONFIGS and not data.get("imap_port"):
            data["imap_port"] = PROVIDER_CONFIGS[provider]["imap_port"]

        super().__init__(**data)


class Account(AccountBase):
    """Stored account model with encrypted password."""

    encrypted_password: bytes = Field(..., description="Fernet-encrypted password")

    model_config = {"arbitrary_types_allowed": True}


class AccountInfo(AccountBase):
    """Account information model without sensitive data."""
