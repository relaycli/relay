# Copyright (C) 2025, Relay.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

"""Main CLI application for Relay."""

import typer
from rich.console import Console

import relay

from .commands.account import app as account_app
from .commands.messages import app as messages_app

console = Console()
app = typer.Typer(
    help="Relay CLI - Manage your emails efficiently.",
    no_args_is_help=True,
    add_completion=True,
)

# Add subcommands
app.add_typer(account_app, name="account")
app.add_typer(messages_app, name="messages")


@app.command()
def version():
    """Show version information."""
    console.print(f"[bold blue]relay {relay.__version__}[/bold blue]")


if __name__ == "__main__":
    app()
