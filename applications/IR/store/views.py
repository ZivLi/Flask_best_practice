# coding: utf-8
"""
业务门店模块调用 api 接口
"""
from flask_restful import Resource
from applications.IR.store.service import StoreService
from applications.IR.store.models import StoreSchema


class StoreViewAPI(Resource):
    """
    资源 store 操作列表
    """

    def __init__(self):
        self.service = StoreService
        self.schema = StoreSchema(many=True)

        super(StoreViewAPI, self).__init__()

    def get(self):
        stores = self.service._model.model_query()
        return self.schema.dump(stores)
