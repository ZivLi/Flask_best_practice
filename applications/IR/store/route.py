# coding: utf-8
from flask import Blueprint
from flask_restful import Api

from applications.IR.store.views import StoreViewAPI

store_bp = Blueprint("store", __name__)
store_api = Api(store_bp)


store_api.add_resource(StoreViewAPI, "", endpoint="stores")
