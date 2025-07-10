# Copyright (C) 2025, Relay.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.


import re

from rich.table import Table
from typer.core import TyperGroup

__all__ = ["AliasGroup", "create_accounts_table", "create_messages_table", "create_table"]


# cf. https://github.com/fastapi/typer/issues/132
class AliasGroup(TyperGroup):
    """Typer class to allow aliases for commands."""

    _CMD_SPLIT_P = re.compile(r" ?[,|] ?")

    def get_command(self, ctx, cmd_name):  # noqa: D102
        cmd_name = self._group_cmd_name(cmd_name)
        return super().get_command(ctx, cmd_name)

    def _group_cmd_name(self, default_name):
        for cmd in self.commands.values():
            name = cmd.name
            if name and default_name in self._CMD_SPLIT_P.split(name):
                return name
        return default_name


# --- Table Creation Utilities ---


def create_table(title: str) -> Table:
    """Create a basic Rich table with title."""
    return Table(title=title)


def create_messages_table(title: str) -> Table:
    """Create a standardized messages table."""
    table = Table(title=title)
    table.add_column("UID", style="cyan", no_wrap=True)
    table.add_column("Timestamp", style="blue", no_wrap=True, width=24)
    table.add_column("From", style="green", no_wrap=True)
    table.add_column("Subject", style="bold", max_width=30)
    table.add_column("Snippet", style="dim", max_width=25)
    return table


def create_accounts_table(title: str = "Configured Accounts") -> Table:
    """Create a standardized accounts table."""
    table = Table(title=title)
    table.add_column("Name", style="cyan")
    table.add_column("Email", style="magenta")
    table.add_column("Provider", style="green")
    table.add_column("Server", style="blue")
    table.add_column("Port", style="yellow")
    return table
