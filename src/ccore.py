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
from cryptography.hazmat.primitives.asymmetric import rsa, padding


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

def extract_user_data(cert: x509.Certificate):
    subj = cert.subject

    names = subj.get_attributes_for_oid(NameOID.GIVEN_NAME)
    if len(names) != 1: return "Missing GIVEN_NAME OID (or have too many)"
    name = names[0].value

    emails = subj.get_attributes_for_oid(NameOID.EMAIL_ADDRESS)
    if len(emails) != 1: return "Missing EMAIL_ADDRESS OID (or have too many)"
    email = emails[0].value

    uids = subj.get_attributes_for_oid(NameOID.SERIAL_NUMBER)
    if len(uids) != 1: return "Missing SERIAL_NUMBER OID (or have too many)"
    uid = uids[0].value

    units = subj.get_attributes_for_oid(NameOID.ORGANIZATIONAL_UNIT_NAME)
    if len(units) != 1: return "Missing ORGANIZATIONAL_UNIT_NAME OID (or have too many)"
    unit = units[0].value

    s = unit.split(",")
    if len(s) != 2:
        return "ORGANIZATIONAL_UNIT_NAME OID value should be of form <department>,<access level>"
    dept, lvl = s

    return {"uid": uid, "name": name, "mail": email, "lvl": lvl, "dept": dept}

def verify_cert(cert: x509.Certificate, trusted: [x509.Certificate]):
    for trust in trusted:
        try:
            trust.public_key().verify(
                signature=cert.signature,
                data=cert.tbs_certificate_bytes,
                padding=padding.PKCS1v15(),
                algorithm=cert.signature_hash_algorithm
            )

            return True
        except:
            continue

    return False
