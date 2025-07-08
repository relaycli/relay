# Copyright (C) 2025, Relay.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

"""Messages CLI commands."""

from datetime import datetime
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from relay.auth.account import AccountManager
from relay.exceptions import AccountNotFoundError, AuthenticationError, ServerConnectionError
from relay.models.message import MessageSummary

from ..utils import AliasGroup

console = Console()
app = typer.Typer(help="Email message commands", cls=AliasGroup)


def format_timestamp_to_utc(timestamp_str: str) -> str:
    """Convert ISO timestamp to UTC for display."""
    if not timestamp_str or "T" not in timestamp_str:
        return timestamp_str

    try:
        # Parse ISO format with timezone
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        # Convert to UTC
        dt_utc = dt.utctimetuple()
        # Format as readable UTC time
        return f"{dt_utc.tm_year:04d}-{dt_utc.tm_mon:02d}-{dt_utc.tm_mday:02d} {dt_utc.tm_hour:02d}:{dt_utc.tm_min:02d}:{dt_utc.tm_sec:02d} UTC"
    except (ValueError, AttributeError):
        # Fallback to original string if parsing fails
        return timestamp_str


@app.command("list | ls")
def list_messages(
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
                date="2025-01-10T10:30:00+00:00",
                snippet="Thank you for installing Relay CLI! This is your first step towards efficient email management...",
            ),
            MessageSummary(
                uid="1002",
                subject="Weekly Newsletter - Tech Updates",
                sender="newsletter@techworld.com",
                date="2025-01-09T08:15:00+00:00",
                snippet="This week in tech: AI developments, new frameworks, and industry insights that matter to developers...",
            ),
            MessageSummary(
                uid="1003",
                subject="Meeting Reminder: Project Sync",
                sender="alice@company.com",
                date="2025-01-07T16:45:00+00:00",
                snippet="Hi team, just a reminder about tomorrow's project sync meeting at 10 AM. Please review the agenda...",
            ),
            MessageSummary(
                uid="1004",
                subject="Your invoice #2025-001",
                sender="billing@service.com",
                date="2025-01-06T14:20:00+00:00",
                snippet="Your monthly invoice is ready. Total amount: $29.99. Payment is due within 30 days...",
            ),
        ]

        # Create table - let high priority columns auto-size, limit truncatable ones
        table = Table(title="Messages (Demo Mode)")
        table.add_column("UID", style="cyan", no_wrap=True)
        table.add_column("Timestamp", style="blue", no_wrap=True, width=24)
        table.add_column("From", style="green", no_wrap=True)
        table.add_column("Subject", style="bold", max_width=30)
        table.add_column("Snippet", style="dim", max_width=25)

        for msg in sample_messages:
            # Convert timestamp to UTC for display
            timestamp_str = format_timestamp_to_utc(msg.date)

            # Truncate only subject and snippet - let UID, timestamp, from display fully
            subject = msg.subject[:27] + "..." if len(msg.subject) > 30 else msg.subject
            snippet = msg.snippet[:22] + "..." if len(msg.snippet) > 25 else msg.snippet

            table.add_row(msg.uid, timestamp_str, msg.sender, subject, snippet)

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

        # Create table - let high priority columns auto-size, limit truncatable ones
        table = Table(title=f"Messages from {account_info.email}")
        table.add_column("UID", style="cyan", no_wrap=True)
        table.add_column("Timestamp", style="blue", no_wrap=True, width=24)
        table.add_column("From", style="green", no_wrap=True)
        table.add_column("Subject", style="bold", max_width=30)
        table.add_column("Snippet", style="dim", max_width=25)

        for msg in message_summaries:
            # Convert timestamp to UTC for display
            timestamp_str = format_timestamp_to_utc(msg.date)

            # Truncate only subject and snippet - let UID, timestamp, from display fully
            subject = msg.subject[:27] + "..." if len(msg.subject) > 30 else msg.subject
            snippet = msg.snippet[:22] + "..." if len(msg.snippet) > 25 else msg.snippet

            table.add_row(msg.uid, timestamp_str, msg.sender, subject, snippet)

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


@app.command("read | cat")
def read_message(
    uid: Annotated[str, typer.Argument(help="Message UID to read")],
    account: Annotated[str, typer.Option("--account", "-a", help="Account name to use")] = "",
):
    """Read a single email message by UID."""
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

        # Show spinner while connecting and fetching message
        with console.status(f"[bold green]Connecting to {account_info.email}...", spinner="dots"):
            # Create IMAP client
            client = manager.get_imap_client(account)

        with console.status(f"[bold green]Fetching message {uid}...", spinner="dots"):
            # Fetch the specific message
            message = client.fetch_message(uid, include_quoted_body=False)
            client.logout()

        # Display message details
        console.print("\n[bold blue]Message Details[/bold blue]")
        console.print(f"[cyan]UID:[/cyan] {message['uid']}")
        console.print(f"[cyan]Timestamp:[/cyan] {format_timestamp_to_utc(message.get('date', 'N/A'))}")
        console.print(f"[cyan]Subject:[/cyan] {message.get('subject', 'N/A')}")

        # Extract sender from headers
        sender = message.get("headers", {}).get("From", "N/A")
        console.print(f"[cyan]From:[/cyan] {sender}")

        # Extract CC and BCC from headers
        cc = message.get("headers", {}).get("CC", message.get("headers", {}).get("Cc", "N/A"))
        bcc = message.get("headers", {}).get("BCC", message.get("headers", {}).get("Bcc", "N/A"))
        console.print(f"[cyan]CC:[/cyan] {cc}")
        console.print(f"[cyan]BCC:[/cyan] {bcc}")

        # Display body
        body = message.get("body", {})
        text_body = body.get("text_plain", "No plain text body available")
        console.print("\n[bold green]Message Body:[/bold green]")
        console.print(f"[white]{text_body}[/white]")

        # Display attachments
        attachments = body.get("attachments", [])
        if attachments:
            console.print(f"\n[bold yellow]Attachments ({len(attachments)}):[/bold yellow]")
            for i, attachment in enumerate(attachments, 1):
                filename = attachment.get("filename", f"attachment_{i}")
                content_type = attachment.get("content_type", "unknown")
                size = attachment.get("size", 0)
                console.print(f"  {i}. [cyan]{filename}[/cyan] ({content_type}, {size} bytes)")
        else:
            console.print("\n[dim]No attachments[/dim]")

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
        console.print(f"[red]✗ Error fetching message: {e}[/red]")
        raise typer.Exit(1)


@app.command("search | find | grep")
def search_messages(
    query: Annotated[str, typer.Argument(help="Search query")],
    account: Annotated[str, typer.Option("--account", "-a", help="Account name to use")] = "",
    count: Annotated[int, typer.Option("--count", "-c", help="Number of messages to search")] = 100,
):
    """Search for messages containing the specified query."""
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

        # Show spinner while connecting and searching
        with console.status(f"[bold green]Connecting to {account_info.email}...", spinner="dots"):
            # Create IMAP client
            client = manager.get_imap_client(account)

        with console.status(f"[bold green]Searching for '{query}'...", spinner="dots"):
            # Get recent messages to search through
            uids = client.list_email_uids(unseen_only=False)

            # Limit search scope
            search_uids = uids[:count]

            if not search_uids:
                client.logout()
                console.print("[yellow]No messages found to search[/yellow]")
                return

            # Fetch messages and search through them
            messages = client.fetch_messages(search_uids, include_quoted_body=False)
            client.logout()

        # Filter messages that contain the query
        matching_messages = []
        query_lower = query.lower()

        for msg in messages:
            # Search in subject, sender, and body (with null checks)
            subject = (msg.get("subject") or "").lower()
            sender = (msg.get("headers", {}).get("From") or "").lower()
            body_text = (msg.get("body", {}).get("text_plain") or "").lower()

            if query_lower in subject or query_lower in sender or query_lower in body_text:
                matching_messages.append(msg)

        if not matching_messages:
            console.print(f"[yellow]No messages found containing '{query}'[/yellow]")
            return

        # Convert to summary objects
        message_summaries = [MessageSummary.from_message_data(msg) for msg in matching_messages]

        # Create table - same format as list command
        table = Table(title=f"Search Results for '{query}' in {account_info.email}")
        table.add_column("UID", style="cyan", no_wrap=True)
        table.add_column("Timestamp", style="blue", no_wrap=True, width=24)
        table.add_column("From", style="green", no_wrap=True)
        table.add_column("Subject", style="bold", max_width=30)
        table.add_column("Snippet", style="dim", max_width=25)

        for msg in message_summaries:
            # Convert timestamp to UTC for display
            timestamp_str = format_timestamp_to_utc(msg.date)

            # Truncate only subject and snippet - let UID, timestamp, from display fully
            subject = msg.subject[:27] + "..." if len(msg.subject) > 30 else msg.subject
            snippet = msg.snippet[:22] + "..." if len(msg.snippet) > 25 else msg.snippet

            table.add_row(msg.uid, timestamp_str, msg.sender, subject, snippet)

        console.print(table)
        console.print(
            f"[dim]Found {len(matching_messages)} messages containing '{query}' (searched {len(search_uids)} messages)[/dim]"
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
        console.print(f"[red]✗ Error searching messages: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
