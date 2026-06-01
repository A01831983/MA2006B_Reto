#! /usr/bin/env python

"""
Authentication module: password hashing and JWT generation/validation.
"""

__author__ = "Diego Octavio Arias Inchaustegui"

import os
import secrets
from datetime import datetime, timedelta

import bcrypt
import jwt
from dotenv import load_dotenv


load_dotenv()

SECRET_KEY = os.environ.get("JWT_SECRET")
if not SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET is not defined. Ensure .env exists and contains: "
        "JWT_SECRET=<key>"
    )

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 8
BCRYPT_ROUNDS = 12
TEMP_PASSWORD_LENGTH = 12

SAFE_CHARS = (
    "abcdefghjkmnpqrstuvwxyz"
    "ABCDEFGHJKLMNPQRSTUVWXYZ"
    "23456789"
)


def hash_password(plain: str) -> str:
    if not isinstance(plain, str) or len(plain) == 0:
        raise ValueError("Password must be a non-empty string")

    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(plain.encode("utf-8"), salt)

    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    if not isinstance(plain, str) or not isinstance(hashed, str):
        return False

    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def generate_temp_password(length: int = TEMP_PASSWORD_LENGTH) -> str:
    return "".join(secrets.choice(SAFE_CHARS) for _ in range(length))


def create_jwt(uid: str, lvl: str, dept: str) -> str:
    now = datetime.utcnow()
    payload = {
        "uid": uid,
        "lvl": lvl,
        "dept": dept,
        "iat": now,
        "exp": now + timedelta(hours=JWT_EXPIRATION_HOURS),
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)

    if isinstance(token, bytes):
        token = token.decode("utf-8")

    return token


def decode_jwt(token: str):
    if not isinstance(token, str) or len(token) == 0:
        return None

    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None