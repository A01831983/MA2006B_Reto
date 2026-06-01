#! /usr/bin/env python

"""
Provides access to the database.
"""

__author__ = "Henning Arvid Ladewig"


import random
from datetime import datetime, date

import tinydb
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import serialization


db = None
users = None
certs = None
auth_table = None

def init(filename):
    global db, users, certs, cert_data

    ldb = tinydb.TinyDB(filename)
    if not _validate_db(ldb):
        return False

    db = ldb

    users = db.table("users")
    certs = db.table("certs")

    return True

def _validate_db(db):
    users = db.table("users")
    certs = db.table("certs")

    # TODO: Validate database contents

    return True

def _ser_date(d: date):
    if not isinstance(d, date):
        raise ValueError(f"d ({d}) should be datetime.date")
    return (d.year, d.month, d.day)

def _des_date(t):
    return date(*t)

def _chk_usr(u: dict):
    keys = u.keys()
    if not ("id" in keys and "name" in keys and "dept" in keys and "lvl" and
            "mail" in keys and "joined" in keys):
        raise ValueError("Not a user dict")

def _ser_usr(u: dict, check=True):
    if check: _chk_usr(u)

    ret = u.copy()

    if check or (not check and "joined" in u.keys()):
        ret["joined"] = _ser_date(u["joined"])

    return ret

def _des_usr(u: dict):
    _chk_usr(u)

    ret = u.copy()
    ret["joined"] = _des_date(u["joined"])

    return ret

def list_users(uid: str = "", name: str = "", dept: str = "", lvl: str = "",
               mail: str = "", joined_before: date = None,
               joined_after: date = None):
    Usr = tinydb.Query()

    # Filter by uid, name, dept, lvl and mail
    ret = map(_des_usr, users.search(
        Usr.id.search(uid) & Usr.name.search(name) & Usr.dept.search(dept) &
        Usr.lvl.search(lvl) & Usr.mail.search(mail)
    ))

    # Filter by join date
    join_filter = lambda u: \
            (u["joined"] <= joined_before if joined_before is not None
             else True) and \
            (u["joined"] >= joined_after if joined_after is not None
             else True)

    # Filter by join date
    return list(filter(join_filter, ret))

def add_user(name: str, dept: str, lvl: str, mail: str, joined: date):
    # Enforce email address uniqueness
    if len(list_users(mail=mail)) != 0:
        raise ValueError("email address must be unique")

    uid = random.randint(0, 2**31-1)
    while len(list_users(uid=str(uid))) != 0:
        uid = random.randint(0, 2**31-1)
    uid = str(uid)

    u = {"id": uid, "name": name, "dept": dept, "lvl": lvl, "mail": mail,
         "joined": joined}

    users.insert(_ser_usr(u))

    return uid

def change_users(uid: str, new: dict):
    if not set(new.keys()).issubset({"name", "dept", "lvl", "mail", "joined"}):
        return "can only update the fields 'name', 'dept', 'lvl', 'mail', and"\
                + " 'joined'"

    if "mail" in new.keys():
        usrs = list_users(mail=new["mail"])

        if len(usrs) > 1:
            raise ValueError("email address must be unique")
        
        if len(usrs) == 1:
            usr = usrs[0]

            if usr["uid"] != uid:
                raise ValueError("email address must be unique")

    update = _ser_usr(new, check=False)

    users.update(update, tinydb.Query().id.search(uid))

def delete_users(uid: str):
    users.remove(tinydb.Query().id.search(uid))

def _chk_crt(c: dict):
    keys = c.keys()
    if not ("id" in keys and "uid" in keys and "not_before" in keys and
            "not_after" in keys and "not_before" in keys and "revoked" in keys):
        raise ValueError("Not a certificate dict")

def _ser_crt(c: dict):
    _chk_crt(c)
    if not "cert" in c.keys():
        raise ValueError("Not a certificate dict (missing 'cert' entry)")

    ret = c.copy()
    ret["raw"] = c["cert"].public_bytes(serialization.Encoding.PEM).decode()
    ret["not_before"] = _ser_date(ret["not_before"])
    ret["not_after"] = _ser_date(ret["not_after"])
    del ret["cert"]

    return ret

def _des_crt(c: dict):
    _chk_crt(c)
    if not "raw" in c.keys():
        raise ValueError("Not a certificate dict (missing 'raw') entry")

    ret = c.copy()
    ret["not_before"] = _des_date(c["not_before"])
    ret["not_after"] = _des_date(c["not_after"])
    ret["cert"] = x509.load_pem_x509_certificate(c["raw"].encode())
    del ret["raw"]

    return ret

def list_certs(cid: str = "", uid: str = "", valid: bool = None,
               not_before: date = None, not_after: date = None,
               revoked: bool = None, pb: bytes = b""):
    Crt = tinydb.Query()

    # Filter by cid, uid, revoked
    ret = map(_des_crt, certs.search(
        Crt.id.search(cid) & Crt.uid.search(uid) if revoked is None else \
        Crt.id.search(cid) & Crt.uid.search(uid) & (Crt.revoked == revoked)
    ))

    # Filter by valid
    if valid is not None:
        today = date.today()
        validity_filter = lambda c: \
            c["not_before"] <= today and c["not_after"] >= today

        if not valid:
            f = lambda c: not validity_filter(c)
        else:
            f = validity_filter

        ret = filter(f, ret)

    # Filter by not_before, not_after
    date_filter = lambda c: \
        (not_before is None or c["not_before"] >= not_before) and \
        (not_after is None or c["not_after"] <= not_after)

    # Filter by public bytes
    pb_filter = lambda c: pb in c["cert"].public_bytes(serialization.Encoding.PEM)

    return list(filter(pb_filter, filter(date_filter, ret)))

def add_cert(uid: str, cert: x509.Certificate):
    cid = random.randint(0, 2**31-1)
    while len(list_certs(cid=str(cid))) != 0:
        cid = random.randint(0, 2**31-1)
    cid = str(cid)

    certinfo = {
        "id": cid, "uid": uid, "not_after": cert.not_valid_after.date(),
        "not_before": cert.not_valid_before.date(), "cert": cert, "revoked": False
    }
    certs.insert(_ser_crt(certinfo))

    return cid


#'''

# mail_db
pgp_keys = None
mail_messages = None
mail_attachments = None

def init(filename):
    global db, users, certs, mail_messages, mail_attachments, auth_table

    ldb = tinydb.TinyDB(filename)
    if not _validate_db(ldb):
        return False

    db = ldb
    users = db.table("users")
    certs = db.table("certs")
    mail_messages = db.table("mail_messages")
    mail_attachments = db.table("mail_attachments")
    auth_table = db.table("auth")
    return True

def add_mail_message(sender_uid: str, recipient: str, subject: str, body: str, body_sig: str, cert_id: str, cert_fpr: str):
    mid = str(len(mail_messages) + 1)
    rec = {
        "id": mid,
        "sender_uid": sender_uid,
        "recipient": recipient,
        "subject": subject,
        "body": body,
        "body_sig": body_sig,
        "cert_id": cert_id,
        "signing_cert_fingerprint": cert_fpr,
        "created_at": datetime.utcnow().isoformat()
    }
    mail_messages.insert(rec)
    return mid

def add_mail_attachment(message_id: str, filename: str, mime: str, content_b64: str, sig_b64: str, sha256: str):
    aid = str(len(mail_attachments) + 1)
    rec = {
        "id": aid,
        "message_id": message_id,
        "filename": filename,
        "mime": mime,
        "content_b64": content_b64,
        "sig_b64": sig_b64,
        "sha256": sha256
    }
    mail_attachments.insert(rec)
    return aid

def list_mail_messages(sender_uid: str = ""):
    Q = tinydb.Query()
    if sender_uid:
        return mail_messages.search(Q.sender_uid == sender_uid)
    return mail_messages.all()

def get_mail_message(message_id: str):
    Q = tinydb.Query()
    ret = mail_messages.search(Q.id == message_id)
    return ret[0] if len(ret) == 1 else None

def get_mail_attachments(message_id: str):
    Q = tinydb.Query()
    return mail_attachments.search(Q.message_id == message_id)

def get_cert(cid: str):
    ret = list_certs(cid=cid)
    return ret[0] if len(ret) == 1 else None

# auth_db
def get_auth(uid: str):
    Q = tinydb.Query()
    ret = auth_table.search(Q.uid == uid)
    return ret[0] if len(ret) == 1 else None

def set_auth(uid: str, password_hash: str, must_change: bool = True):
    Q = tinydb.Query()
    existing = auth_table.search(Q.uid == uid)

    rec = {
        "uid": uid,
        "password_hash": password_hash,
        "must_change_password": must_change,
        "updated_at": datetime.utcnow().isoformat()
    }

    if len(existing) == 0:
        rec["created_at"] = rec["updated_at"]
        auth_table.insert(rec)
    else:
        auth_table.update(rec, Q.uid == uid)

def delete_auth(uid: str):
    Q = tinydb.Query()
    auth_table.remove(Q.uid == uid)

def clear_must_change(uid: str):
    Q = tinydb.Query()
    auth_table.update({"must_change_password": False}, Q.uid == uid)