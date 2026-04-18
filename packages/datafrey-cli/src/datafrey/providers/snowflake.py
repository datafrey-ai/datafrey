"""Snowflake provider: onboarding SQL and credential prompts."""

from __future__ import annotations

import os
from pathlib import Path

from datafrey.providers.base import DatabaseProvider, register_provider
from datafrey.ui.console import console
from datafrey.ui.prompts import prompt_password, prompt_select, prompt_text

# Snowflake unquoted identifier: letter or _ followed by letters/digits/_.
# Anything else is rejected at the prompt so user input can't reshape the
# generated DDL (role/grant/user creation SQL).
SNOWFLAKE_IDENT_PATTERN = r"^[a-zA-Z_][a-zA-Z0-9_]{0,254}$"

# Hard cap on the PEM file we'll read into the encrypted envelope. An RSA-4096
# encrypted PEM is ~3.5 KiB; 16 KiB covers every realistic key and stops a
# social-engineered path (/etc/shadow, ~/.ssh/id_rsa) from being sucked in.
_MAX_PEM_BYTES = 16 * 1024


def _read_pem_key(path_input: str) -> str:
    """Read a PEM private key from disk after validating path and contents.

    Rejects: symlinks, paths outside the user's home directory, files above
    _MAX_PEM_BYTES, and anything that doesn't open with a PEM header.
    """
    expanded = os.path.expanduser(path_input.strip())
    path = Path(expanded).resolve(strict=True)

    # Scope to $HOME so a mis-paste can't exfiltrate system files.
    home = Path.home().resolve()
    try:
        path.relative_to(home)
    except ValueError:
        raise ValueError(
            f"PEM key path must live under {home}. Got: {path}"
        ) from None

    if path.is_symlink():
        raise ValueError(f"PEM key path is a symlink (not allowed): {path}")
    if not path.is_file():
        raise ValueError(f"PEM key path is not a regular file: {path}")

    size = path.stat().st_size
    if size > _MAX_PEM_BYTES:
        raise ValueError(
            f"PEM key file is too large ({size} bytes, max {_MAX_PEM_BYTES})."
        )

    text = path.read_text().replace("\r\n", "\n")
    if "-----BEGIN " not in text.split("\n", 1)[0]:
        raise ValueError("File does not start with a PEM header ('-----BEGIN ...').")
    return text


def _build_setup_sql(choices: dict) -> str:
    """Build the full setup SQL block based on user choices."""
    # Uppercase at emit — Snowflake normalizes unquoted identifiers and the
    # generated DDL reads consistently regardless of how the user typed it.
    warehouse = choices["warehouse"].upper()
    auth = choices["auth_method"]
    db = choices["database"].upper()

    grants = f"""\
GRANT USAGE ON WAREHOUSE {warehouse} TO ROLE DATAFREY_ROLE;
GRANT USAGE ON DATABASE {db} TO ROLE DATAFREY_ROLE;

-- Existing objects
GRANT USAGE ON ALL SCHEMAS IN DATABASE {db} TO ROLE DATAFREY_ROLE;
GRANT SELECT ON ALL TABLES IN DATABASE {db} TO ROLE DATAFREY_ROLE;
GRANT SELECT ON ALL VIEWS IN DATABASE {db} TO ROLE DATAFREY_ROLE;

-- Future objects (auto-granted as new schemas/tables/views are created)
GRANT USAGE ON FUTURE SCHEMAS IN DATABASE {db} TO ROLE DATAFREY_ROLE;
GRANT SELECT ON FUTURE TABLES IN DATABASE {db} TO ROLE DATAFREY_ROLE;
GRANT SELECT ON FUTURE VIEWS IN DATABASE {db} TO ROLE DATAFREY_ROLE;"""

    # User creation
    user = f"""\
CREATE USER IF NOT EXISTS DATAFREY_USER
  DEFAULT_ROLE = DATAFREY_ROLE
  DEFAULT_WAREHOUSE = {warehouse};
GRANT ROLE DATAFREY_ROLE TO USER DATAFREY_USER;"""

    # Network policy (PAT only)
    network = ""
    if auth == "pat":
        network = """

CREATE OR REPLACE NETWORK POLICY DATAFREY_NETWORK_POLICY
  ALLOWED_IP_LIST = ('3.229.236.29');

ALTER USER DATAFREY_USER SET NETWORK_POLICY = DATAFREY_NETWORK_POLICY;"""

    pat = ""
    if auth == "pat":
        pat = """

-- Run this last. Copy the token from the result — it won't be shown again.
ALTER USER DATAFREY_USER ADD PROGRAMMATIC ACCESS TOKEN DATAFREY_PAT
  ROLE_RESTRICTION = 'DATAFREY_ROLE'
  DAYS_TO_EXPIRY = 180;"""

    return f"CREATE ROLE IF NOT EXISTS DATAFREY_ROLE;\n\n{grants}\n\n{user}{network}{pat}"


@register_provider
class SnowflakeProvider(DatabaseProvider):
    name = "snowflake"
    display_name = "Snowflake"

    def collect_auth_method(self) -> dict:
        # Only one option — auto-select without prompting
        console.print("Authentication method: Programmatic Access Token (PAT)")
        return {"auth_method": "pat"}

    def collect_setup_choices(self, pre_choices: dict | None = None) -> dict:
        auth = (pre_choices or {}).get("auth_method", "pat")

        console.print()
        console.print("[dim]To list your databases:[/] [bold cyan]SHOW DATABASES;[/]")
        database = prompt_text(
            "Database name:", validate_pattern=SNOWFLAKE_IDENT_PATTERN
        )
        console.print(
            "[dim]You can connect more databases later.[/]"
        )

        console.print()
        console.print("[dim]To list your warehouses:[/] [bold cyan]SHOW WAREHOUSES;[/]")
        console.print(
            "[dim]This warehouse will execute all LLM queries "
            "— pick one sized for your workload.[/]"
        )
        warehouse = prompt_text(
            "Warehouse name:", validate_pattern=SNOWFLAKE_IDENT_PATTERN
        )

        return {
            "auth_method": auth,
            "warehouse": warehouse,
            "database": database,
        }

    def get_onboarding_steps(self, choices: dict) -> list[tuple[str, str]]:
        setup_sql = _build_setup_sql(choices)
        return [("Run in Snowflake", setup_sql)]

    def collect_credentials(self, choices: dict) -> dict[str, str]:
        auth = choices["auth_method"]
        warehouse = choices["warehouse"]
        database = choices.get("database") or ""

        # For PAT, ask for token first (right after PAT SQL was shown)
        token = None
        if auth == "pat":
            token = prompt_password("Paste the access token:")

        console.print()
        console.print(
            "[dim]To find your account identifier, run in Snowflake:[/]"
        )
        console.print(
            "[bold cyan]SELECT CURRENT_ORGANIZATION_NAME() || '-' "
            "|| CURRENT_ACCOUNT_NAME();[/]"
        )
        console.print(
            "[dim]Expected format:[/] [bold cyan]orgname-accountname[/] "
            "[dim](e.g. myorg-myaccount)[/]"
        )
        account = prompt_text(
            "Account identifier:", validate_pattern=r"^[a-zA-Z0-9_.-]+$"
        )
        username = prompt_text(
            "Username:",
            default="DATAFREY_USER",
            validate_pattern=SNOWFLAKE_IDENT_PATTERN,
        )
        role = prompt_text(
            "Role:",
            default="DATAFREY_ROLE",
            validate_pattern=SNOWFLAKE_IDENT_PATTERN,
        )
        name = f"{account.split('.')[0]}-db"

        base = {
            "account": account,
            "host": f"{account}.snowflakecomputing.com",
            "username": username,
            "role": role,
            "name": name,
            "warehouse": warehouse,
            "database": database,
        }

        if auth == "pat":
            return {**base, "auth_type": "pat", "token": token}

        # RSA Key Pair
        key_path = prompt_text("Path to PEM private key file:")
        private_key_pem = _read_pem_key(key_path)
        passphrase = (
            prompt_password("Key passphrase (Enter to skip):", optional=True) or None
        )
        return {
            **base,
            "auth_type": "keypair",
            "private_key_pem": private_key_pem,
            "private_key_passphrase": passphrase,
        }

    def get_review_fields(self, credentials: dict[str, str]) -> dict[str, str]:
        auth_label = {"pat": "PAT", "keypair": "RSA Key Pair"}.get(
            str(credentials.get("auth_type", "")), "Unknown"
        )
        warehouse = credentials["warehouse"] or "(default)"
        database = credentials["database"] or "(all databases)"
        return {
            "Provider": self.display_name,
            "Account": credentials["account"],
            "User": credentials["username"],
            "Role": credentials["role"],
            "Auth": auth_label,
            "Warehouse": warehouse,
            "Database": database,
            "Name": credentials["name"],
        }
