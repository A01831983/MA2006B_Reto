#! /usr/bin/env python

"""
Defines the API interface of the gestor.
"""

__author__ = "Henning Arvid Ladewig"

from enum import Enum
from datetime import date, datetime

from flask import jsonify
from flask_restx import Api, Resource, fields, reqparse

import db


DATE_FORMAT = "%Y-%m-%d"

# Enums
class StatusEnum(Enum):
    SUCCESS = "success"
    FAILURE = "failure"

class LevelEnum(Enum):
    Administrador = "admin"
    Coordinador = "coordinador"
    Operativo = "operativo"
    Captura = "captura"
    Voluntario = "captura"
    Beneficiario = "beneficiario"

# class CertificateInfo(BaseModel):
#     id: str = Field(..., description="ID of the certificate")
#     uid: str = Field(..., description="Permanent ID of the user this certificate is issued for")
#     lvl: Levels = Field(..., description="To which access level this certificate provides access")
#     not_before: datetime = Field(..., description="Timepoint from which on this certificate is valid")
#     not_after: datetime = Field(..., description="Timepoint from which on this certificate is invalid")
#     revocated: bool = Field(..., description="Indicates whether this certificate is revocated")
#     raw: str = Field(..., description="PEM certificate string")
def register(api, db_filename):
    db.init(db_filename) # Open database

    # Schemas
    StatusResult_m = api.model("StatusReply", {
        "status": EnumField(StatusEnum, required=True, description="Status"),
        "result": StrField("Result (error message in case of failure)", required=False,
                           default="")
    })

    user_model = {
        "id": StrField("Permanent ID of the user", required=True),
        "name": StrField("Full legal name of the user", required=True),
        "dept": StrField("Department the user is working in", required=True),
        "lvl": EnumField(LevelEnum, description="Access level of the user", required=True,
                         default=LevelEnum.Beneficiario.value),
        "mail": StrField("Email address of the user", required=True),
        "joined": fields.Date(description="When the user entered the organisation", required=True)
    }
    User_m = api.model("User", user_model)

    usercreate_model = user_model.copy()
    del usercreate_model["id"]
    UserCreate_m = api.model("UserCreate", usercreate_model)

    certinfo_model = {
        "id": StrField("ID of the certificage", required=True),
        "uid": StrField("Permanent ID of the user this certificate is issued for",
                        required=True),
        "not_before": fields.Date(description="Timepoint from which on this certificate is valid",
                                  required=True),
        "not_after": fields.Date(description="Timepoint from which on this certificate is invalid",
                                 required=True),
        "revoked": fields.Boolean(description="Indicates whether this certificate is revoked",
                                  required=True)
    }
    CertInfo_m = api.model("CertInfo", certinfo_model)

    certcreate_model = certinfo_model.copy()
    del certcreate_model["id"]
    CertCreate_m = api.model("CertCreate", certcreate_model)

    # Query Parameter Parsers
    user_filter_p = reqparse.RequestParser()
    user_filter_p.add_argument("uid", type=str, location="args",
                               required=False, default="")
    user_filter_p.add_argument("name", type=str, location="args",
                               required=False, default="")
    user_filter_p.add_argument("dept", type=str, location="args",
                               required=False, default="")
    user_filter_p.add_argument("lvl", type=str, location="args",
                               required=False, default="")
    user_filter_p.add_argument("mail", type=str, location="args",
                               required=False, default="")
    user_filter_p.add_argument("joined_before", type=str, location="args",
                               required=False, default=None)
    user_filter_p.add_argument("joined_after", type=str, location="args",
                               required=False, default=None)

    cert_filter_p = reqparse.RequestParser()
    cert_filter_p.add_argument("cid", type=str, location="args",
                               required=False, default="")
    cert_filter_p.add_argument("uid", type=str, location="args",
                               required=False, default="")
    cert_filter_p.add_argument("valid", type=str, location="args",
                               required=False, default=None)
    cert_filter_p.add_argument("not_before", type=date, location="args",
                               required=False, default=None)
    cert_filter_p.add_argument("not_after", type=date, location="args",
                               required=False, default=None)
    cert_filter_p.add_argument("revoked", type=bool, location="args",
                               required=False, default=None)

    # Endpoints
    @api.route("/users")
    class Users(Resource):
        @api.doc(params={
            "uid": {"description": "Restrict by user ID",
                    "required": False, "type": str},
            "name": {"description": "Restrict by name", "required": False,
                     "type": str},
            "dept": {"description": "Restrict by department", "required": False,
                     "type": str},
            "lvl": {"description": "Restrict by access level",
                    "required": False, "type": str},
            "mail": {"description": "Restrict by email address",
                     "required": False, "type": str},
            "joined_before": {"description": "Restrict by join date (YYYY-MM-DD)",
                              "required": False, "type": str},
            "joined_after": {"description": "Restrict by join date (YYYY-MM-DD)",
                             "required": False, "type": str}
        })
        @api.marshal_list_with(User_m)
        def get(self):
            args = user_filter_p.parse_args()
            args["joined_before"] = _des_date(args["joined_before"])
            args["joined_after"] = _des_date(args["joined_after"])
            return db.list_users(**args)

        @api.expect(UserCreate_m)
        @api.marshal_with(StatusResult_m)
        def post(self):
            api.payload["joined"] = _des_date(api.payload["joined"])
            
            return {"status": "success", "result": db.add_user(**api.payload)}

    @api.route("/users/me")
    class OwnUser(Resource):
        @api.marshal_with(User_m)
        def get(self): return db.list_users(name="Max Mustermann")[0]

    @api.route("/certs")
    class Certs(Resource):
        @api.doc(params={
            "cid": {"description": "Restrict by certificate ID",
                    "required": False, "type": str},
            "uid": {"description": "Restrict by user ID", "required": False,
                    "type": str},
            "valid": {"description": "Restrict to currently valid certificates",
                      "required": False, "type": bool},
            "not_before": {
                "description": "Restrict by certificate validity period (YYYY-MM-DD)",
                "required": False, "type": str},
            "not_after": {
                "description": "Restrict by certificate validity period (YYYY-MM-DD)",
                "required": False, "type": str},
            "revoked": {"description": "Restrict by revocation status",
                        "required": False, "type": str}
        })
        @api.marshal_list_with(CertInfo_m)
        def get(self):
            args = cert_filter_p.parse_args()
            args["valid"] = _des_bool(args["valid"])
            args["not_before"] = _des_date(args["not_before"])
            args["not_after"] = _des_date(args["not_after"])

            return db.list_certs(**args)

    @api.route("/certs/me")
    class OwnCerts(Resource):
        @api.doc(params={
            "cid": {"description": "Restrict by certificate ID",
                    "required": False, "type": str},
            "valid": {"description": "Restrict to currently valid certificates",
                      "required": False, "type": bool},
            "not_before": {
                "description": "Restrict by certificate validity period (YYYY-MM-DD)",
                "required": False, "type": str},
            "not_after": {
                "description": "Restrict by certificate validity period (YYYY-MM-DD)",
                "required": False, "type": str},
            "revoked": {"description": "Restrict by revocation status",
                        "required": False, "type": str}
        })
        @api.marshal_with(CertInfo_m)
        def get(self):
            args = cert_filter_p.parse_args()
            args["valid"] = _des_bool(args["valid"])
            args["not_before"] = _des_date(args["not_before"])
            args["not_after"] = _des_date(args["not_after"])
            del args["uid"]

            uid = db.list_users(name="Max Mustermann")[0]["id"]
            return db.list_certs(uid=uid, **args)

    return api


# Helper functions
def StrField(desc, **kwargs):
    return fields.String(description=desc, **kwargs)

def EnumField(enumcls, **kwargs):
    return fields.String(enum=[e.value for e in enumcls], **kwargs)

def _des_bool(d):
    return d == "true" if d is not None else d

def _des_date(d):
    return datetime.strptime(d, DATE_FORMAT).date() if d is not None else d


# API Endpoints

# import builtins
# from enum import Enum
# from typing import List, Optional
# from datetime import datetime

# from cryptography import x509
# from fastapi import Depends, Query
# from pydantic import BaseModel, Field, EmailStr

# CertificateInfoList = List[CertificateInfo]

# class CertificateCreationReply(StatusReply):
#     result: str = Field(..., description="Certificate ID in case of success or error message on failure")

# class CSRStatus(BaseModel):
#     id: str = Field(..., description="ID of the certificate signing request")
#     uid: str = Field(..., description="User ID this certificate shall belong to")
#     lvl: Levels = Field(..., description="Which access level this certificate shall grant")

# CSRStatusList = List[CSRStatus]

# class CSRStatusFilter(BaseModel):
#     rid: Optional[str] = None
#     uid: Optional[str] = None
#     lvl: Optional[Levels] = None

# class CSRApprovalReply(StatusReply):
#     result: str = Field(..., description="Certificate ID in case of success or error message on failure")


# API endpoints
# Users

# Certificates
# def list_certs(filters: CertificateFilter = Depends()):
#     filter_ = lambda c: \
        #         (c.id == filters.cid if filters.cid is not None else True) and \
        #         (c.uid == filters.uid if filters.uid is not None else True) and \
        #         (c.lvl == filters.lvl if filters.lvl is not None else True)
#     return builtins.filter(filter_, dummy_certis)

# def create_cert(cert: CertificateInfo):
#     if cert.id in map(lambda c: c.id, dummy_certis):
#         return CertificateCreationReply(status=StatusEnum.FAILURE,
#                                         result="Certificate ID already occupied")
#     dummy_certis.append(cert)

#     return CertificateCreationReply(status=StatusEnum.SUCCESS, result=cert.id)

# def get_own_certs():
#     return [dummy_certis[0]]

# Certificate Signing Requests
# dummy_csrss = [
#     CSRStatus(id="199", uid="3", lvl=Levels.Captura, raw=""),
#     CSRStatus(id="200", uid="7", lvl=Levels.Coordinador, raw="")
# ]
# def list_csrs(filters: CSRStatusFilter = Depends()):
#     filter_ = lambda r: \
        #         (r.id == filters.rid if filters.rid is not None else True) and \
        # (r.uid == filters.uid if filters.uid is not None else True) and \
        # (r.lvl == filters.lvl if filters.lvl is not None else True)
#     return builtins.filter(filter_, dummy_csrss)

# def approve_csr(rid: str = Query(description="ID of the CSR to approve")):
#     if not rid in map(lambda r: r.id, dummy_csrss):
#         return CSRApprovalReply(status=StatusEnum.FAILURE, result="CSR not found")

#     return CSRApprovalReply(status=StatusEnum.SUCCESS, result="")
