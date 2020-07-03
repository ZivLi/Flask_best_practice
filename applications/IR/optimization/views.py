# coding: utf-8
"""
优化模块调用 api 接口
"""
from flask_restful import Resource, reqparse
from applications.IR.optimization.service import OptimizationService
from config import RESPONSE_CREATED_SUCCESS_CODE
from replenish.utils import parse_expired_info


class OptimizationViewAPI(Resource):
    def __init__(self):
        self.service = OptimizationService
        super(OptimizationViewAPI, self).__init__()

    def get(self, order_id):
        optimization_service = self.service(order_id=order_id)
        return optimization_service.get_optimization_results()


class OptimizationListViewAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("page", type=int, required=False, default=1)
        self.reqparse.add_argument(
            "per_page", type=int, required=False, default=30
        )
        super(OptimizationListViewAPI, self).__init__()

    def get(self):
        args = self.reqparse.parse_args()
        optimizations = OptimizationService.list(**args)
        return optimizations


class StoreOptimizationViewAPI(Resource):
    def __init__(self):
        self.service = OptimizationService
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "safety_days", type=int, location="json", required=False
        )

        super(StoreOptimizationViewAPI, self).__init__()

    def get(self, store_id):
        """
        获取优化结果
        """
        optimization_service = self.service(store_id=store_id)
        return optimization_service.get_optimization_results()

    def post(self, store_id):
        """
        第一次生成优化结果
        """
        args = self.reqparse.parse_args()
        safety_days = args.get("safety_days")
        optimization_service = self.service(
            store_id=store_id, safety_days=safety_days
        )
        optimization_service.gen_init_optimization()
        return (
            optimization_service.get_optimization_results(),
            RESPONSE_CREATED_SUCCESS_CODE,
        )


class StoreOptimizationStatusViewAPI(Resource):
    def __init__(self):
        self.service = OptimizationService

    def get(self):
        """
        获取门店对应当前是否有优化进度的状态接口
        """
        return self.service.get_store_optimization_status()


class OptimizationResetViewAPI(Resource):
    def __init__(self):
        self.service = OptimizationService
        super(OptimizationResetViewAPI, self).__init__()

    def get(self, store_id):
        optimization_service = self.service(store_id=store_id)
        optimization_service.reset_optimization()
        return optimization_service.get_optimization_results()


class OptimizationSubmitViewAPI(Resource):
    def __init__(self):
        self.service = OptimizationService
        super(OptimizationSubmitViewAPI, self).__init__()

    def get(self, store_id):
        optimization_service = self.service(store_id=store_id)
        optimization_service.submit_optimization()


class OptimizationEstimateViewAPI(Resource):
    def __init__(self):
        self.service = OptimizationService
        super(OptimizationEstimateViewAPI, self).__init__()

    def get(self, store_id):
        optimization_service = self.service(store_id=store_id)
        estimation = optimization_service.get_optimization_estimation()
        return parse_expired_info(estimation)


class SKUOptimizationViewAPI(Resource):
    def __init__(self):
        self.service = OptimizationService
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "sku_modify", type=list, location="json", required=False
        )

        super(SKUOptimizationViewAPI, self).__init__()

    def put(self, store_id):
        """
        第一次生成优化结果
        """
        args = self.reqparse.parse_args()
        sku_modify = args.get("sku_modify")

        optimization_service = self.service(store_id=store_id)
        optimization_service.modify_sku_replenishment(sku_modify)


class SKUOptimizationDownloadViewAPI(Resource):
    def __init__(self):
        self.service = OptimizationService
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "order_id",
            type=str,
            action="append",
            location="args",
            required=True,
        )
        # 默认下载类型为最终订单
        self.reqparse.add_argument(
            "type", type=int, location="args", required=False, default=2
        )

    def get(self):
        args = self.reqparse.parse_args()
        return self.service.order_download(
            args.get("order_id"), args.get("type")
        )
