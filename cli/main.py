# Copyright (C) 2025, Relay.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

"""Main CLI application for Relay."""

import typer
from rich.console import Console

import relay

from .commands.auth import app as auth_app

console = Console()
app = typer.Typer(
    help="Relay CLI - Manage your emails efficiently.",
    no_args_is_help=True,
    add_completion=False,
)

# Add auth subcommands
app.add_typer(auth_app, name="auth")


@app.command()
def version():
    """Show version information."""
    console.print(f"[bold blue]Relay CLI v{relay.__version__}[/bold blue]")
    console.print("Email management library and CLI")


if __name__ == "__main__":
    app()
