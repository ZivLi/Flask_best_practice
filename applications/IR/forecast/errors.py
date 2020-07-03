# coding: utf-8


class ForecastVersionDoesNotExistError(Exception):
    status_code = 404
    message = "暂无配置信息，请先去业务配置页面保存配置信息。"
