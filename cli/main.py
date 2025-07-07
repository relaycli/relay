# Copyright (C) 2025, Relay.

# All rights reserved.
# Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.

import json
from pathlib import Path
from typing import Optional

import click
import httpx

# Configuration
DEFAULT_BASE_URL = "https://api.relay.com/api/v1"
CONFIG_DIR = Path.home() / ".relay"
CONFIG_FILE = CONFIG_DIR / "config.json"
TOKEN_FILE = CONFIG_DIR / "token"


def ensure_config_dir():
    """Ensure configuration directory exists."""
    CONFIG_DIR.mkdir(exist_ok=True)


def load_config() -> dict:
    """Load configuration from file."""
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {"base_url": DEFAULT_BASE_URL}


def save_config(config: dict):
    """Save configuration to file."""
    ensure_config_dir()
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def load_token() -> Optional[str]:
    """Load stored authentication token."""
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    return None


def save_token(token: str):
    """Save authentication token."""
    ensure_config_dir()
    TOKEN_FILE.write_text(token)
    TOKEN_FILE.chmod(0o600)  # Secure permissions


def delete_token():
    """Delete stored authentication token."""
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()


class APIClient:
    def __init__(self, base_url: str, token: Optional[str] = None):
        self.base_url = base_url
        self.token = token

    @property
    def headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def login_with_credentials(self, email: str, password: str) -> str:
        """Login with email/password and return token."""
        with httpx.Client() as client:
            response = client.post(
                f"{self.base_url}/login/creds",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={"username": email, "password": password},
            )
            response.raise_for_status()
            return response.json()["access_token"]

    def get_user_info(self) -> dict:
        """Get current user information."""
        with httpx.Client() as client:
            response = client.get(f"{self.base_url}/users/me", headers=self.headers)
            response.raise_for_status()
            return response.json()

    def validate_token(self) -> bool:
        """Validate authentication token."""
        with httpx.Client() as client:
            response = client.get(f"{self.base_url}/login/validate", headers=self.headers)
            return response.status_code == 200

    def list_threads(self, max_results: int = 10) -> list[dict]:
        """List all threads."""
        with httpx.Client() as client:
            response = client.get(
                f"{self.base_url}/gmail/threads", headers=self.headers, params={"max_results": max_results}
            )
            response.raise_for_status()
            return response.json()


# CLI Context
@click.group()
@click.option("--base-url", default=None, help="API base URL")
@click.pass_context
def cli(ctx, base_url):
    """InvoxFlow CLI - Manage your inbox efficiently."""
    ctx.ensure_object(dict)

    config = load_config()
    if base_url:
        config["base_url"] = base_url
        save_config(config)

    ctx.obj["config"] = config
    ctx.obj["client"] = APIClient(config["base_url"], load_token())


# Authentication commands
@cli.group()
def auth():
    """Authentication commands."""


@auth.command()
@click.option("--email", prompt=True, help="Your email address")
@click.option("--password", prompt=True, hide_input=True, help="Your password")
@click.pass_context
def login(ctx, email, password):
    """Login with email and password."""
    client = ctx.obj["client"]

    try:
        token = client.login_with_credentials(email, password)
        save_token(token)
        click.echo(click.style("✓ Login successful!", fg="green"))
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            click.echo(click.style("✗ Invalid credentials", fg="red"))
        else:
            click.echo(click.style(f"✗ Login failed: {e.response.text}", fg="red"))
        raise click.Abort()
    except Exception as e:
        click.echo(click.style(f"✗ Login failed: {e!s}", fg="red"))
        raise click.Abort()


@auth.command()
def logout():
    """Logout and clear stored credentials."""
    delete_token()
    click.echo(click.style("✓ Logged out successfully", fg="green"))


@auth.command()
@click.pass_context
def status(ctx):
    """Check authentication status."""
    token = load_token()
    if not token:
        click.echo(click.style("✗ Not authenticated", fg="red"))
        return

    client = ctx.obj["client"]
    if client.validate_token():
        click.echo(click.style("✓ Authenticated", fg="green"))
    else:
        click.echo(click.style("✗ Authentication invalid", fg="red"))
        delete_token()


# User commands
@cli.group()
def user():
    """User management commands."""


@user.command("info")
@click.pass_context
def user_info(ctx):
    """Get current user information."""
    token = load_token()
    if not token:
        click.echo(click.style("✗ Not authenticated. Run 'invox auth login' first.", fg="red"))
        raise click.Abort()

    client = ctx.obj["client"]
    try:
        user_data = client.get_user_info()

        click.echo(click.style("User Information:", fg="blue", bold=True))
        click.echo(f"ID: {user_data['id']}")
        click.echo(f"Email: {user_data['email']}")
        click.echo(f"Role: {user_data['role']}")
        click.echo(f"Username: {user_data.get('username', 'Not set')}")
        click.echo(
            f"Approved: {click.style('Yes', fg='green') if user_data['is_approved'] else click.style('No', fg='red')}"
        )
        click.echo(
            f"Push notifications: {click.style('Enabled', fg='green') if user_data['push_notifications_enabled'] else click.style('Disabled', fg='red')}"
        )
        if user_data.get("dark_mode_enabled") is not None:
            click.echo(
                f"Dark mode: {click.style('Enabled', fg='green') if user_data['dark_mode_enabled'] else click.style('Disabled', fg='red')}"
            )

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            click.echo(click.style("✗ Authentication invalid. Run 'invox auth login' first.", fg="red"))
            delete_token()
        else:
            click.echo(click.style(f"✗ Failed to get user info: {e.response.text}", fg="red"))
        raise click.Abort()
    except Exception as e:
        click.echo(click.style(f"✗ Error: {e!s}", fg="red"))
        raise click.Abort()


# Configuration commands
@cli.group()
def config():
    """Configuration commands."""


@config.command("show")
@click.pass_context
def show_config(ctx):
    """Show current configuration."""
    config = ctx.obj["config"]
    click.echo(click.style("Configuration:", fg="blue", bold=True))
    click.echo(f"Base URL: {config['base_url']}")

    token = load_token()
    if token:
        click.echo(click.style("✓ Authentication token stored", fg="green"))
    else:
        click.echo(click.style("✗ No authentication token", fg="red"))


@config.command("set-url")
@click.argument("url")
@click.pass_context
def set_base_url(ctx, url):
    """Set the API base URL."""
    config = ctx.obj["config"]
    config["base_url"] = url
    save_config(config)
    click.echo(click.style(f"✓ Base URL set to: {url}", fg="green"))


# Gmail commands
@cli.group()
def gmail():
    """Gmail commands."""


@gmail.group()
def threads():
    """Thread commands."""


@threads.command("list")
@click.option("--max-results", default=10, help="Maximum number of threads to list")
@click.pass_context
def list_threads(ctx, max_results):
    """List recent threads."""
    client = ctx.obj["client"]
    threads = client.list_threads(max_results)
    click.echo(click.style(f"Threads: {threads}", fg="green"))


if __name__ == "__main__":
    cli()
