#! /usr/bin/env python

# https://cryptography.io/en/latest/x509/tutorial/

import sys
import os
import random

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa

if len(sys.argv) == 1:
    print("usage: gen_csr.py <password>")
    exit()

in_script_dir = lambda p: os.path.join(os.path.dirname(__file__), p)

# Generate the key
key = rsa.generate_private_key(
    public_exponent=65537, # 2^16+1 (prime)
    key_size=4096
)

# Write to disk
with open(in_script_dir("client_private_key.pem"), "wb") as f:
    f.write(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.BestAvailableEncryption(sys.argv[1].encode())
    ))

# Generate the CSR
csr = x509.CertificateSigningRequestBuilder().subject_name(x509.Name([
    x509.NameAttribute(NameOID.EMAIL_ADDRESS, "example@domain.com"),
    x509.NameAttribute(NameOID.GIVEN_NAME, "Max Mustermann"),
    x509.NameAttribute(NameOID.SURNAME, "Mustermann"),
    x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME,
                       "Beneficiario"),
    x509.NameAttribute(NameOID.SERIAL_NUMBER, str(random.randint(0, 2**31-1)))
])).sign(key, hashes.SHA256())

with open(in_script_dir("csr.pem"), "wb") as f:
    f.write(csr.public_bytes(serialization.Encoding.PEM))

print(repr(csr.public_bytes(serialization.Encoding.PEM).decode()))
