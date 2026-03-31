import base64
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from datafrey_api.common import DatabaseStatus, Provider


def _validate_base64(v: str) -> str:
    try:
        base64.b64decode(v, validate=True)
    except Exception:
        raise ValueError("must be valid standard-alphabet base64")
    return v


class EncryptedCredentials(BaseModel):
    encrypted_key: str = Field(repr=False)  # base64: RSA-OAEP encrypted AES key
    nonce: str = Field(repr=False)  # base64: AES-GCM nonce (12 bytes)
    ciphertext: str = Field(repr=False)  # base64: encrypted payload
    tag: str = Field(repr=False)  # base64: AES-GCM auth tag (16 bytes)

    @field_validator("encrypted_key", "nonce", "ciphertext", "tag")
    @classmethod
    def validate_base64(cls, v: str) -> str:
        return _validate_base64(v)


class DatabaseCreate(BaseModel):
    provider: Provider
    name: Annotated[
        str, StringConstraints(min_length=1, max_length=100, strip_whitespace=True)
    ]
    encrypted_credentials: EncryptedCredentials


class DatabaseRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    provider: Provider
    name: str
    host: str
    status: DatabaseStatus
    created_at: datetime  # UTC, ISO-8601


class DatabaseCreated(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    provider: Provider
    name: str
    host: str
    status: DatabaseStatus
    created_at: datetime
