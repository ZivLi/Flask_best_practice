# coding: utf-8
"""
预测相关 api 接口
"""
from flask_restful import Resource
from flask_restful import reqparse
from applications.IR.forecast.service import (
    ForecastService,
    ForecastFileTimeService,
)
from config import RESPONSE_CREATED_SUCCESS_CODE


class ForecasetCallbackViewAPI(Resource):
    """
    预测结果回调接口
    """

    def __init__(self):
        self.service = ForecastService
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "status", type=int, location="json", required=True
        )
        self.reqparse.add_argument(
            "version", type=str, location="json", required=True
        )
        super(ForecasetCallbackViewAPI, self).__init__()

    def post(self):
        args = self.reqparse.parse_args()
        self.service.update_forecast_status(
            args.get("version"), args.get("status")
        )
        return {}, RESPONSE_CREATED_SUCCESS_CODE


class ForecastCancelViewAPI(Resource):
    """
    取消预测模型运行接口
    """

    def __init__(self):
        self.service = ForecastService
        super(ForecastCancelViewAPI, self).__init__()

    def get(self):
        self.service.cancel_forecast()


class ForecastFileTimeViewAPI(Resource):
    """
    当前预测版本所使用的配置文件时间
    """

    def __init__(self):
        self.service = ForecastFileTimeService
        super(ForecastFileTimeViewAPI, self).__init__()

    def get(self):
        return self.service.get()
