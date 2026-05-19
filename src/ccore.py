#! /usr/bin/env python

"""
Core cryptographic functions:
- Certificate generation
"""

__author__ = "Henning Arvid Ladewig"

from datetime import date, datetime

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives.asymmetric import padding

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
