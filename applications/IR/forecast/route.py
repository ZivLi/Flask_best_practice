# coding: utf-8
from flask import Blueprint
from flask_restful import Api

from applications.IR.forecast.views import (
    ForecasetCallbackViewAPI,
    ForecastCancelViewAPI,
    ForecastFileTimeViewAPI,
)


forecast_bp = Blueprint("forecast", __name__)
forecast_api = Api(forecast_bp)


forecast_api.add_resource(
    ForecasetCallbackViewAPI, "/callback", endpoint="forecast/callback"
)
forecast_api.add_resource(
    ForecastCancelViewAPI, "/cancel", endpoint="forecast/cancel"
)
forecast_api.add_resource(
    ForecastFileTimeViewAPI, "/filetime", endpoint="forecast/filetime"
)
