#! /usr/bin/env python

"""
Defines the API interface of the gestor.
"""

__author__ = "Henning Arvid Ladewig"

import builtins
from enum import Enum
from typing import List, Optional
from datetime import datetime

from cryptography import x509
from fastapi import Depends, Query
from pydantic import BaseModel, Field, EmailStr



# Schemas
class StatusEnum(Enum):
    SUCCESS = "success"
    FAILURE = "failure"

class StatusReply(BaseModel):
    status: StatusEnum = Field(..., description="Status of the request")

class User(BaseModel):
    id: str = Field(..., description="Permanent ID of the user")
    name: str = Field(..., description="Full legal name of the user")
    dept: str = Field(..., description="Department the user is working in")
    mail: EmailStr = Field(..., description="Email address of the user")
    joined: datetime = Field(..., description="When the user entered the organisation")

UserList = List[User]

class UserFilter(BaseModel):
    uid: Optional[str] = Field(None, description="Restrict by user ID")

class UserCreationReply(StatusReply):
    result: str = Field(..., description="User ID in case of success or error message on failure")

class Levels(Enum):
    Administrador = "admin"
    Coordinador = "coordinador"
    Operativo = "operativo"
    Captura = "captura"
    Voluntario = "captura"
    Beneficiario = "beneficiario"

class CertificateInfo(BaseModel):
    id: str = Field(..., description="ID of the certificate")
    uid: str = Field(..., description="Permanent ID of the user this certificate is issued for")
    lvl: Levels = Field(..., description="To which access level this certificate provides access")
    not_before: datetime = Field(..., description="Timepoint from which on this certificate is valid")
    not_after: datetime = Field(..., description="Timepoint from which on this certificate is invalid")
    revocated: bool = Field(..., description="Indicates whether this certificate is revocated")
    raw: str = Field(..., description="PEM certificate string")

CertificateInfoList = List[CertificateInfo]

class CertificateFilter(BaseModel):
    cid: Optional[str] = Field(None, description="Restrict by certificate ID")
    uid: Optional[str] = Field(None, description="Restrict by user ID")
    lvl: Optional[Levels] = Field(None, description="Restrict by access level")

class CertificateCreationReply(StatusReply):
    result: str = Field(..., description="Certificate ID in case of success or error message on failure")

class CSRStatus(BaseModel):
    id: str = Field(..., description="ID of the certificate signing request")
    uid: str = Field(..., description="User ID this certificate shall belong to")
    lvl: Levels = Field(..., description="Which access level this certificate shall grant")

CSRStatusList = List[CSRStatus]

class CSRStatusFilter(BaseModel):
    rid: Optional[str] = None
    uid: Optional[str] = None
    lvl: Optional[Levels] = None

class CSRApprovalReply(StatusReply):
    result: str = Field(..., description="Certificate ID in case of success or error message on failure")


# API endpoints
# Users
now = datetime.now()
dummy_users = [
    User(id="0", name="Max Mustermann", dept="TI", mail="admin@casamonarca.mx", joined=now),
    User(id="1", name="María López", dept="Legal", mail="m.lopez@casamonarca.mx", joined=now),
    User(id="2", name="José Ramírez", dept="Humanitaria", mail="j.ramirez@casamonarca.mx", joined=now),
    User(id="3", name="Ana González", dept="Salud", mail="a.gonzalez@casamonarca.mx", joined=now),
    User(id="4", name="Carlos Vega", dept="Legal", mail="c.vega@casamonarca.mx", joined=now),
    User(id="5", name="Lucía Morales", dept="Educativa", mail="l.morales@casamonarca.mx", joined=now),
    User(id="6", name="Roberto Salas", dept="Humanitaria", mail="r.salas@casamonarca.mx", joined=now),
    User(id="7", name="Diana Fuentes", dept="Salud", mail="d.fuentes@casamonarca.mx", joined=now)
]

def list_users(filters: UserFilter = Depends()):
    filter_ = lambda u: u.id == filters.uid if filters.uid is not None else True
    return builtins.filter(filter_, dummy_users)

def create_user(user: User):
    if user.id in map(lambda u: u.id, dummy_users):
        return UserCreationReply(status=StatusEnum.FAILURE,
                                 result="User ID already occupied")

    dummy_users.append(user)

    return UserCreationReply(status=StatusEnum.SUCCESS, result=user.id)

def get_own_user():
    return dummy_users[0]

# Certificates
begin = datetime(2024, 1, 1)
end = datetime(2025, 6, 15)
dummy_certis = [
    CertificateInfo(id="0", uid="0", lvl=Levels.Administrador,
                    not_before=begin, not_after=end, revocated=False, raw=""),
    CertificateInfo(id="CM-2024-0041", uid="1", lvl=Levels.Coordinador,
                    not_before=begin, not_after=end, revocated=False, raw=""),
    CertificateInfo(id="2", uid="2", lvl=Levels.Operativo, not_before=begin,
                    not_after=end, revocated=False, raw="")
]
def list_certs(filters: CertificateFilter = Depends()):
    filter_ = lambda c: \
        (c.id == filters.cid if filters.cid is not None else True) and \
        (c.uid == filters.uid if filters.uid is not None else True) and \
        (c.lvl == filters.lvl if filters.lvl is not None else True)
    return builtins.filter(filter_, dummy_certis)

def create_cert(cert: CertificateInfo):
    if cert.id in map(lambda c: c.id, dummy_certis):
        return CertificateCreationReply(status=StatusEnum.FAILURE,
                                        result="Certificate ID already occupied")
    dummy_certis.append(cert)

    return CertificateCreationReply(status=StatusEnum.SUCCESS, result=cert.id)

def get_own_certs():
    return [dummy_certis[0]]

# Certificate Signing Requests
dummy_csrss = [
    CSRStatus(id="199", uid="3", lvl=Levels.Captura),
    CSRStatus(id="200", uid="7", lvl=Levels.Coordinador)
]
def list_csrs(filters: CSRStatusFilter = Depends()):
    filter_ = lambda r: \
        (r.id == filters.rid if filters.rid is not None else True) and \
        (r.uid == filters.uid if filters.uid is not None else True) and \
        (r.lvl == filters.lvl if filters.lvl is not None else True)
    return builtins.filter(filter_, dummy_csrss)

def approve_csr(rid: str = Query(description="ID of the CSR to approve")):
    if not rid in map(lambda r: r.id, dummy_csrss):
        return CSRApprovalReply(status=StatusEnum.FAILURE, result="CSR not found")

    return CSRApprovalReply(status=StatusEnum.SUCCESS, result="")

