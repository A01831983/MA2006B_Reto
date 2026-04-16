#! /usr/bin/env python

# https://cryptography.io/en/latest/x509/tutorial/

import os
import datetime

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa

in_script_dir = lambda p: os.path.join(os.path.dirname(__file__), p)

# Generate the key
key = rsa.generate_private_key(
    public_exponent=65537, # 2^16+1 (prime)
    key_size=4096
)

server = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, "MX"),
    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Neuvo León"),
    x509.NameAttribute(NameOID.LOCALITY_NAME, "Monterrey"),
    x509.NameAttribute(NameOID.COMMON_NAME, "backend-example")
])

cert = x509.CertificateBuilder().\
    subject_name(server).\
    issuer_name(server).\
    public_key(key.public_key()).\
    serial_number(x509.random_serial_number()).\
    not_valid_before(datetime.datetime.now()).\
    not_valid_after(datetime.datetime.now() + datetime.timedelta(days=10)).\
    sign(key, hashes.SHA256())

# Write to disk
with open(in_script_dir("server_private_key.pem"), "wb") as f:
    f.write(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.BestAvailableEncryption(b"123Hola")
    ))

with open(in_script_dir("server_cert.pem"), "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))

# with open(in_script_dir("server_public_key.pem"), "wb") as f:
#     f.write(key.public_key().public_bytes(
#         encoding=serialization.Encoding.PEM,
#         format=serialization.PublicFormat.SubjectPublicKeyInfo
#     ))
