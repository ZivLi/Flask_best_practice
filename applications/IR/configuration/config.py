# coding: utf-8
import enum

from applications.IR.api import config as api_config
from applications.IR.invoicing import (
    HubInventory,
    PromotionPlan,
    SellIn,
    SellOut,
    StoreInventory,
)
from applications.IR.sku import SKU
from applications.IR.store import Hub, Store


@enum.unique
class CONFIGURATION_STATUS(enum.Enum):
    """
    配置状态机：
        空模板 -> 数据写入数据库 -> 预测模型 -> 完成
    """

    NULL = 0  # 配置文件未上传/放弃预测回归初始状态
    SAVEDB_ING = 1  # 写入 database 数据库中
    PREDICT_ING = 2  # 预测模型运行中
    FINISHED = 3  # 配置完成状态
    FIRST_FINISHED = 4  # 第一次完成，前端根据这个会进行弹窗提示
    SAVEDB_FAILURE = 5  # 写入 database 失败
    PREDICT_FAILURE = 6  # 预测模型运行失败


CONFIGURATION_REDIS_KEY = "CONFIGURATION_SETTINGS"
# 当前配置版本信息。预测结果和优化结果都追踪以该 version 值.
CONFIGURATION_VERSION_KEY = "version"
CONFIGURATION_STATUS_KEY = "status"

CONFIGURATION_DEFAULT_SETTINGS = {
    CONFIGURATION_VERSION_KEY: None,
    CONFIGURATION_STATUS_KEY: CONFIGURATION_STATUS.NULL.value,
    "predict_cycle": [],
    "target": [],
    "min_order_amount": None,
}
CONFIGURATION_DEFAULT_SETTINGS.update(
    {k: {"updated_at": None} for k in api_config.TEMPLATE_FILE_NAME.keys()}
)


@enum.unique
class CONFIGURATION_FILE_OPTIONS(enum.Enum):
    FULL_UPDATE = 1
    INCREMENTAL_UPDATE = 2


CONFIGURATION_FILES_MODEL_MAP = {
    "store_owner_data": (Store, CONFIGURATION_FILE_OPTIONS.FULL_UPDATE),
    "hub_inventory": (
        HubInventory,
        CONFIGURATION_FILE_OPTIONS.INCREMENTAL_UPDATE,
    ),
    "store_inventory": (
        StoreInventory,
        CONFIGURATION_FILE_OPTIONS.INCREMENTAL_UPDATE,
    ),
    "purchase_data_table": (
        SellIn,
        CONFIGURATION_FILE_OPTIONS.INCREMENTAL_UPDATE,
    ),
    "sales_data_sheet": (
        SellOut,
        CONFIGURATION_FILE_OPTIONS.INCREMENTAL_UPDATE,
    ),
    "promotion_table": (
        PromotionPlan,
        CONFIGURATION_FILE_OPTIONS.INCREMENTAL_UPDATE,
    ),
    "product_master_data": (SKU, CONFIGURATION_FILE_OPTIONS.FULL_UPDATE),
    "replenishment_relationship_configuration_table": (
        Hub,
        CONFIGURATION_FILE_OPTIONS.FULL_UPDATE,
    ),
}


@enum.unique
class CONFIGURATION_PREDICT_CYCLE(enum.Enum):
    # 预测输出周期配置
    _1DAY = 1
    _2DAYS = 2
    _7DAYS = 7
    _14DAYS = 14
    _21DAYS = 21
    _28DAYS = 28


@enum.unique
class CONFIGURATION_TARGET(enum.Enum):
    # 业务目标预设
    INVENTORY_TURNOVER_RATE = 1  # 库存周转率
    MAXIMIZE_PROFITS = 2  # 最大化利润
    OUT_OF_STOCK_RATE = 3  # 缺货率
    CARGOLOSS_RATE = 4  # 货损率
