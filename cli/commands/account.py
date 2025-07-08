# Copyright (C) 2025, Relay.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

"""Account management CLI commands."""

import questionary
import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from relay.auth.account import AccountManager
from relay.exceptions import (
    AccountExistsError,
    AccountNotFoundError,
    AuthenticationError,
    ServerConnectionError,
    ValidationError,
)
from relay.models.account import PROVIDER_CONFIGS, AccountCreate, EmailProvider

from ..utils import AliasGroup

console = Console()
app = typer.Typer(help="Account management commands", cls=AliasGroup)


@app.command("add")
def connect_account() -> None:
    """Add a new IMAP account with interactive setup."""
    console.print("[bold blue]Setting up new IMAP account[/bold blue]")

    # Get account name
    name = Prompt.ask("Account name")

    # Get email address
    email = Prompt.ask("Email address")

    # Auto-detect provider or ask for custom
    provider = EmailProvider.CUSTOM
    email_domain = email.rpartition("@")[-1].lower()

    match email_domain:
        case "gmail.com" | "googlemail.com":
            provider = EmailProvider.GMAIL
        case "outlook.com" | "hotmail.com" | "live.com":
            provider = EmailProvider.OUTLOOK
        case "yahoo.com" | "yahoo.co.uk" | "yahoo.ca":
            provider = EmailProvider.YAHOO
        case "icloud.com" | "me.com" | "mac.com":
            provider = EmailProvider.ICLOUD
        case _:
            console.print(f"[yellow]Unknown provider for domain: {email_domain}[/yellow]")
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

            provider = provider_choice

    # Get server settings
    if provider in PROVIDER_CONFIGS:
        imap_server = PROVIDER_CONFIGS[provider]["imap_server"]
        imap_port = PROVIDER_CONFIGS[provider]["imap_port"]
        console.print(f"[green]Using {provider.value} settings: {imap_server}:{imap_port}[/green]")
    else:
        imap_server = Prompt.ask("IMAP server", default="imap.gmail.com")
        imap_port = int(Prompt.ask("IMAP port", default="993"))

    # Get password
    password = Prompt.ask("Password", password=True)

    # Confirm password
    password_confirm = Prompt.ask("Confirm password", password=True)

    if password != password_confirm:
        console.print("[red]Passwords do not match[/red]")
        raise typer.Exit(1)

    # Create account
    try:
        account_data = AccountCreate(
            name=name, email=email, provider=provider, imap_server=imap_server, imap_port=imap_port, password=password
        )

        with console.status("[bold green]Testing connection...", spinner="dots"):
            manager = AccountManager()
            account = manager.add_account(account_data)

        console.print(f"[green]✓ Account '{account.name}' added successfully![/green]")
        console.print(f"[dim]Email: {account.email}[/dim]")
        console.print(f"[dim]Provider: {account.provider.value}[/dim]")
        console.print(f"[dim]Server: {account.imap_server}:{account.imap_port}[/dim]")

    except AccountExistsError as e:
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


@app.command("list | ls")
def list_accounts() -> None:
    """List all configured accounts."""
    try:
        manager = AccountManager()
        accounts = manager.list_accounts()

        if not accounts:
            console.print("[yellow]No accounts configured[/yellow]")
            return

        table = Table(title="Configured Accounts")
        table.add_column("Name", style="cyan")
        table.add_column("Email", style="magenta")
        table.add_column("Provider", style="green")
        table.add_column("Server", style="blue")
        table.add_column("Port", style="yellow")

        for account in accounts:
            table.add_row(
                account.name, account.email, account.provider.value, account.imap_server, str(account.imap_port)
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]✗ Error listing accounts: {e}[/red]")
        raise typer.Exit(1)


@app.command("remove | rm")
def remove_account_connection(name: str) -> None:
    """Remove an account."""
    try:
        manager = AccountManager()

        # Confirm deletion
        account = manager.get_account(name)
        if not typer.confirm(f"Remove account '{name}' ({account.email})?"):
            console.print("[yellow]Cancelled[/yellow]")
            return

        manager.remove_account(name)
        console.print(f"[green]✓ Account '{name}' removed[/green]")

    except AccountNotFoundError as e:
        console.print(f"[red]✗ {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗ Error removing account: {e}[/red]")
        raise typer.Exit(1)


@app.command("test")
def test_account_connection(name: str) -> None:
    """Test connection to an account."""
    try:
        manager = AccountManager()
        with console.status(f"[bold green]Testing connection to '{name}'...", spinner="dots"):
            manager.test_account(name)
        console.print(f"[green]✓ Connection to '{name}' successful[/green]")

    except AccountNotFoundError as e:
        console.print(f"[red]✗ {e}[/red]")
        raise typer.Exit(1)
    except AuthenticationError as e:
        console.print(f"[red]✗ {e}[/red]")
        raise typer.Exit(1)
    except ServerConnectionError as e:
        console.print(f"[red]✗ {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗ Connection test failed: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
