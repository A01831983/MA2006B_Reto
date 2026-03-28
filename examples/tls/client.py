#! /usr/bin/env python

"""
Client exemplifying certificate verification of the server.
"""

__author__ = "Henning Arvid Ladewig"

import os
import ssl
import socket
import datetime

HOST = "localhost"
PORT = 55555

# Create TLS context
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ctx.minimum_version = ssl.TLSVersion.TLSv1_3    # Minimum version
ctx.verify_mode = ssl.CERT_REQUIRED             # Require server to present certificate
ctx.load_verify_locations(cafile=os.path.join(os.path.dirname(__file__), "certificate.pem"))

# Connect to server
with socket.socket() as sock:
    with ctx.wrap_socket(sock, server_hostname=HOST) as ssock:
        ssock.connect((HOST, PORT))

        ssock.sendall(b"Hello, Server!")
        
        data = ssock.recv(1024)
        print("[*] Received:", data.decode())
        ssock.close()
