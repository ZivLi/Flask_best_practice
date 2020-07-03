# coding: utf-8
"""
项目业务配置模块调用 api 接口
"""
from flask_restful import Resource
from flask_restful import reqparse
from flask_security.core import current_user

from applications.IR.api import config as api_config
from applications.IR.api.service import FileLoadService
from applications.IR.configuration.service import ConfigurationService
from celery_tasks.configuration_tasks import configuration_save
from config import RESPONSE_CREATED_SUCCESS_CODE


class ConfigurationResetViewAPI(Resource):
    """
    模板配置重置时，提供调用接口，仅支持 get方法请求，
    删除临时缓存文件，并未写入数据库内容.
    """

    def __init__(self):
        self.service = FileLoadService
        super(ConfigurationResetViewAPI, self).__init__()

    def get(self):
        self.service.remove_files(directory_path=api_config.TMP_SAVE_PATH)


class ConfigurationViewAPI(Resource):
    """
    配置模板操作 apis.
    """

    def __init__(self):
        self.service = ConfigurationService
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "predict_cycle", type=list, location="json", required=False
        )
        self.reqparse.add_argument(
            "target", type=list, location="json", required=False
        )
        self.reqparse.add_argument(
            "min_order_amount", type=float, location="json", required=False
        )
        super(ConfigurationViewAPI, self).__init__()

    def get(self):
        """
        获取配置 api 接口.
        第一次访问，无配置返回默认表名；
        如果有保存成功过，则返回保存配置内容，及状态.
        """
        return self.service.get_configuration()

    def post(self):
        """
        保存配置 api 接口.
        """
        args = self.reqparse.parse_args()
        # celery 异步任务执行配置保存操作。
        # 因无法在 celery app 中获取到 current user，所以这里把执行人 name 当做参数传递到任务端
        configuration_save.delay(args, current_user.name)
        return {}, RESPONSE_CREATED_SUCCESS_CODE


class ConfigurationStatusViewAPI(Resource):
    """
    前端轮询获取配置状态接口
    """

    def __init__(self):
        self.service = ConfigurationService

    def get(self):
        configuration_status = {"status": self.service.get_status()}
        return configuration_status
