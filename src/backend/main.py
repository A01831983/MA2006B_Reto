#! /usr/bin/env python

"""
Runs the API backend.
"""

__author__ = "Henning Arvid Ladewig"

from flask import Flask
from flask_restx import Api, Resource, fields
from flask_swagger_ui import get_swaggerui_blueprint

import api_intf as ai

app = Flask(__name__)
api = Api(app, version="1.0", title="Gestor-API", doc=False,
    description="Gestor API",
)
swaggerui_bp = get_swaggerui_blueprint(
    "/docs", "/swagger.json"
)
app.register_blueprint(swaggerui_bp)

api = ai.register(api, "examples/dummy.json")

if __name__ == '__main__':
    app.run(debug=True, port=8000)

# Users (identities)
# list_users = a.get("/users", response_model=ai.UserList)(ai.list_users)
# create_user = a.post("/users", response_model=ai.UserCreationReply)(ai.create_user)
# get_own_user = a.get("/users/me", response_model=ai.User)(ai.get_own_user)

# Certificates
# list_certs = a.get("/certs", response_model=ai.CertificateInfoList)(ai.list_certs)
# create_cert = a.post("/certs", response_model=ai.CertificateCreationReply)(ai.create_cert)
# get_own_certs = a.get("/certs/me", response_model=ai.CertificateInfoList)(ai.get_own_certs)

# Certificate Signing Requests
# list_csrs = a.get("/csrs", response_model=ai.CSRStatusList)(ai.list_csrs)
# approve_csr = a.post("/csrs/approve", response_model=ai.CSRApprovalReply)(ai.approve_csr)
