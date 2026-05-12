#! /usr/bin/env python

"""
Generates a dummy infrastructure setup, including server and admin keys/certificates.
- self-signed server certificate and key (srv_cert.pem, srv_key.pem)
- self-signed admin certificate and key (admin_cert.pem, admin_key.pem)
- self-signed backup admin certificate and key (badmin_cert.pem, badmin_key.pem)
- 2 coordinador certificates and keys
- database (dummy.json)
"""

__author__ = "Henning Arvid Ladewig"

import os
import sys
import datetime
from datetime import date

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                             "..")))

from src import db


# Utility functions
indir = lambda filename: os.path.join(os.path.dirname(__file__), filename)
org_unit = lambda u: u["dept"] + "," + u["lvl"]

def create_ck(key_size, key_file, cert_file, issuer, subject, signing_key=None):
    # Generate the key
    key = rsa.generate_private_key(
        public_exponent=65537, # 2^16 + 1, Fermat prime and efficient for computing
        key_size=key_size      # Minimum is 2048
    )

    # Save private key to a file
    with open(indir(key_file), "wb") as f:
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
    with open(indir(cert_file), "wb") as f:
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

def add_cert(mail, cert):
    return db.add_cert(db.list_users(mail=mail)[0]["id"], cert)

# Server certificate
sissuer = ssubject = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, "MX"),
    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Nuevo León"),
    x509.NameAttribute(NameOID.LOCALITY_NAME, "Monterrey"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME,
                       "Casa Monarca DUMMY TEST NOT REAL"),
    x509.NameAttribute(NameOID.COMMON_NAME, "casamonarca.mx")
])
scert, skey = create_ck(3072, "srv_key.pem", "srv_cert.pem", sissuer, ssubject)

# Database
if not db.init(indir("dummy.json")):
    raise ValueError("Database file invalid format")

if len(db.list_users()) != 0: exit()

# Users
admin = {"name": "Max Mustermann", "dept": "TI", "lvl": "admin",
         "mail": "admin@casamonarca.mx", "joined": date(2026, 3, 10)}

badmin = admin.copy()
badmin["mail"] = "backup-admin@casamonarca.mx"

lopez = {"name": "María López", "dept": "Legal", "lvl": "coordinador",
         "mail": "m.lopez@casamonarca.mx", "joined": date(2024, 1, 1)}

morales = {"name": "Lucía Morales", "dept": "Almacén", "lvl": "coordinador",
           "mail": "l.morales@casamonarca.mx", "joined": date(2019, 12, 1)}

# Write users
dummy_users = [
    admin, badmin, lopez,
    {"name": "José Ramírez", "dept": "Humanitaria", "lvl": "operativo",
     "mail": "j.ramirez@casamonarca.mx", "joined": date(2024, 8, 15)},
    {"name": "Ana González", "dept": "PsicoSocial", "lvl": "operativo",
     "mail": "a.gonzalez@casamonarca.mx", "joined": date(2024, 10, 13)},
    {"name": "Carlos Vega", "dept": "Legal", "lvl": "operativo",
     "mail": "c.vega@casamonarca.mx", "joined": date(2020, 6, 1)},
    morales,
    {"name": "Roberto Salas", "dept": "Comunicación", "lvl": "operativo",
     "mail": "r.salas@casamonarca.mx", "joined": date(2025, 12, 24)},
    {"name": "Diana Fuentes", "dept": "PsicoSocial", "lvl": "operativo",
     "mail": "d.fuentes@casamonarca.mx", "joined": date(2026, 1, 1)}
]

dummy_user_ids = {}
def upd(d, k, v):
    d[k] = v
    return v
list(map(lambda u: upd(dummy_user_ids, u["mail"], db.add_user(**u)), dummy_users))

# Write certificates
aissuer = asubject = create_usr_x509(admin, dummy_user_ids[admin["mail"]])
acert, akey = create_ck(2048, "admin_key.pem", "admin_cert.pem", aissuer,
                        asubject)
bissuer = bsubject = create_usr_x509(badmin, dummy_user_ids[badmin["mail"]])
bcert, bkey = create_ck(2048, "badmin_key.pem", "badmin_cert.pem", bissuer,
                        bsubject)
c1subject = create_usr_x509(lopez, dummy_user_ids[lopez["mail"]])
c1cert, c1key = create_ck(2048, "lopez_key.pem", "lopez_cert.pem", asubject,
                          c1subject, akey)
c2subject = create_usr_x509(morales, dummy_user_ids[morales["mail"]])
c2cert, c2key = create_ck(2048, "morales_key.pem", "morales_cert.pem",
                          asubject, c2subject, akey)
if len(db.list_certs()) != 0: exit()

add_cert(admin["mail"], acert)
add_cert(badmin["mail"], bcert)
add_cert(lopez["mail"], c1cert)
add_cert(morales["mail"], c2cert)
