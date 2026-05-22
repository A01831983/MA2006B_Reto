# pgp_core.py
#'''
import hashlib
import base64
import pgpy

def load_public_key(armored: str):
    key, _ = pgpy.PGPKey.from_blob(armored)
    return key

def load_private_key(armored: str):
    key, _ = pgpy.PGPKey.from_blob(armored)
    return key

def fingerprint_of_public_key(armored: str) -> str:
    key = load_public_key(armored)
    return str(key.fingerprint)

def canonicalize_body(subject: str, body: str) -> str:
    return f"Subject: {subject}\n\n{body}".replace("\r\n", "\n").strip() + "\n"

def sign_text_detached(private_key_armored: str, password: str, text: str) -> str:
    key = load_private_key(private_key_armored)
    if key.is_protected:
        with key.unlock(password):
            sig = key.sign(text, detached=True)
    else:
        sig = key.sign(text, detached=True)
    return str(sig)

def verify_text_detached(public_key_armored: str, text: str, signature_armored: str) -> bool:
    pub = load_public_key(public_key_armored)
    sig = pgpy.PGPSignature.from_blob(signature_armored)
    return bool(pub.verify(text, sig))

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sign_bytes_detached(private_key_armored: str, password: str, data: bytes) -> str:
    key = load_private_key(private_key_armored)
    if key.is_protected:
        with key.unlock(password):
            sig = key.sign(data, detached=True)
    else:
        sig = key.sign(data, detached=True)
    return str(sig)

def verify_bytes_detached(public_key_armored: str, data: bytes, signature_armored: str) -> bool:
    pub = load_public_key(public_key_armored)
    sig = pgpy.PGPSignature.from_blob(signature_armored)
    return bool(pub.verify(data, sig))

def b64encode_bytes(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")

def b64decode_bytes(data_b64: str) -> bytes:
    return base64.b64decode(data_b64.encode("utf-8"))

#'''