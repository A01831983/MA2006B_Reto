#! /usr/bin/env python

"""
Runs the API backend.
"""

__author__ = "Henning Arvid Ladewig"

import os
import sys
import argparse

from flask import Flask, render_template
from flask_restx import Api, Resource, fields
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS

import src.api_intf as ai

def parse_args():
    parser = argparse.ArgumentParser(
        description="Start the backend."
    )

    parser.add_argument(
        "--db",
        required=True,
        help="Database file (.json)"
    )
    parser.add_argument(
        "--cert",
        required=True,
        help="Server certificate file (.pem)"
    )
    parser.add_argument(
        "--key",
        required=True,
        help="Server private key file (.pem)"
    )

    args = parser.parse_args()

    # Prüfen, ob die angegebenen Dateien existieren
    for file_arg in [("Database", args.db), ("Certificate", args.cert), ("Private key", args.key)]:
        name, path = file_arg
        if not os.path.isfile(path):
            print(f"Error: {name} file does not exist: {path}", file=sys.stderr)
            exit(1)

    return args


app = Flask(__name__)

args = parse_args()

CORS(app)

api = Api(app, version="1.0", title="Gestor", doc=False,
    description="Gestor de identidades", validate=True, prefix="/api"
)
swaggerui_bp = get_swaggerui_blueprint(
    "/api/docs", "/api/swagger.json"
)
app.register_blueprint(swaggerui_bp)

api = ai.register(api, args.db)

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, port=8000)
