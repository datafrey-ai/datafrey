import pytest
from pydantic import ValidationError

from datafrey_api import PublicKeyResponse

_PEM = "-----BEGIN PUBLIC KEY-----\nMIIBIjAN...\n-----END PUBLIC KEY-----"
_FINGERPRINT = "SHA256:" + "A" * 44


class TestPublicKeyResponse:
    def test_valid(self):
        resp = PublicKeyResponse(
            public_key=_PEM,
            fingerprint=_FINGERPRINT,
            algorithm="RSA-OAEP-SHA256",
        )
        assert resp.algorithm == "RSA-OAEP-SHA256"

    def test_frozen(self):
        resp = PublicKeyResponse(
            public_key=_PEM,
            fingerprint=_FINGERPRINT,
            algorithm="RSA-OAEP-SHA256",
        )
        with pytest.raises(ValidationError):
            resp.public_key = "other"

    def test_bad_fingerprint_rejected(self):
        with pytest.raises(ValidationError, match="fingerprint"):
            PublicKeyResponse(
                public_key=_PEM,
                fingerprint="md5:abc",
                algorithm="RSA-OAEP-SHA256",
            )

    def test_fingerprint_too_short(self):
        with pytest.raises(ValidationError):
            PublicKeyResponse(
                public_key=_PEM,
                fingerprint="SHA256:short",
                algorithm="RSA-OAEP-SHA256",
            )

    def test_wrong_algorithm_rejected(self):
        with pytest.raises(ValidationError):
            PublicKeyResponse(
                public_key=_PEM,
                fingerprint=_FINGERPRINT,
                algorithm="RSA-PKCS1",
            )
