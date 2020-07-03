# coding: utf-8
import pandas as pd
from json import dumps

from flask import Blueprint, Response, current_app, make_response
from flask_restful.utils import PY3

from applications.user import user_datastore, user_bp, user_api
from applications.demo import demo_api, demo_bp
from applications.IR import (
    IR_apis,
    IR_bps,
)
from config import RESPONSE_SUCCESS_CODE, RESPONSE_SUCCESS_MSG, app_config


exception_bp = Blueprint("exception", __name__)
"""
系统接口统一处理 exception，通过各个子模块定义的 Exceptions，在这里进行分解 status code & message，更友好返回给前端，
并进行提示报错原因信息展示。
"""


@exception_bp.app_errorhandler(Exception)
def error_500(error):
    """
    如果含有 status code 属性，则是系统封装的 exception，可以直接返回，前端可能会根据对应 message 做提示，
    否则直接返回运行 exception.
    """
    if hasattr(error, "status_code"):
        res = {"code": error.status_code, "message": error.message}
    # 开发环境 抛出异常
    elif app_config.DEBUG:
        raise error
    else:
        res = {"message": str(error)}
    return Response(dumps(res), mimetype="application/json")


blueprints = [
    (user_bp, "/"),
    (exception_bp, "/error"),
    *IR_bps,
]


def configure_blueprints(app):
    # 注册 blueprint
    app.register_blueprint(demo_bp, url_prefix="/demo")
    for bp, url_prefix in blueprints:
        app.register_blueprint(bp, url_prefix=url_prefix)


apis = [user_api, *IR_apis]


@demo_api.representation("application/json")
def output_json(
    data, code=RESPONSE_SUCCESS_CODE, message=RESPONSE_SUCCESS_MSG, headers=None
):
    """Makes a Flask response with a JSON encoded body"""

    # 此处为自定义添加***************
    # if 'message' not in data:
    data = {
        "code": code,
        "message": message,
        # 如果 service 接口返回 dataframe，这里统一做 record 转换
        "data": data.to_dict("record")
        if isinstance(data, pd.DataFrame)
        else data,
    }
    # **************************

    settings = current_app.config.get("RESTFUL_JSON", {})

    # If we're in debug mode, and the indent is not set, we set it to a
    # reasonable value here.  Note that this won't override any existing value
    # that was set.  We also set the "sort_keys" value.
    if current_app.debug:
        settings.setdefault("indent", 4)
        settings.setdefault("sort_keys", not PY3)

    # always end the json dumps with a new line
    # see https://github.com/mitsuhiko/flask/pull/1262
    dumped = dumps(data, **settings) + "\n"

    resp = make_response(dumped, RESPONSE_SUCCESS_CODE)
    resp.headers.extend(headers or {})
    return resp


# 通过赋值的方式给 output_json 函数加装饰器
for api in apis:
    output_json = api.representation("application/json")(output_json)
