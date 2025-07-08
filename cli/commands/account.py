# Copyright (C) 2025, Relay.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

"""Account management CLI commands."""

from typing import Callable

import questionary
import typer
from rich.console import Console
from rich.prompt import Prompt

from relay.auth.account import AccountManager
from relay.exceptions import (
    AccountExistsError,
    AccountNotFoundError,
    AuthenticationError,
    ServerConnectionError,
    ValidationError,
)
from relay.models.account import PROVIDER_CONFIGS, AccountCreate, EmailProvider
from relay.providers.imap import IMAPClient

from ..utils import AliasGroup, create_accounts_table

console = Console()
app = typer.Typer(help="Account management commands", cls=AliasGroup)


# --- Helper Functions for DRY Code ---


def _handle_account_errors(func: Callable) -> Callable:
    """Decorator to handle common account management errors."""
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AccountExistsError as e:
            console.print(f"[red]✗ {e}[/red]")
            raise typer.Exit(1)
        except AccountNotFoundError as e:
            console.print(f"[red]✗ {e}[/red]")
            raise typer.Exit(1)
        except AuthenticationError as e:
            console.print(f"[red]✗ {e}[/red]")
            raise typer.Exit(1)
        except ServerConnectionError as e:
            console.print(f"[red]✗ {e}[/red]")
            raise typer.Exit(1)
        except ValidationError as e:
            console.print(f"[red]✗ {e}[/red]")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]✗ Unexpected error: {e}[/red]")
            raise typer.Exit(1)

    return wrapper


def _get_account_manager() -> AccountManager:
    """Get account manager instance."""
    return AccountManager()


def _detect_provider_from_domain(email_domain: str) -> EmailProvider:
    """Detect provider from email domain using centralized logic."""
    # Use the centralized detection logic from IMAPClient
    return IMAPClient._detect_provider("", f"user@{email_domain}")


def _get_provider_choice() -> EmailProvider:
    """Get provider choice from user via questionary dropdown."""
    provider_choices = [
        questionary.Choice("Gmail", EmailProvider.GMAIL),
        questionary.Choice("Outlook (Hotmail/Live)", EmailProvider.OUTLOOK),
        questionary.Choice("Yahoo Mail", EmailProvider.YAHOO),
        questionary.Choice("iCloud Mail", EmailProvider.ICLOUD),
        questionary.Choice("Custom IMAP Server", EmailProvider.CUSTOM),
    ]
    provider_choice = questionary.select(
        "Select your email provider:",
        choices=provider_choices,
        default=EmailProvider.CUSTOM,
    ).ask()

    if provider_choice is None:
        console.print("[yellow]Cancelled[/yellow]")
        raise typer.Exit(1)

    return provider_choice


def _get_server_settings(provider: EmailProvider) -> tuple[str, int]:
    """Get server settings for provider or prompt user."""
    if provider in PROVIDER_CONFIGS:
        imap_server = PROVIDER_CONFIGS[provider]["imap_server"]
        imap_port = PROVIDER_CONFIGS[provider]["imap_port"]
        console.print(f"[green]Using {provider.value} settings: {imap_server}:{imap_port}[/green]")
        return imap_server, imap_port
    imap_server = Prompt.ask("IMAP server", default="imap.gmail.com")
    imap_port = int(Prompt.ask("IMAP port", default="993"))
    return imap_server, imap_port


# --- Command Functions ---


@app.command("add")
@_handle_account_errors
def connect_account() -> None:
    """Add a new IMAP account with interactive setup."""
    console.print("[bold blue]Setting up new IMAP account[/bold blue]")

    # Get account name
    name = Prompt.ask("Account name")

    # Get email address
    email = Prompt.ask("Email address")

    # Auto-detect provider or ask for custom
    email_domain = email.rpartition("@")[-1].lower()
    provider = _detect_provider_from_domain(email_domain)

    if provider == EmailProvider.CUSTOM:
        console.print(f"[yellow]Unknown provider for domain: {email_domain}[/yellow]")
        provider = _get_provider_choice()

    # Get server settings
    imap_server, imap_port = _get_server_settings(provider)

    # Get password
    password = Prompt.ask("Password", password=True)

    # Confirm password
    password_confirm = Prompt.ask("Confirm password", password=True)

    if password != password_confirm:
        console.print("[red]Passwords do not match[/red]")
        raise typer.Exit(1)

    # Create and add account
    account_data = AccountCreate(
        name=name, email=email, provider=provider, imap_server=imap_server, imap_port=imap_port, password=password
    )

    with console.status("[bold green]Testing connection...", spinner="dots"):
        manager = _get_account_manager()
        account = manager.add_account(account_data)

    console.print(f"[green]✓ Account '{account.name}' added successfully![/green]")
    console.print(f"[dim]Email: {account.email}[/dim]")
    console.print(f"[dim]Provider: {account.provider.value}[/dim]")
    console.print(f"[dim]Server: {account.imap_server}:{account.imap_port}[/dim]")


@app.command("list | ls")
@_handle_account_errors
def list_accounts() -> None:
    """List all configured accounts."""
    manager = _get_account_manager()
    accounts = manager.list_accounts()

    if not accounts:
        console.print("[yellow]No accounts configured[/yellow]")
        return

    table = create_accounts_table()
    for account in accounts:
        table.add_row(account.name, account.email, account.provider.value, account.imap_server, str(account.imap_port))

    console.print(table)


@app.command("remove | rm")
@_handle_account_errors
def remove_account_connection(name: str) -> None:
    """Remove an account."""
    manager = _get_account_manager()

    # Confirm deletion
    account = manager.get_account(name)
    if not typer.confirm(f"Remove account '{name}' ({account.email})?"):
        console.print("[yellow]Cancelled[/yellow]")
        return

    manager.remove_account(name)
    console.print(f"[green]✓ Account '{name}' removed[/green]")


@app.command("test")
@_handle_account_errors
def test_account_connection(name: str) -> None:
    """Test connection to an account."""
    manager = _get_account_manager()
    with console.status(f"[bold green]Testing connection to '{name}'...", spinner="dots"):
        manager.test_account(name)
    console.print(f"[green]✓ Connection to '{name}' successful[/green]")


if __name__ == "__main__":
    app()
