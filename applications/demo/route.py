# coding: utf-8
from flask import Blueprint
from flask_restful import Api

from applications.demo.views import DemoViewAPI

demo_bp = Blueprint("demo", __name__)
demo_api = Api(demo_bp)


demo_api.add_resource(DemoViewAPI, "", endpoint="")
