#! /usr/bin/env python

"""
Starts a sample server, that is to be authenticated.
Needs the password for the private key file as argument.
"""

__author__ = "Henning Arvid Ladewig"

import os
import sys
import ssl
import socket

from cryptography.hazmat.primitives.serialization import load_pem_private_key

HOST = "localhost"
PORT = 55555

# Check command-line arguments
if len(sys.argv) != 2:
    print("Usagae: server.py <password>")
    exit()

# User-supplied password for private key file
pwd = sys.argv[1].encode()

# Create TLS context
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ctx.minimum_version = ssl.TLSVersion.TLSv1_3

in_script_dir = lambda name: os.path.join(os.path.dirname(__file__), name)
ctx.load_cert_chain(certfile=in_script_dir("certificate.pem"),   # Certificate file
                    keyfile=in_script_dir("private_key.pem"),    # Private key
                    password=pwd)

with socket.socket() as sock:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allow immediate reuse of port
    sock.bind((HOST, PORT))
    sock.listen()

    # Listen for clients
    with ctx.wrap_socket(sock, server_side=True) as ssock:
        conn, addr = ssock.accept()

        with conn:
            data = conn.recv(1024)

            print("[*] Received:", data.decode())

            conn.send(b"Hello, Client!")

            conn.close()
