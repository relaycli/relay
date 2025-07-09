# Copyright (C) 2025, Relay.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.


from ..models.base import EmailProvider

__all__ = ["resolve_provider"]

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


def resolve_provider(server: str, email_address: str) -> EmailProvider:
    """Detect email provider from server address or email domain.

    Args:
        server: Server address
        email_address: Email address

    Returns:
        Email provider
    """
    # First try to detect by server address
    for provider, config in EMAIL_PROVIDERS.items():
        if any(server.endswith(domain) for domain in config["server_domains"]):
            return provider

    # Fall back to email domain detection
    if "@" in email_address:
        email_domain = email_address.rpartition("@")[-1].lower()
        for provider, config in EMAIL_PROVIDERS.items():
            if email_domain in config["email_domains"]:
                return provider

    # Default to custom if no match found
    return EmailProvider.CUSTOM
