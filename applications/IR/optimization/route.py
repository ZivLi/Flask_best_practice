# coding: utf-8
from flask import Blueprint
from flask_restful import Api

from applications.IR.optimization.views import (
    OptimizationViewAPI,
    OptimizationListViewAPI,
    StoreOptimizationViewAPI,
    StoreOptimizationStatusViewAPI,
    OptimizationResetViewAPI,
    OptimizationSubmitViewAPI,
    OptimizationEstimateViewAPI,
    SKUOptimizationViewAPI,
    SKUOptimizationDownloadViewAPI,
)


optimization_bp = Blueprint("optimization", __name__)
optimization_api = Api(optimization_bp)


optimization_api.add_resource(
    OptimizationListViewAPI, "", endpoint="optimizations"
)
optimization_api.add_resource(
    OptimizationViewAPI, "/<int:order_id>", endpoint="optimizations/"
)
optimization_api.add_resource(
    StoreOptimizationViewAPI,
    "/store/<int:store_id>",
    endpoint="optimizations/store",
)
optimization_api.add_resource(
    OptimizationResetViewAPI,
    "/reset/<int:store_id>",
    endpoint="optimizations/reset",
)
optimization_api.add_resource(
    OptimizationSubmitViewAPI,
    "/submit/<int:store_id>",
    endpoint="optimizations/submit",
)
optimization_api.add_resource(
    OptimizationEstimateViewAPI,
    "/estimate/<int:store_id>",
    endpoint="optimizations/estimate",
)
optimization_api.add_resource(
    StoreOptimizationStatusViewAPI,
    "/stores/status",
    endpoint="optimizations/stores/status",
)
optimization_api.add_resource(
    SKUOptimizationViewAPI,
    "/sku-modify/<int:store_id>",
    endpoint="optimizations/sku-modify",
)
optimization_api.add_resource(
    SKUOptimizationDownloadViewAPI,
    "/download",
    endpoint="optimizations/download",
)
