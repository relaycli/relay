# Copyright (C) 2025, Relay.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

"""Messages CLI commands."""

from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from relay.auth.account import AccountManager
from relay.exceptions import AccountNotFoundError, AuthenticationError, ServerConnectionError
from relay.models.message import MessageSummary

console = Console()
app = typer.Typer(help="Email message commands")


@app.command()
def list(
    account: Annotated[str, typer.Option("--account", "-a", help="Account name to use")] = "",
    count: Annotated[int, typer.Option("--count", "-c", help="Number of messages to fetch")] = 20,
    unread_only: Annotated[bool, typer.Option("--unread", "-u", help="Show only unread messages")] = False,
    demo: Annotated[bool, typer.Option("--demo", help="Show demo data instead of real emails")] = False,
):
    """List recent emails from specified account."""
    # Demo mode - show sample data
    if demo:
        sample_messages = [
            MessageSummary(
                uid="1001",
                subject="Welcome to Relay CLI",
                sender="noreply@relay.com",
                date="Mon, 10 Jan 2025 10:30:00",
                snippet="Thank you for installing Relay CLI! This is your first step towards efficient email management...",
            ),
            MessageSummary(
                uid="1002",
                subject="Weekly Newsletter - Tech Updates",
                sender="newsletter@techworld.com",
                date="Sun, 09 Jan 2025 08:15:00",
                snippet="This week in tech: AI developments, new frameworks, and industry insights that matter to developers...",
            ),
            MessageSummary(
                uid="1003",
                subject="Meeting Reminder: Project Sync",
                sender="alice@company.com",
                date="Fri, 07 Jan 2025 16:45:00",
                snippet="Hi team, just a reminder about tomorrow's project sync meeting at 10 AM. Please review the agenda...",
            ),
            MessageSummary(
                uid="1004",
                subject="Your invoice #2025-001",
                sender="billing@service.com",
                date="Thu, 06 Jan 2025 14:20:00",
                snippet="Your monthly invoice is ready. Total amount: $29.99. Payment is due within 30 days...",
            ),
        ]

        # Create table
        table = Table(title="Messages (Demo Mode)")
        table.add_column("Date", style="cyan", width=20)
        table.add_column("From", style="green", width=25)
        table.add_column("Subject", style="bold", width=40)
        table.add_column("Snippet", style="dim", width=50)

        for msg in sample_messages:
            # Format date (extract date part if it's a full date string)
            date_str = msg.date
            if len(date_str) > 20:
                parts = date_str.split()
                if len(parts) >= 4:
                    date_str = " ".join(parts[:4])

            # Truncate fields for display
            sender = msg.sender[:23] + "..." if len(msg.sender) > 25 else msg.sender
            subject = msg.subject[:37] + "..." if len(msg.subject) > 40 else msg.subject
            snippet = msg.snippet[:47] + "..." if len(msg.snippet) > 50 else msg.snippet

            table.add_row(date_str, sender, subject, snippet)

        console.print(table)
        console.print(f"[dim]Showing {len(sample_messages)} demo messages[/dim]")
        return

    try:
        # Get account manager
        manager = AccountManager()

        # If no account specified, get first available account
        if not account:
            accounts = manager.list_accounts()
            if not accounts:
                console.print("[red]✗ No accounts configured. Use 'relay account add' to add an account.[/red]")
                raise typer.Exit(1)
            account = accounts[0].name
            console.print(f"[dim]Using account: {account}[/dim]")

        # Get account info
        account_info = manager.get_account(account)

        # Show spinner while connecting and fetching emails
        with console.status(f"[bold green]Connecting to {account_info.email}...", spinner="dots"):
            # Create IMAP client
            client = manager.get_imap_client(account)

        with console.status(
            f"[bold green]Fetching {count} {'unread ' if unread_only else ''}messages...", spinner="dots"
        ):
            # Get email UIDs
            uids = client.list_email_uids(unseen_only=unread_only)

            # Limit to requested count
            uids = uids[:count]

            if not uids:
                client.logout()
                console.print(f"[yellow]No {'unread ' if unread_only else ''}messages found[/yellow]")
                return

            # Fetch messages
            messages = client.fetch_messages(uids, include_quoted_body=False)
            client.logout()

        # Convert to summary objects
        message_summaries = [MessageSummary.from_message_data(msg) for msg in messages]

        # Create table
        table = Table(title=f"Messages from {account_info.email}")
        table.add_column("Date", style="cyan", width=20)
        table.add_column("From", style="green", width=25)
        table.add_column("Subject", style="bold", width=40)
        table.add_column("Snippet", style="dim", width=50)

        for msg in message_summaries:
            # Format date (extract date part if it's a full date string)
            date_str = msg.date
            if len(date_str) > 20:
                # Try to extract just the date part from longer date strings
                parts = date_str.split()
                if len(parts) >= 4:
                    date_str = " ".join(parts[:4])  # Take first 4 parts (day, date, month, year)

            # Truncate fields for display
            sender = msg.sender[:23] + "..." if len(msg.sender) > 25 else msg.sender
            subject = msg.subject[:37] + "..." if len(msg.subject) > 40 else msg.subject
            snippet = msg.snippet[:47] + "..." if len(msg.snippet) > 50 else msg.snippet

            table.add_row(date_str, sender, subject, snippet)

        console.print(table)
        console.print(
            f"[dim]Showing {len(message_summaries)} of {len(uids)} {'unread ' if unread_only else ''}messages[/dim]"
        )

    except AccountNotFoundError as e:
        console.print(f"[red]✗ {e}[/red]")
        console.print("[dim]Use 'relay account list' to see available accounts[/dim]")
        raise typer.Exit(1)
    except AuthenticationError as e:
        console.print(f"[red]✗ {e}[/red]")
        raise typer.Exit(1)
    except ServerConnectionError as e:
        console.print(f"[red]✗ {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗ Error fetching messages: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
