# coding: utf-8
from flask import Blueprint
from flask_restful import Api

from applications.IR.configuration.views import (
    ConfigurationResetViewAPI,
    ConfigurationStatusViewAPI,
    ConfigurationViewAPI,
)

configuration_bp = Blueprint("configuration", __name__)
configuration_api = Api(configuration_bp)


configuration_api.add_resource(
    ConfigurationViewAPI, "", endpoint="configuration"
)
configuration_api.add_resource(
    ConfigurationStatusViewAPI, "/status", endpoint="configuration/status"
)
configuration_api.add_resource(
    ConfigurationResetViewAPI, "/reset", endpoint="configuration/reset"
)
