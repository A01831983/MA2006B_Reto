#! /usr/bin/env python

"""
Routines for simplifying certificate creation for users from the gestor.
"""

__author__ = "Henning Arvid Ladewig"

import datetime

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa


org_unit = lambda u: u["dept"] + "," + u["lvl"]

def load_cert_file(filename):
    with open(filename, "rb") as file:
        data = file.read()
    
    return x509.load_pem_x509_certificate(data)

def load_key_file(filename, password: bytes = None):
    if isinstance(password, str): password = password.encode()

    with open(filename, "rb") as file:
        data = file.read()

    return serialization.load_pem_private_key(data, password=password)

def create_ck(key_size, key_file, cert_file, issuer, subject, signing_key=None):
    # Generate the key
    key = rsa.generate_private_key(
        public_exponent=65537, # 2^16 + 1, Fermat prime and efficient for computing
        key_size=key_size      # Minimum is 2048
    )

    # Save private key to a file
    with open(key_file, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    # Create certificate
    cert = x509.CertificateBuilder().\
        subject_name(subject).\
        issuer_name(issuer).\
        public_key(key.public_key()).\
        serial_number(x509.random_serial_number()).\
        not_valid_before(datetime.datetime.now()).\
        not_valid_after(datetime.datetime.now() + datetime.timedelta(weeks=4))

    if signing_key is None: # Self-sign
        signing_key = key
    
    cert = cert.sign(signing_key, hashes.SHA256())

    # Save the certificate to a file
    with open(cert_file, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    return cert, key

def create_usr_x509(usr, num):
    return x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "MX"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Nuevo León"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Monterrey"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME,
                           "Casa Monarca DUMMY TEST NOT REAL"),
        x509.NameAttribute(NameOID.GIVEN_NAME, usr["name"]),
        x509.NameAttribute(NameOID.EMAIL_ADDRESS, usr["mail"]),
        x509.NameAttribute(NameOID.SERIAL_NUMBER, num),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, org_unit(usr))
    ])
