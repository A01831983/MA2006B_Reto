#! /usr/bin/env python

"""
Runs the API backend.
"""

__author__ = "Henning Arvid Ladewig"

from flask import Flask
from flask_restx import Api, Resource, fields
from flask_swagger_ui import get_swaggerui_blueprint

import api_intf as ai
import ccore


ccore.init("examples/dummy_server_key.pem")

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
