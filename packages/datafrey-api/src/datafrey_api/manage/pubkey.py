import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

_FINGERPRINT_RE = re.compile(r"^SHA256:[A-Za-z0-9+/=]{44}$")


class PublicKeyResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    public_key: str  # PEM-encoded RSA public key
    fingerprint: str  # pattern: ^SHA256:[A-Za-z0-9+/=]{44}$
    algorithm: Literal["RSA-OAEP-SHA256"]

    @field_validator("fingerprint")
    @classmethod
    def validate_fingerprint(cls, v: str) -> str:
        if not _FINGERPRINT_RE.match(v):
            raise ValueError("fingerprint must match ^SHA256:[A-Za-z0-9+/=]{44}$")
        return v
