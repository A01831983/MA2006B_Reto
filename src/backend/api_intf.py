#! /usr/bin/env python

"""
Defines the API interface of the gestor.
"""

__author__ = "Henning Arvid Ladewig"

from enum import Enum
from datetime import date, datetime

from flask import jsonify
from flask_restx import Api, Resource, fields, reqparse
from cryptography.hazmat.primitives import serialization

import ccore
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


def register(api, db_filename):
    db.init(db_filename) # Open database

    # Schemas
    user_model = {
        "id": StrField("Permanent ID of the user", required=True),
        "name": StrField("Full legal name of the user", required=True),
        "dept": StrField("Department the user is working in", required=True),
        "lvl": EnumField(LevelEnum, description="Access level of the user",
                         required=True,
                         default=LevelEnum.Voluntario.value),
        "mail": StrField("Email address of the user", required=True),
        "joined": fields.Date(description="When the user entered the organisation",
                              required=True)
    }
    User_m = api.model("User", user_model)

    usercreate_model = user_model.copy()
    del usercreate_model["id"]
    UserCreate_m = api.model("UserCreate", usercreate_model)

    usercreatereply_model = {
        "id": StrField("The permament ID of the freshly created user",
                       required=True)
    }
    UserCreateReply_m = api.model("UserCreateReply", usercreatereply_model)

    usermodify_model = {
        "name": StrField("Full legal name of the user", required=False),
        "dept": StrField("Department the user is working in", required=False),
        "lvl": EnumField(LevelEnum, description="Access level of the user",
                         required=False,
                         default=LevelEnum.Voluntario.value),
        "mail": StrField("Email address of the user", required=False),
        "joined": fields.Date(description="When the user entered the organisation",
                              required=False)
    }
    UserModify_m = api.model("UserModify", usermodify_model)

    certinfo_model = {
        "id": StrField("ID of the certificate", required=True),
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

    certcreate_model = {
        "key_size": fields.Integer(description="Key size in bits", min=2048,
                                   required=True),
        "pwd": StrField("The password with which to encrypt the private key",
                        required=True)
    }
    CertCreate_m = api.model("CertCreate", certcreate_model)

    certcreatereply_model = {
        "raw": StrField("Encrypted private key (PEM)", required=True)
    }
    CertCreateReply_m = api.model("CertCreateReply", certcreatereply_model)

    rawcert_model = {
        "raw": StrField("Raw certificate data (PEM)", required=True)
    }
    RawCert_m = api.model("RawCert", rawcert_model)

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

    uid_p = reqparse.RequestParser()
    uid_p.add_argument("uid", type=str, location="args", required=True)

    cert_filter_p = reqparse.RequestParser()
    cert_filter_p.add_argument("cid", type=str, location="args",
                               required=False, default="")
    cert_filter_p.add_argument("uid", type=str, location="args",
                               required=False, default="")
    cert_filter_p.add_argument("valid", type=str, location="args",
                               required=False, default=None)
    cert_filter_p.add_argument("not_before", type=str, location="args",
                               required=False, default=None)
    cert_filter_p.add_argument("not_after", type=str, location="args",
                               required=False, default=None)
    cert_filter_p.add_argument("revoked", type=str, location="args",
                               required=False, default=None)

    cert_create_p = reqparse.RequestParser()
    cert_create_p.add_argument("uid", type=str, location="args",
                               required=True)
    cert_create_p.add_argument("not_before", type=str, location="args",
                               required=True)
    cert_create_p.add_argument("not_after", type=str, location="args",
                               required=True)

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
        }, description="Query registered users")
        @api.marshal_list_with(User_m)
        def get(self):
            args = user_filter_p.parse_args()

            try:
                args["joined_before"] = _des_date(args["joined_before"])
            except ValueError:
                api.abort(400, _des_date_err("joined_before", args["joined_before"]))

            try:
                args["joined_after"] = _des_date(args["joined_after"])
            except ValueError:
                api.abort(400, _des_date_err("joined_after", args["joined_after"]))

            return db.list_users(**args)

        @api.expect(UserCreate_m)
        @api.marshal_with(UserCreateReply_m)
        @api.doc(description="Create a new user")
        def post(self):
            try:
                if "joined" in api.payload.keys():
                    api.payload["joined"] = _des_date(api.payload["joined"])
            except ValueError:
                api.abort(400, _des_date_err("joined", api.payload["joined"]))

            try:
                ret = db.add_user(**api.payload)
            except Exception as e:
                api.abort(400, "Error adding user to database: {e}")
            
            return {"id": ret}

        @api.doc(params={
            "uid": {"description": "The id of the user which to modify",
                    "required": True, "type": str}
        }, description="Change the data of a specific user")
        @api.expect(UserModify_m)
        def patch(self):
            args = uid_p.parse_args(); print(args); print(api.payload)

            usrs = db.list_users(uid=args["uid"])
            if len(usrs) != 1:
                api.abort(400, "uid must match exactly one user's id " + \
                        f"(obtained {len(usrs)} matches)")

            try:
                if "joined" in api.payload.keys():
                    api.payload["joined"] = _des_date(api.payload["joined"])
            except ValueError:
                api.abort(400, _des_date_err("joined", api.payload["joined"]))

            ret = db.change_users(args["uid"], api.payload)

            if ret is not None:
                api.abort(400, ret)

    @api.route("/certs")
    @api.doc(description="Certificate querying and creation")
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
                        "required": False, "type": bool}
        }, description="Query registered certificates")
        @api.marshal_list_with(CertInfo_m)
        def get(self):
            args = cert_filter_p.parse_args()

            if args["valid"] not in (None, "true", "false"):
                api.abort(400, _des_bool_err("valid", args["valid"]))

            if args["revoked"] not in (None, "true", "false"):
                api.abort(400, _des_bool_err("revoked", args["revoked"]))

            args["valid"] = _des_bool(args["valid"])
            args["revoked"] = _des_bool(args["revoked"])

            try:
                args["not_before"] = _des_date(args["not_before"])
            except ValueError:
                api.abort(400, _des_date_err("not_before", args["not_before"]))
            
            try:
                args["not_after"] = _des_date(args["not_after"]); print(args)
            except ValueError:
                api.abort(400, _des_date_err("not_after", args["not_after"]))
            
            try:
                ret = db.list_certs(**args)
            except Exception as e:
                api.abort(500, f"Error querying certificate database: {str(e)}")

            return ret

        @api.doc(params={
            "uid": {
                "description": "The ID of the user which to issue a certificate for",
                "required": True, "type": str},
            "not_before": {"description": "Validity period", "required": True,
                           "type": str},
            "not_after": {"description": "Validity period", "required": True,
                          "type": str}
        }, description="Create new certificate for a specific user")
        @api.expect(CertCreate_m)
        @api.marshal_with(CertCreateReply_m)
        def post(self):
            args = cert_create_p.parse_args()

            # Validate dates
            try:
                not_before = _des_date(args["not_before"])
            except ValueError:
                api.abort(400, _des_date_err("not_before", args["not_before"]))

            try:
                not_after = _des_date(args["not_after"])
            except ValueError:
                api.abort(400, _des_date_err("not_after", args["not_after"]))

            today = date.today()
            if not_after < not_before:
                api.abort(400, "Validity period must start before it ends")
            if not_before < today:
                api.abort(400, "Validity period must not start before current date")
            if not_after < today:
                api.abort(400, "Validity period must end after current date")
            
            # Validate user
            uid_err = "uid must exactly match the ID of one user"

            usrs = db.list_users(uid=args["uid"])
            if len(usrs) != 1: api.abort(400, uid_err)

            usr = usrs[0]
            if usr["id"] != args["uid"]: api.abort(400, uid_err)

            # Validate cryptographical parameters
            key_size = api.payload["key_size"]
            if key_size < 2048:
                api.abort(400, "Key size too small (minimum 2048 bits)")

            usr_without_id_joined = usr.copy()
            del usr_without_id_joined["id"]
            del usr_without_id_joined["joined"]

            try:
                cert, key = ccore.create_cert(
                    uid=usr["id"], **usr_without_id_joined, not_before=not_before,
                    not_after=not_after, pwd=api.payload["pwd"], key_size=key_size)
            except Exception as e:
                api.error(400, f"Error creating certificate: {e}")

            try:
                db.add_cert(usr["id"], cert)
            except Exception as e:
                api.abort(400, f"Error adding certificate to database: {e}")

            return {"raw": key.decode()}

    @api.route("/certs/<string:cid>")
    @api.doc(description="Retrieve raw PEM data of one specific certificate")
    @api.param("cid", "The id of the certificate for which to retrieve the raw PEM data for")
    class RawCert(Resource):
        @api.marshal_with(RawCert_m)
        def get(self, cid):
            certs = db.list_certs(cid=cid)
            
            if len(certs) != 1:
                api.abort(400,
                          "cid match must match exactly one certificate's id" \
                                  + f" (obtained {len(certs)} matches)")

            cert = certs[0]["cert"]
            
            return {"raw": cert.public_bytes(serialization.Encoding.PEM).decode()}

    return api


# Helper functions
def StrField(desc, **kwargs):
    return fields.String(description=desc, **kwargs)

def EnumField(enumcls, **kwargs):
    return fields.String(enum=[e.value for e in enumcls], **kwargs)

def _des_bool(d):
    return d == "true" if d is not None else d

def _des_bool_err(field_name, v):
    return f"Invalid format for '{field_name}': Shall be bool ('true'/'false')" \
            + f", instead received {v}"

def _des_date(d):
    return datetime.strptime(d, DATE_FORMAT).date() if d is not None else d

def _des_date_err(field_name, v):
    return f"Invalid format for '{field_name}': Shall be date as in YYYY-MM-DD"
