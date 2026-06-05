#! /usr/bin/env python

"""
Defines the API interface of the gestor.
"""

__author__ = "Henning Arvid Ladewig, Ximena Montes Bautista, Valeria Arciga Valencia"

from enum import Enum
import os
from datetime import date, datetime, timedelta
import secrets

from flask import jsonify, render_template, Response, request
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
lvls = tuple(l.value for l in LevelEnum)


def register(api, db_filename):
    db.init(db_filename) # Open database
    _bootstrap_admin()

    # Schemas
    user_model = {
        "id": StrField("Permanent ID of the user", required=True),
        "name": StrField("Full legal name of the user", required=True),
        "dept": EnumField(DeptEnum,
                          description="Department the user is working in",
                          required=True),
        "lvl": EnumField(LevelEnum, description="Access level of the user",
                         required=True,
                         default=LevelEnum.Captura.value),
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
                       required=True),
        "temp_password": StrField("The temporary password assigned to the user. "
                                  "Must be shared with the user; they will be "
                                  "asked to change it on first login.",
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
                         default=LevelEnum.Captura.value),
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
            from . import auth

            actor = _get_current_user_from_token()
            if actor is None:
                api.abort(401, "Authentication required")

            target_lvl = api.payload.get("lvl", "")

            if actor["lvl"] == "admin":
                pass
            elif actor["lvl"] == "coordinador":
                if target_lvl not in ("operativo", "captura"):
                    api.abort(403, "Coordinators can only create operativo or captura users")
            else:
                api.abort(403, "You are not allowed to create users")

            if "mail" in api.payload.keys():
                if not validators.email(api.payload["mail"]):
                    api.abort(400, "'mail' must be a valid email")

            try:
                if "joined" in api.payload.keys():
                    api.payload["joined"] = _des_date(api.payload["joined"])
            except ValueError:
                api.abort(400, _des_date_err("joined", api.payload["joined"]))

            try:
                new_uid = db.add_user(**api.payload)
            except Exception as e:
                api.abort(400, f"Error adding user to database: {e}")

            temp_password = auth.generate_temp_password()
            password_hash = auth.hash_password(temp_password)
            db.set_auth(new_uid, password_hash, must_change=True)

            return {"id": new_uid, "temp_password": temp_password}

        @api.doc(params={
            "uid": {"description": "The id of the user which to modify (must match uniquely)",
                    "required": True, "type": str}
        }, description="Change the data of a specific user")
        @api.expect(UserModify_m)
        def patch(self):
            actor = _get_current_user_from_token()
            if actor is None:
                api.abort(401, "Authentication required")

            args = uid_p.parse_args()

            usrs = db.list_users(uid=args["uid"])
            if len(usrs) != 1:
                api.abort(400, _not_unique_err("uid", "user", len(usrs)))

            target_user = usrs[0]

            if actor["lvl"] == "admin":
                pass
            elif actor["lvl"] == "coordinador":
                if target_user["dept"] != actor["dept"]:
                    api.abort(403, "Coordinators can only edit users in their own department")
                if target_user["lvl"] not in ("operativo", "captura"):
                    api.abort(403, "Coordinators can only edit operativo or captura users")
                new_lvl = api.payload.get("lvl")
                if new_lvl and new_lvl not in ("operativo", "captura"):
                    api.abort(403, "Coordinators cannot promote users to admin or coordinador")
            else:
                api.abort(403, "You are not allowed to edit users")

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

#'''
    # mail
    from . import mail_crypto

    attachment_model = api.model("MailAttachment", {
        "filename": StrField("Attachment filename", required=True),
        "mime": StrField("MIME type", required=True),
        "content_b64": StrField("Attachment content in base64", required=True),
        "sig": StrField("Detached signature for attachment", required=True)
    })

    mail_create_model = api.model("MailCreate", {
        "uid": StrField("Sender uid", required=True),
        "recipient": StrField("Mail recipient", required=True),
        "subject": StrField("Mail subject", required=True),
        "body": StrField("Mail body", required=True),
        "body_sig": StrField("Detached signature for canonical mail body", required=True),
        "attachments": fields.List(fields.Nested(attachment_model), required=False)
    })

    mail_info_model = api.model("MailInfo", {
        "id": StrField("Message id", required=True),
        "sender_uid": StrField("Sender uid", required=True),
        "recipient": StrField("Recipient", required=True),
        "subject": StrField("Mail subject", required=True),
        "body": StrField("Mail body", required=True),
        "body_sig": StrField("Detached signature", required=True),
        "cert_id": StrField("Signing certificate id", required=True),
        "signing_cert_fingerprint": StrField("Signing certificate fingerprint", required=True),
        "created_at": StrField("Creation timestamp", required=True),
        "validation_token": StrField("One-time verification token", required=False),
        "validation_url": StrField("Public verification URL (ephemeral)", required=False),
        "expires_at": StrField("Token expiry timestamp (ISO-8601 UTC)", required=False),
        "attachments": fields.List(fields.Raw, required=False)
    })

    verify_reply_model = api.model("MailVerifyReply", {
        "message_ok": fields.Boolean(required=True),
        "attachments_ok": fields.Boolean(required=True),
        "certificate_ok": fields.Boolean(required=True),
        "signer_uid": StrField("Signer uid", required=True),
        "fingerprint": StrField("Key fingerprint", required=True),
        "details": StrField("Verification details", required=True)
    })

    public_verify_model = api.model("PublicVerifyReply", {
        "message_ok": fields.Boolean(required=True),
        "certificate_ok": fields.Boolean(required=True),
        "signer_uid": StrField("Signer uid", required=True),
        "fingerprint": StrField("Signing certificate SHA-256 fingerprint", required=True),
        "subject": StrField("Mail subject", required=True),
        "recipient": StrField("Mail recipient", required=True),
        "created_at": StrField("Message creation timestamp", required=True),
        "details": StrField("Human-readable verification result", required=True)
    })

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

            valid_certs = db.list_certs(uid=payload["uid"], valid=True, revoked=False)
            if len(valid_certs) == 0:
                api.abort(400, "User has no active official certificate")

            cert_rec = valid_certs[0]
            cert = cert_rec["cert"]
            cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode()

            canonical_body = mail_crypto.canonicalize_body(
                payload["subject"],
                payload["recipient"],
                payload["body"]
            )

            body_ok = mail_crypto.verify_bytes(
                cert_pem,
                canonical_body,
                payload["body_sig"]
            )
            if not body_ok:
                api.abort(400, "Invalid body signature")

            recipient_lower = payload["recipient"].strip().lower()
            recipient_users = db.list_users(mail=recipient_lower)
            is_external = len(recipient_users) == 0

            if is_external:
                validation_token = secrets.token_hex(16).upper()
                expires_at = (datetime.utcnow() + timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S")
                base_url = os.environ.get("PUBLIC_BASE_URL", "http://localhost:8000/api")
                validation_url = base_url + "/public/verify/" + validation_token
            else:
                validation_token = None
                expires_at = None
                validation_url = None

            msg_id = db.add_mail_message(
                payload["uid"],
                payload["recipient"],
                payload["subject"],
                payload["body"],
                payload["body_sig"],
                cert_rec["id"],
                mail_crypto.cert_fingerprint_sha256(cert),
                validation_token=validation_token,
                validation_url=validation_url,
                expires_at=expires_at
            )

            for att in payload.get("attachments", []):
                raw = mail_crypto.b64decode_bytes(att["content_b64"])

                att_ok = mail_crypto.verify_bytes(
                    cert_pem,
                    raw,
                    att["sig"]
                )
                if not att_ok:
                    api.abort(400, "Invalid signature for attachment '" + att["filename"] + "'")

                db.add_mail_attachment(
                    msg_id,
                    att["filename"],
                    att["mime"],
                    att["content_b64"],
                    att["sig"],
                    mail_crypto.sha256_bytes(raw)
                )

            return {
                "id": msg_id,
                "validation_token": validation_token,
                "validation_url": validation_url
            }, 201

    from flask_cors import CORS
    CORS(api.app)

    @api.route("/mail/x509")
    class MailX509(Resource):
        def options(self):
            return {}, 200

        def post(self):
            payload = request.get_json(force=True) or {}

            uid = payload.get("uid")
            recipient = payload.get("recipient")
            subject = payload.get("subject")
            body = payload.get("body")
            private_key_pem = payload.get("private_key_pem")
            attachments = payload.get("attachments", [])

            missing = [k for k in ["uid", "recipient", "subject", "body", "private_key_pem"] if not payload.get(k)]
            if missing:
                return {
                    "error": True,
                    "message": f"Faltan campos obligatorios: {', '.join(missing)}"
                }, 400

            usrs = db.list_users(uid=uid)
            if len(usrs) != 1:
                return {"error": True, "message": "Usuario no encontrado de forma única"}, 400

            certs = db.list_certs(uid=uid, valid=True, revoked=False)
            if len(certs) == 0:
                return {"error": True, "message": "El usuario no tiene certificado activo registrado"}, 400

            cert_rec = certs[0]
            cert = cert_rec["cert"]

            canonical_body = mail_crypto.canonicalize_body(subject, recipient, body)

            body_sig = mail_crypto.sign_bytes(
                private_key_pem,
                None,
                canonical_body
            )

            cert_fpr = mail_crypto.cert_fingerprint_sha256(cert)

            recipient_lower = recipient.strip().lower()
            recipient_users = db.list_users(mail=recipient_lower)
            is_external = len(recipient_users) == 0

            if is_external:
                validation_token = secrets.token_hex(16).upper()
                expires_at = (datetime.utcnow() + timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S")
                base_url = os.environ.get("PUBLIC_BASE_URL", "http://localhost:8000/api")
                validation_url = base_url + "/public/verify/" + validation_token
            else:
                validation_token = None
                expires_at = None
                validation_url = None

            msg_id = db.add_mail_message(
                uid,
                recipient,
                subject,
                body,
                body_sig,
                cert_rec["id"],
                cert_fpr,
                validation_token=validation_token,
                validation_url=validation_url,
                expires_at=expires_at
            )

            for att in attachments:
                raw = mail_crypto.b64decode_bytes(att["content_b64"])
                sig = mail_crypto.sign_bytes(private_key_pem, None, raw)

                db.add_mail_attachment(
                    msg_id,
                    att["filename"],
                    att["mime"],
                    att["content_b64"],
                    sig,
                    mail_crypto.sha256_bytes(raw)
                )

            return {
                "error": False,
                "id": msg_id,
                "validation_token": validation_token,
                "validation_url": validation_url,
                "message": "Correo firmado y guardado"
            }, 201

    @api.route("/mail/x509/certs")
    class X509Certs(Resource):
        def options(self):
            return {}, 200

        def post(self):
            payload = api.payload
            uid = payload.get("uid")
            cert_pem = payload.get("cert_pem")

            if not uid or not cert_pem:
                api.abort(400, "uid y cert_pem son obligatorios")

            return {"ok": True, "uid": uid}, 201

    @api.route("/mail/<string:message_id>/verify")
    class MailVerify(Resource):
        @api.marshal_with(verify_reply_model)
        def get(self, message_id):
            msg = db.get_mail_message(message_id)
            if msg is None:
                api.abort(404, "Message not found")

            cert_rec = db.get_cert(msg["cert_id"])
            if cert_rec is None:
                api.abort(400, "Signing certificate not found")

            cert = cert_rec["cert"]
            cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode()

            body_to_verify = msg.get("body_raw", msg["body"])

            canonical_body = mail_crypto.canonicalize_body(
                msg["subject"],
                msg["recipient"],
                body_to_verify
            )

            body_ok = mail_crypto.verify_bytes(
                cert_pem,
                canonical_body,
                msg["body_sig"]
            )

            atts = db.get_mail_attachments(message_id)
            atts_ok = True
            for att in atts:
                raw = mail_crypto.b64decode_bytes(att["content_b64"])
                ok = mail_crypto.verify_bytes(
                    cert_pem,
                    raw,
                    att["sig_b64"]
                )
                if not ok:
                    atts_ok = False
                    break

            cert_ok = (
                not cert_rec["revoked"] and
                cert_rec["not_before"] <= date.today() and
                cert_rec["not_after"] >= date.today()
            )

            return {
                "message_ok": body_ok,
                "attachments_ok": atts_ok,
                "certificate_ok": cert_ok,
                "signer_uid": msg["sender_uid"],
                "fingerprint": msg["signing_cert_fingerprint"],
                "details": "Valid signature" if (body_ok and atts_ok and cert_ok)
                           else "Invalid signature, modified content, or invalid certificate"
            }
        
    @api.route("/public/verify/<string:token>")
    @api.doc(description="Ephemeral one-time verification link for a signed message")
    @api.param("token", "The single-use verification token included in the signed message")
    class PublicVerify(Resource):
        @api.marshal_with(public_verify_model)
        def get(self, token):
            msg = db.get_mail_message_by_token(token)
            if msg is None:
                api.abort(404, "Token invalido o no encontrado")

            if msg.get("token_used", False):
                api.abort(410, "Este enlace ya fue utilizado y no puede reutilizarse")

            expires_at_str = msg.get("expires_at")
            if expires_at_str is not None:
                try:
                    expires_dt = datetime.strptime(expires_at_str[:19], "%Y-%m-%dT%H:%M:%S")
                    if datetime.utcnow() > expires_dt:
                        api.abort(410, "Este enlace ha expirado (valido por 24 horas)")
                except ValueError:
                    api.abort(500, "Error interno al verificar la expiracion del token")

            # Consume el token ANTES de la verificacion criptografica (Zero-Trust: un solo uso)
            db.mark_token_used(token)

            cert_rec = db.get_cert(msg["cert_id"])
            if cert_rec is None:
                api.abort(400, "Certificado firmante no encontrado en la base de datos")

            cert = cert_rec["cert"]
            cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode()

            # Verificar contra body_raw para no incluir el footer de verificacion en la firma
            body_to_verify = msg.get("body_raw", msg["body"])

            canonical_body = mail_crypto.canonicalize_body(
                msg["subject"],
                msg["recipient"],
                body_to_verify
            )

            body_ok = mail_crypto.verify_bytes(
                cert_pem,
                canonical_body,
                msg["body_sig"]
            )

            cert_ok = (
                not cert_rec["revoked"] and
                cert_rec["not_before"] <= date.today() and
                cert_rec["not_after"] >= date.today()
            )

            if body_ok and cert_ok:
                details = "Firma criptografica valida. El contenido no ha sido alterado."
            elif not cert_ok:
                details = "Certificado firmante revocado o fuera de periodo de validez."
            else:
                details = "Firma invalida. El contenido pudo haber sido modificado."

            return {
                "message_ok": body_ok,
                "certificate_ok": cert_ok,
                "signer_uid": msg["sender_uid"],
                "fingerprint": msg["signing_cert_fingerprint"],
                "subject": msg["subject"],
                "recipient": msg["recipient"],
                "created_at": msg["created_at"],
                "details": details
            }

#'''
    register_auth_endpoints(api)

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

# ─── AUTHENTICATION HELPERS (used by other endpoints) ────────────────────────

def _get_current_user_from_token():
    """Decodifica el JWT del header Authorization y devuelve el usuario actual.
    Devuelve None si no hay token, el token es inválido, o el usuario no existe.
    """
    from . import auth

    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None

    token = header[7:].strip()
    payload = auth.decode_jwt(token)
    if payload is None:
        return None

    all_users = db.list_users()
    matches = [u for u in all_users if u["id"] == payload["uid"]]

    if len(matches) != 1:
        return None

    return matches[0]

# ─── AUTHENTICATION ENDPOINTS ─────────────────────────────────────────────────
def register_auth_endpoints(api):
    from . import auth

    login_model = api.model("AuthLogin", {
        "mail": StrField("Email address", required=True),
        "password": StrField("Password", required=True)
    })

    login_reply_model = api.model("AuthLoginReply", {
        "token": StrField("JWT access token", required=True),
        "must_change_password": fields.Boolean(required=True),
        "uid": StrField("User ID", required=True),
        "name": StrField("Full name", required=True),
        "lvl": StrField("Access level", required=True),
        "dept": StrField("Department", required=True)
    })

    me_reply_model = api.model("AuthMeReply", {
        "uid": StrField("User ID", required=True),
        "name": StrField("Full name", required=True),
        "mail": StrField("Email address", required=True),
        "lvl": StrField("Access level", required=True),
        "dept": StrField("Department", required=True),
        "must_change_password": fields.Boolean(required=True)
    })

    change_pwd_model = api.model("AuthChangePassword", {
        "old_password": StrField("Current password", required=True),
        "new_password": StrField("New password", required=True)
    })

    def _get_current_user():
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return None

        token = header[7:].strip()
        payload = auth.decode_jwt(token)
        if payload is None:
            return None

        usrs = db.list_users(uid=payload["uid"])
        if len(usrs) != 1:
            return None

        return usrs[0]

    @api.route("/auth/login")
    class AuthLogin(Resource):
        @api.expect(login_model)
        @api.marshal_with(login_reply_model)
        def post(self):
            mail = api.payload.get("mail", "").strip().lower()
            password = api.payload.get("password", "")

            if not mail or not password:
                api.abort(400, "Email and password are required")

            all_users = db.list_users()
            matches = [u for u in all_users if u["mail"].lower() == mail]

            if len(matches) != 1:
                api.abort(401, "Invalid credentials")

            usr = matches[0]

            auth_rec = db.get_auth(usr["id"])
            if auth_rec is None:
                api.abort(401, "Invalid credentials")

            if not auth.verify_password(password, auth_rec["password_hash"]):
                api.abort(401, "Invalid credentials")

            token = auth.create_jwt(usr["id"], usr["lvl"], usr["dept"])

            return {
                "token": token,
                "must_change_password": auth_rec.get("must_change_password", False),
                "uid": usr["id"],
                "name": usr["name"],
                "lvl": usr["lvl"],
                "dept": usr["dept"]
            }

    @api.route("/auth/me")
    class AuthMe(Resource):
        @api.marshal_with(me_reply_model)
        def get(self):
            usr = _get_current_user()
            if usr is None:
                api.abort(401, "Not authenticated")

            auth_rec = db.get_auth(usr["id"])
            must_change = auth_rec.get("must_change_password", False) if auth_rec else False

            return {
                "uid": usr["id"],
                "name": usr["name"],
                "mail": usr["mail"],
                "lvl": usr["lvl"],
                "dept": usr["dept"],
                "must_change_password": must_change
            }

    @api.route("/auth/change-password")
    class AuthChangePassword(Resource):
        @api.expect(change_pwd_model)
        def post(self):
            usr = _get_current_user()
            if usr is None:
                api.abort(401, "Not authenticated")

            old_password = api.payload.get("old_password", "")
            new_password = api.payload.get("new_password", "")

            if not old_password or not new_password:
                api.abort(400, "Both old_password and new_password are required")

            if len(new_password) < 8:
                api.abort(400, "New password must be at least 8 characters")

            auth_rec = db.get_auth(usr["id"])
            if auth_rec is None:
                api.abort(400, "User has no auth record")

            if not auth.verify_password(old_password, auth_rec["password_hash"]):
                api.abort(401, "Old password is incorrect")

            new_hash = auth.hash_password(new_password)
            db.set_auth(usr["id"], new_hash, must_change=False)

            return {"status": "ok"}, 200

    @api.route("/auth/logout")
    class AuthLogout(Resource):
        def post(self):
            return {"status": "ok"}, 200
        
# ─── BOOTSTRAP ────────────────────────────────────────────────────────────────

def _bootstrap_admin():
    from . import auth

    existing_auth = db.auth_table.all() if db.auth_table is not None else []
    if len(existing_auth) > 0:
        return

    print("=" * 60)
    print("Bootstrapping initial admin user...")

    all_users = db.list_users()
    existing_admin = next(
        (u for u in all_users if u["mail"].lower() == "admin@casamonarca.mx"),
        None
    )

    if existing_admin is not None:
        uid = existing_admin["id"]
        print("  An admin user with this email already exists, reusing it.")
    else:
        uid = db.add_user(
            name="Administrador Casa Monarca",
            dept="TI",
            lvl="admin",
            mail="admin@casamonarca.mx",
            joined=date.today()
        )

    password_hash = auth.hash_password("admin123")
    db.set_auth(uid, password_hash, must_change=True)

    print(f"  Email:    admin@casamonarca.mx")
    print(f"  Password: admin123 (must change on first login)")
    print(f"  UID:      {uid}")
    print("=" * 60)