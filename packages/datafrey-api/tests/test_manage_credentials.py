"""Tests for provider-specific credential schemas."""

import pytest
from pydantic import ValidationError

from datafrey_api import (
    Provider,
    SnowflakeCredentials,
    SnowflakeKeyPairCredentials,
    SnowflakePATCredentials,
    validate_credentials,
)

_FAKE_PEM = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----"

_SNOWFLAKE_COMMON = {
    "account": "abc12345.us-east-1",
    "host": "abc12345.us-east-1.snowflakecomputing.com",
    "username": "DATAFREY_USER",
    "role": "DATAFREY_ROLE",
    "warehouse": "COMPUTE_WH",
    "database": "PROD_DB",
}


class TestSnowflakePATCredentials:
    _VALID = {**_SNOWFLAKE_COMMON, "auth_type": "pat", "token": "v2.st.abc123"}

    def test_valid(self):
        creds = SnowflakePATCredentials(**self._VALID)
        assert creds.account == "abc12345.us-east-1"
        assert creds.auth_type == "pat"

    def test_token_required(self):
        data = {**self._VALID, "token": ""}
        with pytest.raises(ValidationError):
            SnowflakePATCredentials(**data)

    def test_token_hidden_in_repr(self):
        creds = SnowflakePATCredentials(**self._VALID)
        assert "v2.st.abc123" not in repr(creds)

    def test_host_must_be_snowflake_domain(self):
        data = {**self._VALID, "host": "evil.example.com"}
        with pytest.raises(ValidationError, match="snowflakecomputing.com"):
            SnowflakePATCredentials(**data)

    def test_account_format_enforced(self):
        data = {**self._VALID, "account": "bad account!"}
        with pytest.raises(ValidationError, match="account"):
            SnowflakePATCredentials(**data)

    def test_warehouse_optional(self):
        data = {**self._VALID}
        del data["warehouse"]
        creds = SnowflakePATCredentials(**data)
        assert creds.warehouse == ""

    def test_database_optional(self):
        data = {**self._VALID}
        del data["database"]
        creds = SnowflakePATCredentials(**data)
        assert creds.database == ""


class TestSnowflakeKeyPairCredentials:
    _VALID = {
        **_SNOWFLAKE_COMMON,
        "auth_type": "keypair",
        "private_key_pem": _FAKE_PEM,
    }

    def test_valid(self):
        creds = SnowflakeKeyPairCredentials(**self._VALID)
        assert creds.auth_type == "keypair"
        assert creds.private_key_passphrase is None

    def test_passphrase_optional(self):
        creds = SnowflakeKeyPairCredentials(**self._VALID)
        assert creds.private_key_passphrase is None

    def test_passphrase_stored(self):
        creds = SnowflakeKeyPairCredentials(**{**self._VALID, "private_key_passphrase": "secret"})
        assert creds.private_key_passphrase == "secret"

    def test_private_key_pem_required(self):
        data = {**self._VALID, "private_key_pem": ""}
        with pytest.raises(ValidationError):
            SnowflakeKeyPairCredentials(**data)

    def test_private_key_pem_must_start_with_begin(self):
        data = {**self._VALID, "private_key_pem": "not a pem"}
        with pytest.raises(ValidationError, match="PEM"):
            SnowflakeKeyPairCredentials(**data)

    def test_private_key_pem_hidden_in_repr(self):
        creds = SnowflakeKeyPairCredentials(**self._VALID)
        assert "MIIEowIBAAKCAQEA" not in repr(creds)

    def test_host_must_be_snowflake_domain(self):
        data = {**self._VALID, "host": "evil.example.com"}
        with pytest.raises(ValidationError, match="snowflakecomputing.com"):
            SnowflakeKeyPairCredentials(**data)



class TestValidateCredentials:
    def test_dispatches_to_snowflake_pat(self):
        result = validate_credentials(
            Provider.snowflake,
            {
                "account": "abc123",
                "host": "abc123.snowflakecomputing.com",
                "username": "user",
                "role": "role",
                "auth_type": "pat",
                "token": "mytoken",
            },
        )
        assert isinstance(result, SnowflakePATCredentials)

    def test_dispatches_to_snowflake_keypair(self):
        result = validate_credentials(
            Provider.snowflake,
            {
                "account": "abc123",
                "host": "abc123.snowflakecomputing.com",
                "username": "user",
                "role": "role",
                "auth_type": "keypair",
                "private_key_pem": _FAKE_PEM,
            },
        )
        assert isinstance(result, SnowflakeKeyPairCredentials)

    def test_snowflake_unknown_auth_type_fails(self):
        with pytest.raises(ValidationError):
            validate_credentials(
                Provider.snowflake,
                {
                    "account": "abc123",
                    "host": "abc123.snowflakecomputing.com",
                    "username": "user",
                    "role": "role",
                    "auth_type": "password",
                    "password": "secret",
                },
            )

    def test_missing_host_shows_clear_error(self):
        """Credentials sent without host field raise a clear error."""
        with pytest.raises(ValidationError, match="host"):
            validate_credentials(
                Provider.snowflake,
                {
                    "account": "sfdsfsd",
                    "username": "DATAFREY_USER",
                    "role": "DATAFREY_ROLE",
                    "warehouse": "",
                    "database": "",
                    "auth_type": "pat",
                    "token": "tok",
                },
            )
