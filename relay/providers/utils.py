# Copyright (C) 2025, Relay.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.


from ..models.base import EmailProvider

__all__ = ["EMAIL_TO_PROVIDER", "IMAP_TO_PROVIDER", "PROVIDER_INFO", "SMTP_TO_PROVIDER"]


PROVIDER_DOMAINS = {
    EmailProvider.GMAIL: ["gmail.com", "googlemail.com"],
    EmailProvider.OUTLOOK: ["outlook.com", "hotmail.com", "hotmail.fr", "live.com"],
    EmailProvider.YAHOO: ["yahoo.com", "yahoo.co.uk", "yahoo.ca"],
    EmailProvider.ICLOUD: ["icloud.com", "me.com", "mac.com"],
}

EMAIL_TO_PROVIDER: dict[str, EmailProvider] = {
    domain: provider for provider, domains in PROVIDER_DOMAINS.items() for domain in domains
}


PROVIDER_INFO = {
    # https://support.google.com/a/answer/9003945
    EmailProvider.GMAIL: {
        "imap": {
            "server": "imap.gmail.com",
            "port": 993,
        },
        "smtp": {
            "server": "smtp.gmail.com",
            "port": 465,
        },
        "folders": {
            "inbox": "INBOX",
            "trash": "[Gmail]/Trash",
            "spam": "[Gmail]/Spam",
            "sent": "[Gmail]/Sent Mail",
            "drafts": "[Gmail]/Drafts",
        },
    },
    # https://support.microsoft.com/en-us/office/pop-imap-and-smtp-settings-for-outlook-com-d088b986-291d-42b8-9564-9c414e2aa040
    EmailProvider.OUTLOOK: {
        "imap": {
            "server": "outlook.office365.com",
            "port": 993,
        },
        "smtp": {
            "server": "smtp-mail.outlook.com",
            "port": 465,
        },
        "folders": {
            "inbox": "INBOX",
            "trash": "Deleted Items",
            "spam": "Junk Email",
            "sent": "Sent Items",
            "drafts": "Drafts",
        },
    },
    # https://help.yahoo.com/kb/SLN4075.html
    EmailProvider.YAHOO: {
        "imap": {
            "server": "imap.mail.yahoo.com",
            "port": 993,
        },
        "smtp": {
            "server": "smtp.mail.yahoo.com",
            "port": 465,
        },
        "folders": {"inbox": "INBOX", "trash": "Trash", "spam": "Bulk Mail", "sent": "Sent", "drafts": "Draft"},
    },
    # https://support.apple.com/en-us/102525
    EmailProvider.ICLOUD: {
        "imap": {
            "server": "imap.mail.me.com",
            "port": 993,
        },
        "smtp": {
            "server": "smtp.mail.me.com",
            "port": 465,
        },
        "folders": {
            "inbox": "INBOX",
            "trash": "Deleted Messages",
            "spam": "Junk",
            "sent": "Sent Messages",
            "drafts": "Drafts",
        },
    },
    EmailProvider.CUSTOM: {
        "folders": {
            "inbox": "INBOX",
            "trash": "Trash",
            "spam": "Junk",
            "sent": "Sent",
            "drafts": "Drafts",
        },
    },
}

IMAP_TO_PROVIDER: dict[str, EmailProvider] = {
    config["imap"]["server"]: provider for provider, config in PROVIDER_INFO.items() if provider != EmailProvider.CUSTOM
}
SMTP_TO_PROVIDER: dict[str, EmailProvider] = {
    config["smtp"]["server"]: provider for provider, config in PROVIDER_INFO.items() if provider != EmailProvider.CUSTOM
}
