# Copyright (C) 2025, Relay.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

"""Account management CLI commands."""

import functools
from collections.abc import Callable
from typing import Annotated

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
from relay.providers.utils import resolve_provider

from ..utils import AliasGroup, create_accounts_table

console = Console()
app = typer.Typer(help="Account management commands", cls=AliasGroup)


# --- Helper Functions for DRY Code ---


def _handle_account_errors(func: Callable) -> Callable:
    """Decorate function to handle common account management errors."""

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


# --- Command Functions ---


@app.command("add")
@_handle_account_errors
def connect_account(
    name: Annotated[str | None, typer.Option("--name", "-n", help="Account name")] = None,
    email: Annotated[str | None, typer.Option("--email", "-e", help="Email address")] = None,
    provider: Annotated[EmailProvider | None, typer.Option("--provider", "-p", help="Email provider")] = None,
    imap_server: Annotated[
        str | None, typer.Option("--imap-server", help="IMAP server address for custom providers")
    ] = None,
    imap_port: Annotated[int | None, typer.Option("--imap-port", help="IMAP port for custom providers")] = None,
) -> None:
    """Add a new IMAP account with interactive setup."""
    console.print("[bold blue]Setting up new IMAP account[/bold blue]")

    # Get account name
    name = name or Prompt.ask("Account name")

    # Get email address
    email = email or Prompt.ask("Email address")

    # Auto-detect provider or ask for custom
    final_provider = provider
    if not final_provider:
        email_domain = email.rpartition("@")[-1].lower()
        final_provider = resolve_provider("", f"user@{email_domain}")
        if final_provider == EmailProvider.CUSTOM:
            console.print(f"[yellow]Unknown provider for domain: {email_domain}[/yellow]")
            final_provider = _get_provider_choice()

    # Get server settings
    final_imap_server = imap_server
    if imap_server is None:
        if final_provider in PROVIDER_CONFIGS:
            final_imap_server = PROVIDER_CONFIGS[final_provider]["imap_server"]
            console.print(f"[green]Using {final_provider.value} settings for IMAP server: {final_imap_server}[/green]")
        else:
            final_imap_server = Prompt.ask("IMAP server", default="imap.gmail.com")

    final_imap_port = imap_port
    if imap_port is None:
        if final_provider in PROVIDER_CONFIGS:
            final_imap_port = PROVIDER_CONFIGS[final_provider]["imap_port"]
            console.print(f"[green]Using {final_provider.value} settings for IMAP port: {final_imap_port}[/green]")
        else:
            final_imap_port = int(Prompt.ask("IMAP port", default="993"))

    # Get password
    password = Prompt.ask("Password", password=True)

    # Confirm password
    password_confirm = Prompt.ask("Confirm password", password=True)

    if password != password_confirm:
        console.print("[red]Passwords do not match[/red]")
        raise typer.Exit(1)

    # Create and add account
    account_data = AccountCreate(
        name=name,
        email=email,
        provider=final_provider,
        imap_server=final_imap_server,
        imap_port=final_imap_port,
        password=password,
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
def remove_account_connection(
    name: str,
    force: Annotated[bool, typer.Option("--force", "-f", "-y", help="Force removal without confirmation")] = False,
) -> None:
    """Remove an account."""
    manager = _get_account_manager()

    # Confirm deletion
    account = manager.get_account(name)
    if not force and not typer.confirm(f"Remove account '{name}' ({account.email})?"):
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
