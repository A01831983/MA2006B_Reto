#! /usr/bin/env python

"""
Defines the API interface of the gestor.
"""

__author__ = "Henning Arvid Ladewig"

from enum import Enum
from datetime import date, datetime

from flask import jsonify, render_template, Response
from flask_restx import Api, Resource, fields, reqparse
from cryptography import x509
from cryptography.hazmat.primitives import serialization
import validators

from . import ccore
from . import db


DATE_FORMAT = "%Y-%m-%d"

# Enums
class DeptEnum(Enum):
    Humanitaria = "Humanitaria"
    PsicoSocial = "PsicoSocial"
    Legal = "Legal"
    Comunicacion = "Comunicación"
    Almacen = "Alamcén"
    TI = "TI"
depts = tuple(d.value for d in DeptEnum)

class LevelEnum(Enum):
    Administrador = "admin"
    Coordinador = "coordinador"
    Operativo = "operativo"
    Captura = "captura"
    Voluntario = "captura"
lvls = tuple(l.value for l in LevelEnum)


def register(api, db_filename):
    db.init(db_filename) # Open database

    # Schemas
    user_model = {
        "id": StrField("Permanent ID of the user", required=True),
        "name": StrField("Full legal name of the user", required=True),
        "dept": EnumField(DeptEnum,
                          description="Department the user is working in",
                          required=True),
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
        "dept": EnumField(DeptEnum,
                          description="Department the user is working in",
                          required=False),
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
        "id": StrField("The id of the freshly generated certificate",
                       required=True),
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
    @api.route("/")
    class HomePage(Resource):
        def get(self):
            return Response(render_template("index.html"),
                            mimetype="text/html")

    @api.route("/users")
    class Users(Resource):
        @api.doc(params={
            "uid": {"description": "Restrict by user ID",
                    "required": False, "type": str},
            "name": {"description": "Restrict by name", "required": False,
                     "type": str},
            "dept": {"description": "Restrict by department", "required": False,
                     "type": str, "enum": depts},
            "lvl": {"description": "Restrict by access level",
                    "required": False, "type": str, "enum": lvls},
            "mail": {"description": "Restrict by email address",
                     "required": False, "type": str},
            "joined_before": {"description": "Restrict by join date (YYYY-MM-DD)",
                              "required": False, "type": str, "format": "date"},
            "joined_after": {"description": "Restrict by join date (YYYY-MM-DD)",
                             "required": False, "type": str, "format": "date"}
        }, description="Query registered users")
        @api.marshal_list_with(User_m)
        def get(self):
            args = user_filter_p.parse_args()

            if "dept" in args.keys():
                if args["dept"] != "" and args["dept"] not in depts:
                    api.abort(400, _chk_dept_err(args["dept"]))

            if "lvl" in args.keys():
                if args["lvl"] != "" and args["lvl"] not in lvls:
                    api.abort(400, _chk_lvl_err(args["lvl"]))

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
            if "mail" in api.payload.keys():
                if not validators.email(api.payload["mail"]):
                    api.abort(400, "'mail' must be a valid email")

            try:
                if "joined" in api.payload.keys():
                    api.payload["joined"] = _des_date(api.payload["joined"])
            except ValueError:
                api.abort(400, _des_date_err("joined", api.payload["joined"]))

            try:
                ret = db.add_user(**api.payload)
            except Exception as e:
                api.abort(400, f"Error adding user to database: {e}")
            
            return {"id": ret}

        @api.doc(params={
            "uid": {"description": "The id of the user which to modify (must match uniquely)",
                    "required": True, "type": str}
        }, description="Change the data of a specific user")
        @api.expect(UserModify_m)
        def patch(self):
            args = uid_p.parse_args()

            usrs = db.list_users(uid=args["uid"])
            if len(usrs) != 1:
                api.abort(400, _not_unique_err("uid", "user", len(usrs)))

            if "mail" in api.payload.keys():
                if not validators.email(api.payload["mail"]):
                    api.abort(400, "'mail' must be a valid email")

            try:
                if "joined" in api.payload.keys():
                    api.payload["joined"] = _des_date(api.payload["joined"])
            except ValueError:
                api.abort(400, _des_date_err("joined", api.payload["joined"]))

            try:
                ret = db.change_users(args["uid"], api.payload)
            except Exception as e:
                api.abort(400, f"Error changing user data in database: {e}")

            if ret is not None:
                api.abort(400, ret)

        @api.doc(params={
            "uid": {"description": "The id of the user which to remove (must match uniquely)",
                    "required": True, "type": str}
        }, description="Remove a specific user")
        def delete(self):
            args = uid_p.parse_args()

            usrs = db.list_users(uid=args["uid"])
            if len(usrs) != 1:
                api.abort(400, _not_unique_err("uid", "user", len(usrs)))
            try:
                ret = db.delete_users(args["uid"])
            except Exception as e:
                api.abort(400, f"Error removing user from database: {e}")

    @api.route("/certs")
    @api.doc(description="Certificate querying and creation")
    class Certs(Resource):
        @api.doc(params={
            "cid": {"description": "Restrict by certificate ID",
                    "required": False, "type": str},
            "uid": {"description": "Restrict by user ID", "required": False,
                    "type": str},
            "valid": {"description": "Restrict by certificate validity",
                      "required": False, "type": bool},
            "not_before": {
                "description": "Restrict by certificate validity period (YYYY-MM-DD)",
                "required": False, "type": str, "format": "date"},
            "not_after": {
                "description": "Restrict by certificate validity period (YYYY-MM-DD)",
                "required": False, "type": str, "format": "date"},
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
                args["not_after"] = _des_date(args["not_after"])
            except ValueError:
                api.abort(400, _des_date_err("not_after", args["not_after"]))
            
            try:
                ret = db.list_certs(**args)
            except Exception as e:
                api.abort(500, f"Error querying certificate database: {str(e)}")

            return ret

        @api.expect(RawCert_m)
        def post(self):
            def get_admin_certs() -> [x509.Certificate]:
                admins = map(lambda u: u["id"],
                             db.list_users(lvl=LevelEnum.Administrador.value))

                admins_certs = map(lambda uid: db.list_certs(uid=uid), admins)

                admin_certs = [cert for certs in admins_certs for cert in certs]

                admin_certs = list(map(lambda c: c["cert"], admin_certs))

                return admin_certs

            cert = api.payload["raw"]

            try:
                cert = x509.load_pem_x509_certificate(cert.encode())
            except ValueError:
                api.abort(400, "Invalid certificate format")

            usr = ccore.extract_user_data(cert)

            if isinstance(usr, str):
                api.abort(400, usr)

            usrs = db.list_users(**usr)

            if len(usrs) != 1:
                api.abort(400, _not_unique_err("The certificate's details",
                                               "user", len(usrs)))

            found_usr = usrs[0]
            usr["id"] = usr["uid"]
            del usr["uid"]

            if not all([found_usr[k] == usr[k] for k in usr.keys()]):
                api.abort(400, "Certificate details must match user details exactly")

            if not ccore.verify_cert(cert, get_admin_certs()):
                api.abort(400, "Certificate is not signed by a registered administrator")

            # Prevent duplicate certificates
            if len(db.list_certs(pb=cert.public_bytes(serialization.Encoding.PEM))) != 0:
                api.abort(400, "Certificate already registered")

            db.add_cert(usr["id"], cert)

    @api.route("/certs/<string:cid>")
    @api.doc(description="Retrieve raw PEM data of one specific certificate")
    @api.param("cid", "The id of the certificate for which to retrieve the raw PEM data for")
    class RawCert(Resource):
        @api.marshal_with(RawCert_m)
        def get(self, cid):
            certs = db.list_certs(cid=cid)
            
            if len(certs) != 1:
                api.abort(400,
                          _not_unique_err("cid", "certificate", len(certs)))

            cert = certs[0]["cert"]
            
            return {"raw": cert.public_bytes(serialization.Encoding.PEM).decode()}

#    return api

#'''
    # mail
    from . import pgp_core

    pgp_key_model = api.model("PGPKeyCreate", {
        "uid": StrField("User id", required=True),
        "public_key_armored": StrField("Public PGP key", required=True)
    })

    attachment_model = api.model("MailAttachment", {
        "filename": StrField("Attachment filename", required=True),
        "mime": StrField("MIME type", required=True),
        "content_b64": StrField("Attachment content in base64", required=True)
    })

    mail_create_model = api.model("MailCreate", {
        "uid": StrField("Sender uid", required=True),
        "subject": StrField("Mail subject", required=True),
        "body": StrField("Mail body", required=True),
        "private_key_armored": StrField("Private PGP key", required=True),
        "password": StrField("Private key password", required=True),
        "attachments": fields.List(fields.Nested(attachment_model), required=False)
    })

    mail_info_model = api.model("MailInfo", {
        "id": StrField("Message id", required=True),
        "sender_uid": StrField("Sender uid", required=True),
        "subject": StrField("Mail subject", required=True),
        "body": StrField("Mail body", required=True),
        "body_sig": StrField("Detached signature", required=True),
        "sender_fingerprint": StrField("Sender key fingerprint", required=True),
        "created_at": StrField("Creation timestamp", required=True),
        "attachments": fields.List(fields.Raw, required=False)
    })

    verify_reply_model = api.model("MailVerifyReply", {
        "message_ok": fields.Boolean(required=True),
        "attachments_ok": fields.Boolean(required=True),
        "signer_uid": StrField("Signer uid", required=True),
        "fingerprint": StrField("Key fingerprint", required=True),
        "details": StrField("Verification details", required=True)
    })

    pgpkeyinfo_model = api.model("PGPKeyInfo", {
        "uid": StrField("User id", required=True),
        "fingerprint": StrField("Fingerprint", required=True),
        "active": fields.Boolean(required=True),
        "revoked": fields.Boolean(required=True),
        "created_at": StrField("Creation time", required=True)
    })

    @api.route("/pgp/keys")
    class PGPKeysResource(Resource):
        @api.marshal_list_with(pgpkeyinfo_model)
        def get(self):
            return db.list_pgp_keys()

        @api.expect(pgp_key_model)
        def post(self):
            payload = api.payload
            usrs = db.list_users(uid=payload["uid"])
            if len(usrs) != 1:
                api.abort(400, "User not found uniquely")

            fpr = pgp_core.fingerprint_of_public_key(payload["public_key_armored"])
            db.add_pgp_key(payload["uid"], fpr, payload["public_key_armored"])
            return {"uid": payload["uid"], "fingerprint": fpr}, 201
    
    @api.route("/mail")
    class MailResource(Resource):
        @api.marshal_list_with(mail_info_model)
        def get(self):
            messages = db.list_mail_messages()
            for msg in messages:
                msg["attachments"] = db.get_mail_attachments(msg["id"])
            return messages

        @api.expect(mail_create_model)
        def post(self):
            payload = api.payload
            usrs = db.list_users(uid=payload["uid"])
            if len(usrs) != 1:
                api.abort(400, "User not found uniquely")

            usr = usrs[0]
            if usr["lvl"] not in {"admin", "coordinador"}:
                api.abort(403, "User is not allowed to sign mail")

            pubkey = db.get_active_pgp_key(payload["uid"])
            if pubkey is None:
                api.abort(400, "No active public PGP key registered for this user")

            canonical_body = pgp_core.canonicalize_body(payload["subject"], payload["body"])
            body_sig = pgp_core.sign_text_detached(
                payload["private_key_armored"],
                payload["password"],
                canonical_body
            )

            msg_id = db.add_mail_message(
                payload["uid"],
                payload["subject"],
                payload["body"],
                body_sig,
                pubkey["fingerprint"]
            )

            for att in payload.get("attachments", []):
                raw = pgp_core.b64decode_bytes(att["content_b64"])
                sig = pgp_core.sign_bytes_detached(
                    payload["private_key_armored"],
                    payload["password"],
                    raw
                )
                db.add_mail_attachment(
                    msg_id,
                    att["filename"],
                    att["mime"],
                    att["content_b64"],
                    sig,
                    pgp_core.sha256_bytes(raw)
                )

            return {"id": msg_id}, 201

    @api.route("/mail/<string:message_id>/verify")
    class MailVerify(Resource):
        @api.marshal_with(verify_reply_model)
        def get(self, message_id):
            msg = db.get_mail_message(message_id)
            if msg is None:
                api.abort(404, "Message not found")

            pubkey = db.get_active_pgp_key(msg["sender_uid"])
            if pubkey is None:
                api.abort(400, "Signer has no active public key")

            canonical_body = pgp_core.canonicalize_body(msg["subject"], msg["body"])
            body_ok = pgp_core.verify_text_detached(
                pubkey["public_key_armored"],
                canonical_body,
                msg["body_sig"]
            )

            atts = db.get_mail_attachments(message_id)
            atts_ok = True
            for att in atts:
                raw = pgp_core.b64decode_bytes(att["content_b64"])
                ok = pgp_core.verify_bytes_detached(
                    pubkey["public_key_armored"],
                    raw,
                    att["sig_b64"]
                )
                if not ok:
                    atts_ok = False
                    break

            return {
                "message_ok": body_ok,
                "attachments_ok": atts_ok,
                "signer_uid": msg["sender_uid"],
                "fingerprint": msg["sender_fingerprint"],
                "details": "Valid signature" if body_ok and atts_ok else "Invalid signature or modified content"
            }
#'''

    return api



# Helper functions
def StrField(desc, **kwargs):
    return fields.String(description=desc, **kwargs)

def EnumField(enumcls, **kwargs):
    return fields.String(enum=[e.value for e in enumcls], **kwargs)

def _not_unique_err(field_name, object_name, matches):
    return f"{field_name} must match exactly one {object_name}'s id " + \
            f"(obtained {matches} matches)"

def _des_bool(d):
    return d == "true" if d is not None else d

def _des_bool_err(field_name, v):
    return f"Invalid format for '{field_name}': Shall be bool ('true'/'false')" \
            + f", instead received {v}"

def _chk_dept_err(dept):
    depts_str = "', '".join(depts)

    return f"Department '{dept}' invalid; Must be one of '{depts_str}'"

def _chk_lvl_err(lvl):
    lvls_str = "', '".join(lvls)

    return f"Access level '{lvl}' invalid; Must be one of '{lvls_str}'"

def _des_date(d):
    return datetime.strptime(d, DATE_FORMAT).date() if d is not None else d

def _des_date_err(field_name, v):
    return f"Invalid format for '{field_name}': Shall be date as in YYYY-MM-DD"
