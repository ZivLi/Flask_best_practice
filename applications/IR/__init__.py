# coding: utf-8
"""
智能补货项目结构为
configuration <- sku <- hub/store <- invoicing <- forecast <- optimization
从左到右依次为依赖关系
所以需要在项目中注意引用关系，避免 Circular Imports.
"""
from applications.IR.api import api_api, api_bp
from applications.IR.configuration import (
    configuration_api,
    configuration_bp,
)
from applications.IR.store import store_api, store_bp
from applications.IR.invoicing import (
    inventory_api,
    inventory_bp,
)
from applications.IR.forecast import forecast_bp, forecast_api
from applications.IR.optimization import (
    optimization_api,
    optimization_bp,
)

MODULE_PREFIX = "/IR"
IR_apis = [
    configuration_api,
    inventory_api,
    optimization_api,
    forecast_api,
    store_api,
    api_api,
]
# 智能补货模块所有蓝图及 url_prefix
IR_bps = [
    (api_bp, f"{MODULE_PREFIX}/api"),
    (configuration_bp, f"{MODULE_PREFIX}/configuration"),
    (store_bp, f"{MODULE_PREFIX}/stores"),
    (inventory_bp, f"{MODULE_PREFIX}/inventory"),
    (optimization_bp, f"{MODULE_PREFIX}/optimizations"),
    (forecast_bp, f"{MODULE_PREFIX}/forecast"),
]
