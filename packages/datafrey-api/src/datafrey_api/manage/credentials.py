"""Provider-specific plaintext credential schemas.

These models validate the credential dict BEFORE encryption (CLI-side)
and AFTER decryption (API-side). They ensure the encrypted payload
contains exactly the fields each provider requires.
"""

from __future__ import annotations

import re
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, StringConstraints, TypeAdapter, field_validator

from datafrey_api.common import Provider

# ---------------------------------------------------------------------------
# Snowflake
# ---------------------------------------------------------------------------

_ACCOUNT_RE = r"^[a-zA-Z0-9_.-]+$"
_HOST_RE = r"^[a-zA-Z0-9._-]+\.snowflakecomputing\.com$"


class _SnowflakeBase(BaseModel):
    """Shared fields for all Snowflake auth variants."""

    account: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
    host: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
    username: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
    role: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
    warehouse: str = ""
    database: str = ""

    @field_validator("account")
    @classmethod
    def validate_account(cls, v: str) -> str:
        if not re.match(_ACCOUNT_RE, v):
            raise ValueError(
                "account must contain only alphanumerics, dots, hyphens, and underscores"
            )
        return v

    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        if not re.match(_HOST_RE, v):
            raise ValueError("host must be a *.snowflakecomputing.com address")
        return v


class SnowflakePATCredentials(_SnowflakeBase):
    """Programmatic Access Token authentication."""

    auth_type: Literal["pat"] = "pat"
    token: Annotated[str, StringConstraints(min_length=1)] = Field(repr=False)


class SnowflakeKeyPairCredentials(_SnowflakeBase):
    """RSA Key Pair authentication."""

    auth_type: Literal["keypair"] = "keypair"
    private_key_pem: Annotated[str, StringConstraints(min_length=1)] = Field(repr=False)
    private_key_passphrase: str | None = Field(default=None, repr=False)

    @field_validator("private_key_pem")
    @classmethod
    def validate_pem(cls, v: str) -> str:
        if not v.strip().startswith("-----BEGIN"):
            raise ValueError("private_key_pem must be a PEM-encoded private key")
        return v


# Discriminated union — use as the canonical Snowflake credential type
SnowflakeCredentials = Annotated[
    Union[SnowflakePATCredentials, SnowflakeKeyPairCredentials],
    Field(discriminator="auth_type"),
]

_SNOWFLAKE_ADAPTER: TypeAdapter = TypeAdapter(SnowflakeCredentials)


# ---------------------------------------------------------------------------
# PostgreSQL (placeholder — expand when postgres provider is implemented)
# ---------------------------------------------------------------------------


class PostgresCredentials(BaseModel):
    """Plaintext PostgreSQL credential fields."""

    host: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
    port: int = Field(default=5432, ge=1, le=65535)
    username: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
    password: Annotated[str, StringConstraints(min_length=1)] = Field(repr=False)
    database: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_CREDENTIAL_SCHEMAS = {
    Provider.snowflake: _SNOWFLAKE_ADAPTER,
    Provider.postgres: PostgresCredentials,
}


def validate_credentials(provider: Provider, data: dict) -> BaseModel:
    """Validate a plaintext credential dict against the provider's schema.

    Returns the validated model instance.
    Raises ``pydantic.ValidationError`` on invalid data.
    """
    schema = _CREDENTIAL_SCHEMAS[provider]
    if isinstance(schema, TypeAdapter):
        return schema.validate_python(data)
    return schema.model_validate(data)
