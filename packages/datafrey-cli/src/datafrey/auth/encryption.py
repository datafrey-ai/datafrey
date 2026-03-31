"""Client-side credential encryption: AES-256-GCM + RSA-OAEP."""

from __future__ import annotations

import json
import os
from base64 import b64encode

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def encrypt_credentials(
    credentials: dict, public_key_pem: str, *, aad: bytes | None = None
) -> dict[str, str]:
    """Encrypt credentials with AES-256-GCM, wrap key with RSA-OAEP.

    Args:
        aad: Additional Authenticated Data binding the ciphertext to context
             (e.g. user sub). The server must pass the same AAD during decryption.

    Returns dict with base64-encoded: encrypted_key, nonce, ciphertext, tag.
    """
    # Normalize PEM: handle literal \n sequences and Windows line endings
    normalized_pem = public_key_pem.replace("\\n", "\n").replace("\r\n", "\n")
    public_key = serialization.load_pem_public_key(normalized_pem.encode())

    # Generate random AES-256 key
    aes_key = AESGCM.generate_key(bit_length=256)
    nonce = os.urandom(12)

    # Encrypt credentials
    plaintext = json.dumps(credentials).encode()
    ct = AESGCM(aes_key).encrypt(nonce, plaintext, aad)

    # AES-GCM appends the 16-byte tag to the ciphertext
    ciphertext = ct[:-16]
    tag = ct[-16:]

    # Wrap AES key with RSA-OAEP
    encrypted_key = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    return {
        "encrypted_key": b64encode(encrypted_key).decode(),
        "nonce": b64encode(nonce).decode(),
        "ciphertext": b64encode(ciphertext).decode(),
        "tag": b64encode(tag).decode(),
    }
