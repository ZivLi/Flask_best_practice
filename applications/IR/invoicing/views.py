# coding: utf-8
"""
经销存相关 api 接口
"""
from flask_restful import Resource

from applications.IR.invoicing.service import StoreInventoryService


class StoreInventoryViewAPI(Resource):
    """
    门店库存信息
    """

    def __init__(self):
        self.service = StoreInventoryService

        super(StoreInventoryViewAPI, self).__init__()

    def get(self, store_id):
        # 获取某个门店下的库存结果
        store_inventory_service = self.service(store_id=store_id)
        return store_inventory_service.get_last_store_inventory(
            with_sku_info=True
        )
