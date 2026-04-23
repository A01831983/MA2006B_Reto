#! /usr/bin/env python

"""
Provides access to the database.
"""

__author__ = "Henning Arvid Ladewig"


import random
from datetime import datetime, date

import tinydb


db = None
users = None
certs = None

def init(filename):
    global db, users, certs

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

def _ser_usr(u: dict):
    _chk_usr(u)

    ret = u.copy()
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

def _chk_crt(c: dict):
    keys = c.keys()
    if not ("id" in keys and "uid" in keys and "not_before" in keys and
            "not_after" in keys and "not_before" in keys and "revoked" in keys):
        raise ValueError("Not a certificate dict")

def _ser_crt(c: dict):
    _chk_crt(c)

    ret = c.copy()
    ret["not_before"] = _ser_date(ret["not_before"])
    ret["not_after"] = _ser_date(ret["not_after"])

    return ret

def _des_crt(c: dict):
    _chk_crt(c)

    ret = c.copy()
    ret["not_before"] = _des_date(c["not_before"])
    ret["not_after"] = _des_date(c["not_after"])

    return ret

def list_certs(cid: str = "", uid: str = "", valid: bool = None,
               not_before: date = None, not_after: date = None,
               revoked: bool = None):
    Crt = tinydb.Query()

    # Filter by cid, uid, revoked
    ret = map(_des_crt, certs.search(
        Crt.id.search(cid) & Crt.uid.search(uid) if revoked is None else \
        Crt.id.search(cid) & Crt.uid.search(uid) & Crt.revoked == revoked
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

def add_cert(uid: str, not_before: date, not_after: date):
    cid = random.randint(0, 2**31-1)
    while len(list_certs(cid=str(cid))) != 0:
        cid = random.randint(0, 2**31-1)

    c = {"id": cid, "uid": str(uid), "not_before": not_before,
         "not_after": not_after, "revoked": False}

    certs.insert(_ser_crt(c))

    return str(cid)

if __name__ == "__main__":
    if not init("examples/dummy.json"):
        raise ValueError("Database file invalid format")

    if len(list_users()) == 0:
        dummy_users = [
            {"name": "Max Mustermann", "dept": "TI", "lvl": "admin",
             "mail": "admin@casamonarca.mx", "joined": date(2026, 3, 10)},
            {"name": "María López", "dept": "Legal", "lvl": "coordinador",
             "mail": "m.lopez@casamonarca.mx", "joined": date(2024, 1, 1)},
            {"name": "José Ramírez", "dept": "Humanitaria", "lvl": "operativo",
             "mail": "j.ramirez@casamonarca.mx", "joined": date(2024, 8, 15)},
            {"name": "Ana González", "dept": "Salud", "lvl": "captura",
             "mail": "a.gonzalez@casamonarca.mx", "joined": date(2024, 10, 13)},
            {"name": "Carlos Vega", "dept": "Legal", "lvl": "operativo",
             "mail": "c.vega@casamonarca.mx", "joined": date(2020, 6, 1)},
            {"name": "Lucía Morales", "dept": "Educativa", "lvl": "coordinador",
             "mail": "l.morales@casamonarca.mx", "joined": date(2019, 12, 1)},
            {"name": "Roberto Salas", "dept": "Humanitaria", "lvl": "captura",
             "mail": "r.salas@casamonarca.mx", "joined": date(2025, 12, 24)},
            {"name": "Diana Fuentes", "dept": "Salud", "lvl": "operativo",
             "mail": "d.fuentes@casamonarca.mx", "joined": date(2026, 1, 1)}
        ]

        list(map(lambda u: add_user(**u), dummy_users))

        if len(list_certs()) != 0: exit()

        get_uid = lambda name: list_users(name=name)[0]["id"]
        
        today = date.today()
        begin = date(2024, 1, 1)
        end = date(2025, 6, 15)
        dummy_certs = [
            {"uid": get_uid("Max"), "not_before": begin, "not_after": end},
            {"uid": get_uid("Max"), "not_before": end, "not_after": today},
            {"uid": get_uid("María"), "not_before": begin, "not_after": end},
            {"uid": get_uid("Ramírez"), "not_before": begin, "not_after": end}
        ]

        list(map(lambda c: add_cert(**c), dummy_certs))
