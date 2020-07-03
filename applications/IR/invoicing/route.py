# coding: utf-8
from flask import Blueprint
from flask_restful import Api

from applications.IR.invoicing.views import StoreInventoryViewAPI


inventory_bp = Blueprint("inventory", __name__)
inventory_api = Api(inventory_bp)

inventory_api.add_resource(
    StoreInventoryViewAPI, "/store/<int:store_id>", endpoint="inventory/store"
)
