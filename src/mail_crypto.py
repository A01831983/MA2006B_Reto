#! /usr/bin/env python
from typing import Optional
import base64
import hashlib

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


def canonicalize_body(subject: str, recipient: str, body: str) -> bytes:
    subject = (subject or "").replace("\r\n", "\n").replace("\r", "\n")
    recipient = (recipient or "").replace("\r\n", "\n").replace("\r", "\n")
    body = (body or "").replace("\r\n", "\n").replace("\r", "\n")

    text = (
        f"To: {recipient}\n"
        f"Subject: {subject}\n\n"
        f"{body}"
    )

    if not text.endswith("\n"):
        text += "\n"

    return text.encode("utf-8")

def cert_fingerprint_sha256(cert: x509.Certificate) -> str:
    return cert.fingerprint(hashes.SHA256()).hex()


def load_private_key_pem(pem: str, password: Optional[str] = None):
    return serialization.load_pem_private_key(
        pem.encode("utf-8"),
        password=password.encode("utf-8") if password else None
    )


def sign_bytes(private_key_pem: str, password: Optional[str], data: bytes) -> str:
    key = load_private_key_pem(private_key_pem, password)
    sig = key.sign(
        data,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    return base64.b64encode(sig).decode("utf-8")


def verify_bytes(cert_pem: str, data: bytes, sig_b64: str) -> bool:
    cert = x509.load_pem_x509_certificate(cert_pem.encode("utf-8"))
    sig = base64.b64decode(sig_b64.encode("utf-8"))

    try:
        cert.public_key().verify(
            sig,
            data,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def b64decode_bytes(data_b64: str) -> bytes:
    return base64.b64decode(data_b64.encode("utf-8"))