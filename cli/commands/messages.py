# Copyright (C) 2025, Relay.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

"""Messages CLI commands."""

import functools
from collections.abc import Callable
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.table import Table

from relay.auth.account import AccountManager
from relay.exceptions import AccountNotFoundError, AuthenticationError, ServerConnectionError, ValidationError
from relay.models.message import MessageSummary

from ..utils import AliasGroup, create_messages_table

console = Console()
app = typer.Typer(help="Email message commands", cls=AliasGroup)


def format_timestamp_to_utc(timestamp_str: str) -> str:
    """Convert ISO timestamp to UTC for display."""
    # Parse ISO format with timezone
    dt = datetime.fromisoformat(timestamp_str)
    # Convert to UTC and format
    return dt.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")


# --- Helper Functions for DRY Code ---


def _get_account_manager_and_client(account: str) -> tuple[AccountManager, Any, str]:
    """Get account manager, IMAP client, and account name.

    Returns:
        Tuple of (AccountManager, IMAPClient, account_name)

    """
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

    # Connect to IMAP
    with console.status(f"[bold green]Connecting to {account_info.email}...", spinner="dots"):
        client = manager.get_imap_client(account)

    return manager, client, account


def _handle_common_errors(func: Callable) -> Callable:
    """Decorate to handle common IMAP errors."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
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
            console.print(f"[red]✗ Error: {e}[/red]")
            raise typer.Exit(1)

    return wrapper


def _add_message_to_table(table: Table, msg: MessageSummary) -> None:
    """Add a message to the table with consistent formatting."""
    # Convert timestamp to UTC for display
    timestamp_str = format_timestamp_to_utc(msg.date)

    # Truncate only subject and snippet - let UID, timestamp, from display fully
    subject = msg.subject[:27] + "..." if len(msg.subject) > 30 else msg.subject
    snippet = msg.snippet[:22] + "..." if len(msg.snippet) > 25 else msg.snippet

    table.add_row(msg.uid, timestamp_str, msg.sender, subject, snippet)


# --- Command Functions ---


@app.command("list | ls")
@_handle_common_errors
def list_messages(
    account: Annotated[str, typer.Option("--account", "-a", help="Account name to use")] = "",
    limit: Annotated[int, typer.Option("--limit", "-l", help="Number of messages to fetch")] = 20,
    unread_only: Annotated[bool, typer.Option("--unread", "-u", help="Show only unread messages")] = False,
):
    """List recent emails from specified account."""
    manager, client, account = _get_account_manager_and_client(account)
    account_info = manager.get_account(account)

    with console.status(f"[bold green]Fetching {limit} {'unread ' if unread_only else ''}messages...", spinner="dots"):
        # Get email UIDs
        uids = list(reversed(client.list_email_uids(unseen_only=unread_only)))
        uids = uids[: min(limit, len(uids))]

        if not uids:
            client.logout()
            console.print(f"[yellow]No {'unread ' if unread_only else ''}messages found[/yellow]")
            return

        # Fetch messages
        messages = client.fetch_messages(uids, include_quoted_body=False)
        client.logout()

    # Convert to summary objects
    message_summaries = [MessageSummary.from_message_data(msg) for msg in messages]

    # Create and populate table
    table = create_messages_table(f"Messages from {account_info.email}")
    for msg in message_summaries:
        _add_message_to_table(table, msg)

    console.print(table)
    console.print(
        f"[dim]Showing {len(message_summaries)} of {len(uids)} {'unread ' if unread_only else ''}messages[/dim]"
    )


@app.command("open | cat")
@_handle_common_errors
def open_message(
    uid: Annotated[str, typer.Argument(help="Message UID to read")],
    account: Annotated[str, typer.Option("--account", "-a", help="Account name to use")] = "",
):
    """Read a single email message by UID."""
    _, client, account = _get_account_manager_and_client(account)

    with console.status(f"[bold green]Fetching message {uid}...", spinner="dots"):
        # Fetch the specific message
        message = client.fetch_message(uid, include_quoted_body=False)
        client.logout()

    # Display message details
    console.print("\n[bold blue]Message Details[/bold blue]")
    console.print(f"[cyan]UID:[/cyan] {message['uid']}")
    console.print(f"[cyan]Timestamp:[/cyan] {format_timestamp_to_utc(message.get('date', 'N/A'))}")
    console.print(f"[cyan]Subject:[/cyan] {message.get('subject', 'N/A')}")

    # Extract headers
    headers = message.get("headers", {})
    sender = headers.get("From", "N/A")
    cc = headers.get("CC", headers.get("Cc", "N/A"))
    bcc = headers.get("BCC", headers.get("Bcc", "N/A"))

    console.print(f"[cyan]From:[/cyan] {sender}")
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


@app.command("search | find | grep")
@_handle_common_errors
def search_messages(
    query: Annotated[str, typer.Argument(help="Search query")],
    account: Annotated[str, typer.Option("--account", "-a", help="Account name to use")] = "",
    limit: Annotated[int, typer.Option("--limit", "-l", help="Number of messages to search")] = 100,
):
    """Search for messages containing the specified query."""
    manager, client, account = _get_account_manager_and_client(account)
    account_info = manager.get_account(account)

    with console.status(f"[bold green]Searching for '{query}'...", spinner="dots"):
        # Get recent messages to search through
        uids = client.list_email_uids(unseen_only=False)
        search_uids = uids[:limit]

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

    # Convert to summary objects and sort by date (newest first)
    message_summaries = [MessageSummary.from_message_data(msg) for msg in matching_messages]

    # Sort by date (newest first) - handle cases where date might be empty
    message_summaries.sort(
        key=lambda x: datetime.fromisoformat(x.date) if x.date else datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )

    table = create_messages_table(f"Search Results for '{query}' in {account_info.email}")

    for msg in message_summaries:
        _add_message_to_table(table, msg)

    console.print(table)
    console.print(
        f"[dim]Found {len(matching_messages)} messages containing '{query}' (searched {len(search_uids)} messages)[/dim]"
    )


@app.command("trash | rm")
@_handle_common_errors
def trash_message(
    uid: Annotated[str, typer.Argument(help="Message UID to move to trash")],
    account: Annotated[str, typer.Option("--account", "-a", help="Account name to use")] = "",
):
    """Move a message to trash."""
    _, client, account = _get_account_manager_and_client(account)

    with console.status(f"[bold green]Moving message {uid} to trash...", spinner="dots"):
        client.move_to_trash(uid)
        client.logout()

    console.print(f"[green]✓ Message {uid} moved to trash[/green]")


@app.command("spam")
@_handle_common_errors
def mark_message_spam(
    uid: Annotated[str, typer.Argument(help="Message UID to mark as spam")],
    account: Annotated[str, typer.Option("--account", "-a", help="Account name to use")] = "",
):
    """Mark a message as spam."""
    _, client, account = _get_account_manager_and_client(account)

    with console.status(f"[bold green]Marking message {uid} as spam...", spinner="dots"):
        client.mark_as_spam(uid)
        client.logout()

    console.print(f"[green]✓ Message {uid} marked as spam[/green]")


class Status(StrEnum):
    """Message status."""

    READ = "read"
    UNREAD = "unread"


@app.command("mark")
@_handle_common_errors
def mark_message(
    status: Annotated[Status, typer.Argument(help="Action to perform: 'read' or 'unread'")],
    uid: Annotated[str, typer.Argument(help="Message UID to mark")],
    account: Annotated[str, typer.Option("--account", "-a", help="Account name to use")] = "",
):
    """Mark a message as read or unread."""
    _, client, account = _get_account_manager_and_client(account)

    with console.status(f"[bold blue]Marking message {uid} as {status.value}...", spinner="dots"):
        try:
            if status == Status.READ:
                client.mark_as_read(uid)
            else:  # action == "unread"
                client.mark_as_unread(uid)
            client.logout()
        except ValidationError as e:
            client.logout()
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)

    console.print(f"[green]✓ Message {uid} marked as {status.value}[/green]")


if __name__ == "__main__":
    app()
