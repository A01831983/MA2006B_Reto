#! /usr/bin/env python

import os
import random
from datetime import datetime

from fastapi import FastAPI, Body
from pydantic import BaseModel, Field
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import serialization, hashes

in_script_dir = lambda p: os.path.join(os.path.dirname(__file__), p)

# Load server private key
with open(in_script_dir("server_private_key.pem"), "rb") as f:
    priv_key = serialization.load_pem_private_key(f.read(),
                                                  password=b"123Hola")

# Load server certificate
with open(in_script_dir("server_cert.pem"), "rb") as f:
    srv_cert = x509.load_pem_x509_certificate(f.read())

app = FastAPI()

cert_db = {}  # Certificate database
crl = []      # Certiifcate revocation list
csr_db = {}   # Certificate signing request database


class StatusResultReply(BaseModel):
    status: str = Field(..., description="Indicates whether request was successfull ('success') or not ('failure')")
    result: str = Field(..., description="Request-specific result field. Carries error message upon failure.")



@app.post("/verify")
def verify_cert(cert: str = Body(...)):
    cert = x509.load_pem_x509_certificate(cert.encode())

    return {"status": "success", "result": cert in cert_db.values()}

# Get status of CSR, needs CSR id (returned on POST)
# Returns true when CSR is found, otherwise false
@app.get("/csr", response_model=StatusResultReply)
def get_csr_status(rid: int):
    if not int(rid) in csr_db.keys():
        return {"status": "success", "result": False}

    return {"status": "success", "result": True}


def validify_csr(csr):
    uid = csr.subject.get_attributes_for_oid(NameOID.SERIAL_NUMBER)[0].value
    grp = csr.subject.get_attributes_for_oid(NameOID.ORGANIZATIONAL_UNIT_NAME)\
            [0].value

    int_err = "SERIAL_NUMBER must be integer between 0 and 2^31-1"

    try:
        uid = int(uid)
    except ValueError:
        return int_err

    if uid < 0 or uid > 2**31-1: return int_err

    if grp not in ("Beneficiario", "Admin", "Colaborador", "Operativo"):
        return "ORGANIZATIONAL_UNIT_NAME must be valid"
   

# Post new certificate signing request
@app.post("/csr")
def post_csr(csr: str = Body(...)):
    csr = x509.load_pem_x509_csr(csr.encode()) # Deserialise the CSR

    if not csr.is_signature_valid:
        return {"status": "error", "result": "Signature is invalid"}
    
    if (err := validify_csr(csr)):
        return {"status": "error", "result": err}
    
    rid = random.randint(0, 2**31-1)  # Generate id to identify the CSR
    while rid in csr_db.keys():
        rid = random.randint(0, 2**31-1) # Generate new id

    csr_db[rid] = csr

    return {"status": "success", "result": rid}


# For demonstration purposes
# Approves a certificate signing request
@app.post("/admin/approve")
def approve_csr(rid: int, starting_from: datetime, ending_on: datetime):
    if not int(rid) in csr_db.keys():
        return {"status": "error", "result": "Request ID not found"}

    csr = csr_db[rid]
    email = csr.subject.get_attributes_for_oid(NameOID.EMAIL_ADDRESS)[0].value
    name = csr.subject.get_attributes_for_oid(NameOID.GIVEN_NAME)[0].value
    uid = csr.subject.get_attributes_for_oid(NameOID.SERIAL_NUMBER)[0].value
    grp = csr.subject.get_attributes_for_oid(NameOID.ORGANIZATIONAL_UNIT_NAME)\
            [0].value

    cid = random.randint(0, 2**31-1) # Generate id to identitfy the certificate
    while cid in cert_db.keys():
        cid = random.randint(0, 2**31-1)

    cert = x509.CertificateBuilder().\
        subject_name(csr.subject).\
        issuer_name(srv_cert.subject).\
        public_key(csr.public_key()).\
        serial_number(cid).\
        not_valid_before(starting_from).\
        not_valid_after(ending_on).\
        sign(priv_key, hashes.SHA256())

    cert_db[cid] = cert
    del csr_db[rid]

    print(cert.public_bytes(serialization.Encoding.PEM).decode())

    return {"status": "success", "result": cert.public_bytes(serialization.Encoding.PEM)}
