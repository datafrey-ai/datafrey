"""Snowflake provider: onboarding SQL and credential prompts."""

from __future__ import annotations

from pathlib import Path

from datafrey.providers.base import DatabaseProvider, register_provider
from datafrey.ui.console import console
from datafrey.ui.prompts import prompt_password, prompt_select, prompt_text


def _build_setup_sql(choices: dict) -> str:
    """Build the full setup SQL block based on user choices."""
    warehouse = choices["warehouse"]
    auth = choices["auth_method"]
    db = choices["database"]

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
        console.print("[dim]To list your databases:[/] [bold]SHOW DATABASES;[/]")
        database = prompt_text("Database name:")
        console.print(
            "[dim]You can connect more databases later.[/]"
        )

        console.print()
        console.print("[dim]To list your warehouses:[/] [bold]SHOW WAREHOUSES;[/]")
        console.print(
            "[dim]This warehouse will execute all LLM queries "
            "— pick one sized for your workload.[/]"
        )
        warehouse = prompt_text("Warehouse name:")

        return {
            "auth_method": auth,
            "warehouse": warehouse,
            "database": database,
        }

    def get_onboarding_steps(self, choices: dict) -> list[tuple[str, str]]:
        setup_sql = _build_setup_sql(choices)
        return [("Run in Snowflake", setup_sql)]

    def collect_credentials(self, choices: dict) -> dict[str, str]:
        import os

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
            "[bold]SELECT CURRENT_ORGANIZATION_NAME() || '-' "
            "|| CURRENT_ACCOUNT_NAME();[/]"
        )
        console.print(
            "[dim]Expected format:[/] [bold]orgname-accountname[/] "
            "[dim](e.g. myorg-myaccount)[/]"
        )
        account = prompt_text(
            "Account identifier:", validate_pattern=r"^[a-zA-Z0-9_.-]+$"
        )
        username = prompt_text("Username:", default="DATAFREY_USER")
        role = prompt_text("Role:", default="DATAFREY_ROLE")
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
        key_path = os.path.expanduser(key_path.strip())
        private_key_pem = Path(key_path).read_text().replace("\r\n", "\n")
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
