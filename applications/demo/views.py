# coding: utf-8
"""
Views for current app system.
"""
from flask_restful import Resource, reqparse

from applications.demo.service import DemoService


class DemoViewAPI(Resource):
    """
    某个application 下的某个url对应的视图功能
    """

    def __init__(self):
        self.service = DemoService
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "test", type=int, location="args", required=True
        )

        super(DemoViewAPI, self).__init__()

    def get(self):
        args = self.reqparse.parse_args()
        test_value = args.get("test")
        if self.service.is_demo_true(test_value):
            return "ok"
            # return ResponseService("ok").response()
        else:
            return "no"
