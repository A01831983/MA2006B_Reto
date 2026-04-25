#! /usr/bin/env python

"""
Generates a dummy (self-signed) certificate, saves it and the private key
encrypted with the password given as the command line.
"""

__author__ = "Henning Arvid Ladewig"

import os
import sys
import datetime

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa


# Utility function
indir = lambda filename: os.path.join(os.path.dirname(__file__), filename)

# Generate the key
key = rsa.generate_private_key(
    public_exponent=65537, # 2^16 + 1, Fermat prime and efficient for computing
    key_size=3072          # Minimum is 2048
)

# Save encrypted private key to a file
with open(indir("dummy_server_key.pem"), "wb") as f:
    f.write(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ))

# Details about the issuer of this certificate
# Since this is a self-issued certificate, these are the same for the subject
issuer = subject = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, "MX"),
    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Nuevo León"),
    x509.NameAttribute(NameOID.LOCALITY_NAME, "Monterrey"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Casa Monarca DUMMY TEST NOT REAL"),
    x509.NameAttribute(NameOID.COMMON_NAME, "casamonarca.mx")
])

# Create certificate
cert = x509.CertificateBuilder().\
    subject_name(subject).\
    issuer_name(issuer).\
    public_key(key.public_key()).\
    serial_number(x509.random_serial_number()).\
    not_valid_before(datetime.datetime.now()).\
    not_valid_after(datetime.datetime.now() + datetime.timedelta(weeks=4)).\
    sign(key, hashes.SHA256())

# Save the certificate to a file
with open(indir("dummy_server_cert.pem"), "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))
