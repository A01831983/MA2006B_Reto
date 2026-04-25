#! /usr/bin/env python

"""
Generates a dummy backend database.
"""

__author__ = "Henning Arvid Ladewig"


import os
import sys
from datetime import date

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                             "../src/backend")))

import db
import ccore


# Helper function
indir = lambda filename: os.path.join(os.path.dirname(__file__), filename)

if not db.init(indir("dummy.json")):
    raise ValueError("Database file invalid format")

ccore.init(indir("dummy_server_key.pem"))

if len(db.list_users()) != 0: exit()

# Write dummy data to examples/dummy.json
adm = {"name": "Max Mustermann", "dept": "TI", "lvl": "admin",
       "mail": "admin@casamonarca.mx", "joined": date(2026, 3, 10)}
dummy_users = [
    adm,
    {"name": "María López", "dept": "Legal", "lvl": "coordinador",
     "mail": "m.lopez@casamonarca.mx", "joined": date(2024, 1, 1)},
    {"name": "José Ramírez", "dept": "Humanitaria", "lvl": "operativo",
     "mail": "j.ramirez@casamonarca.mx", "joined": date(2024, 8, 15)},
    {"name": "Ana González", "dept": "PsicoSocial", "lvl": "operativo",
     "mail": "a.gonzalez@casamonarca.mx", "joined": date(2024, 10, 13)},
    {"name": "Carlos Vega", "dept": "Legal", "lvl": "operativo",
     "mail": "c.vega@casamonarca.mx", "joined": date(2020, 6, 1)},
    {"name": "Lucía Morales", "dept": "Almacén", "lvl": "coordinador",
     "mail": "l.morales@casamonarca.mx", "joined": date(2019, 12, 1)},
    {"name": "Roberto Salas", "dept": "Comunicación", "lvl": "operativo",
     "mail": "r.salas@casamonarca.mx", "joined": date(2025, 12, 24)},
    {"name": "Diana Fuentes", "dept": "PsicoSocial", "lvl": "operativo",
     "mail": "d.fuentes@casamonarca.mx", "joined": date(2026, 1, 1)}
]

list(map(lambda u: db.add_user(**u), dummy_users))

if len(db.list_certs()) != 0: exit()

get_uid = lambda name: db.list_users(name=name)[0]["id"]
max_uid = get_uid("Max")

max_without_joined = adm.copy()
del max_without_joined["joined"]

db.add_cert(max_uid, ccore.create_cert(
    max_uid, **max_without_joined,
    not_before=date(2027, 1, 1), not_after=date(2028, 1, 1),
    pwd="123Hallo")[0])
