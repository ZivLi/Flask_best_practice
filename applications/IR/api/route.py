# coding: utf-8
from flask import Blueprint
from flask_restful import Api

from applications.IR.api.views import TempFileLoadViewAPI

api_bp = Blueprint("api", __name__)
api_api = Api(api_bp)


api_api.add_resource(
    TempFileLoadViewAPI, "/tempfile/<file_name>", endpoint="api/tempfile"
)
