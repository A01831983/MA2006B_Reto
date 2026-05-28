#! /usr/bin/env python

desc = \
"""
Generates a new certificate for a user already registered in a database.
"""

__author__ = "Henning Arvid Ladewig"

import os
import sys
import argparse

from certutil import load_cert_file, load_key_file, create_ck, create_usr_x509

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                             "..")))

from src import db


indir = lambda filename: os.path.join(os.path.dirname(__file__), filename)

def parse_args():
    parser = argparse.ArgumentParser(description=desc)

    cf = indir("cert.pem")
    kf = indir("key.pem")
    acf = indir("admin_cert.pem")
    akf = indir("admin_key.pem")

    parser.add_argument(
        "database", help="Database file (.json)"
    )
    parser.add_argument(
        "email", help="Email of the user to create a certificate for"
    )
    parser.add_argument(
        "-c", "--cert", default=cf,
        help=f"Output certificate file (default={cf})"
    )
    parser.add_argument(
        "-k", "--key", default=kf, help=f"Output key file (default={kf})"
    )
    parser.add_argument(
        "-p", "--password", default=None,
        help="Password with which to encrypt the private key file"
    )
    parser.add_argument(
        "-s", "--size", default=2048, help="Key size (default=minimum=2048)"
    )
    parser.add_argument(
        "-a", "--admin-cert", default=acf,
        help=f"Admin certificate to use as issuer (default={acf})"
    )
    parser.add_argument(
        "-l", "--admin-key", default=akf,
        help=f"Admin key file to use for signing (default={akf})"
    )
    parser.add_argument(
        "-o", "--admin-pwd", default=None, help="Password of the admin key"
    )

    args = parser.parse_args()

    for name, path in (("Database", args.database),
                       ("Admin certificate", args.admin_cert),
                       ("Admin key", args.admin_key)):
        if path is None: continue
        if not os.path.isfile(name): continue

        print(f"Error: {name} file does not exist: {path}", file=sys.stderr)
        exit(1)

    if args.size < 2048:
        print(f"Error: Key size must be at least 2048 (have {args.size})",
              file=sys.stderr)
        exit(2)

    return args

def main():
    args = parse_args()

    db.init(args.database)

    usrs = list(filter(lambda u: u["mail"] == args.email,
                db.list_users(mail=args.email)))
    if len(usrs) == 0:
        print(f"Error: No user with email {args.email} found", file=sys.stderr)
        exit(3)

    usr = usrs[0]

    admin_cert = load_cert_file(args.admin_cert)
    admin_key = load_key_file(args.admin_key, args.admin_pwd)

    subject = create_usr_x509(usr, usr["id"])

    cert, key = create_ck(args.size, args.key, args.cert, admin_cert.subject,
                          subject, admin_key)

if __name__ == "__main__":
    main()
