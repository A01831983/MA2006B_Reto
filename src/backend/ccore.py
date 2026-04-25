#! /usr/bin/env python

"""
Core cryptographic functions:
- Certificate generation
"""

__author__ = "Henning Arvid Ladewig"

from datetime import date, datetime

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa


COUNTRY = "MX"
STATE = "Nuevo León"
ORG_NAME = "Casa Monarca DUMMY TEST NOT REAL"
CITY = "Monterrey"
URL = "casamonarca.mx"

ISSUER = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, COUNTRY),
    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, STATE),
    x509.NameAttribute(NameOID.LOCALITY_NAME, CITY),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, ORG_NAME),
    x509.NameAttribute(NameOID.COMMON_NAME, URL)
])

privkey = None

def init(pkey_file, pwd=None):
    global privkey

    with open(pkey_file, "rb") as f:
        privkey = serialization.load_pem_private_key(
            f.read(),
            password=pwd
        )

def create_cert(uid: str, name: str, mail: str, dept: str, lvl: str,
                not_before: date, not_after: date, pwd: str,
                key_size: int = 2048):
    # Generate the key
    key = rsa.generate_private_key(
        public_exponent=65537, # 2^16+1, Fermat prime and efficient for computing
        key_size=key_size
    )

    pem_key = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.BestAvailableEncryption(pwd.encode())
    )

    # Generate the subject data
    serial_number = str(uid)
    unit = dept + "," + lvl

    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, COUNTRY),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, STATE),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, ORG_NAME),
        x509.NameAttribute(NameOID.GIVEN_NAME, name),
        x509.NameAttribute(NameOID.EMAIL_ADDRESS, mail),
        x509.NameAttribute(NameOID.SERIAL_NUMBER, serial_number),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, unit)
    ])

    cert = x509.CertificateBuilder().\
        subject_name(subject).\
        issuer_name(ISSUER).\
        public_key(key.public_key()).\
        serial_number(x509.random_serial_number()).\
        not_valid_before(datetime.combine(not_before, datetime.min.time())).\
        not_valid_after(datetime.combine(not_after, datetime.min.time())).\
        sign(privkey, hashes.SHA256())

    return cert, pem_key
