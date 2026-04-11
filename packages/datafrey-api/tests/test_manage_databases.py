import base64
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from datafrey_api import (
    DatabaseCreate,
    DatabaseCreated,
    DatabaseRecord,
    EncryptedCredentials,
    Provider,
    DatabaseStatus,
)

# Valid base64 test values
_B64 = base64.b64encode(b"test-data-16byte").decode()


def _make_creds(**overrides) -> EncryptedCredentials:
    defaults = dict(encrypted_key=_B64, nonce=_B64, ciphertext=_B64, tag=_B64)
    defaults.update(overrides)
    return EncryptedCredentials(**defaults)


class TestEncryptedCredentials:
    def test_valid(self):
        creds = _make_creds()
        assert creds.encrypted_key == _B64

    def test_invalid_base64_rejected(self):
        with pytest.raises(ValidationError, match="base64"):
            _make_creds(nonce="not!valid!base64!")

    def test_all_fields_repr_hidden(self):
        creds = _make_creds()
        r = repr(creds)
        assert _B64 not in r
        for field in ("encrypted_key", "nonce", "ciphertext", "tag"):
            assert field not in r or "=" not in r.split(field)[-1][:5]

    def test_empty_string_is_valid_base64(self):
        """Empty string is valid base64 (decodes to b'')."""
        creds = _make_creds(encrypted_key="")
        assert creds.encrypted_key == ""

    def test_padding_variants(self):
        for data in (b"a", b"ab", b"abc", b"abcd"):
            val = base64.b64encode(data).decode()
            creds = _make_creds(encrypted_key=val)
            assert creds.encrypted_key == val


class TestDatabaseCreate:
    def test_valid(self):
        db = DatabaseCreate(
            provider=Provider.snowflake,
            name="Production",
            encrypted_credentials=_make_creds(),
        )
        assert db.provider == Provider.snowflake
        assert db.name == "Production"

    def test_name_stripped(self):
        db = DatabaseCreate(
            provider=Provider.snowflake,
            name="  Staging  ",
            encrypted_credentials=_make_creds(),
        )
        assert db.name == "Staging"

    def test_name_empty_rejected(self):
        with pytest.raises(ValidationError):
            DatabaseCreate(
                provider=Provider.snowflake,
                name="",
                encrypted_credentials=_make_creds(),
            )

    def test_name_too_long_rejected(self):
        with pytest.raises(ValidationError):
            DatabaseCreate(
                provider=Provider.snowflake,
                name="x" * 101,
                encrypted_credentials=_make_creds(),
            )

    def test_name_whitespace_only_rejected(self):
        with pytest.raises(ValidationError):
            DatabaseCreate(
                provider=Provider.snowflake,
                name="   ",
                encrypted_credentials=_make_creds(),
            )


class TestDatabaseRecord:
    _VALID = dict(
        id="db-123",
        provider="snowflake",
        name="Prod",
        host="account.snowflakecomputing.com",
        status="connected",
        created_at="2025-01-01T00:00:00Z",
    )

    def test_valid_from_json(self):
        rec = DatabaseRecord.model_validate(self._VALID)
        assert rec.id == "db-123"
        assert rec.provider is Provider.snowflake
        assert rec.status is DatabaseStatus.connected
        assert isinstance(rec.created_at, datetime)

    def test_frozen(self):
        rec = DatabaseRecord.model_validate(self._VALID)
        with pytest.raises(ValidationError):
            rec.name = "Other"

    def test_invalid_provider_rejected(self):
        data = {**self._VALID, "provider": "mysql"}
        with pytest.raises(ValidationError):
            DatabaseRecord.model_validate(data)

    def test_invalid_status_rejected(self):
        data = {**self._VALID, "status": "pending"}
        with pytest.raises(ValidationError):
            DatabaseRecord.model_validate(data)


class TestDatabaseCreated:
    def test_frozen(self):
        rec = DatabaseCreated(
            id="db-1",
            provider=Provider.snowflake,
            name="Test",
            host="localhost",
            status=DatabaseStatus.disconnected,
            created_at=datetime.now(timezone.utc),
        )
        with pytest.raises(ValidationError):
            rec.id = "other"
