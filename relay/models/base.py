# Copyright (C) 2025, Relay.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

"""Base enums for the Relay library."""

from enum import StrEnum

__all__ = ["EmailProvider"]


class EmailProvider(StrEnum):
    """Supported email providers."""

    GMAIL = "gmail"
    OUTLOOK = "outlook"
    YAHOO = "yahoo"
    ICLOUD = "icloud"
    CUSTOM = "custom"
