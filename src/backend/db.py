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

    update = _ser_usr(new, check=False)

    users.update(update, tinydb.Query().id.search(uid))

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
               revoked: bool = None):
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

    return list(filter(date_filter, ret))

def add_cert(uid: str, cert: x509.Certificate):
    cid = random.randint(0, 2**31-1)
    while len(list_certs(cid=str(cid))) != 0:
        cid = random.randint(0, 2**31-1)
    cid = str(cid)

    certinfo = {
        "id": cid, "uid": uid, "not_after": cert.not_valid_after,
        "not_before": cert.not_valid_before, "cert": cert, "revoked": False
    }
    certs.insert(_ser_crt(certinfo))

    return cid
