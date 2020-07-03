# coding: utf-8
import enum


@enum.unique
class OPTIMIZATION_STATUS(enum.Enum):
    """
    优化进行状态
    """

    INIT = 0  # 生成初始化第一版优化结果
    UNDETERMINED = 1  # 修改中还未最终确认版
    FINISHED = 2  # 优化结果最终确认


OPTIMIZATION_ORDER_TYPE = {
    OPTIMIZATION_STATUS.INIT.value: "建议单",
    OPTIMIZATION_STATUS.FINISHED.value: "最终单",
}


OPTIMIZATION_SAFETY_DAYS_DEFAULT = 7  # 安全库存天数默认值为 7 天

OPTIMIZE_COUNT_REDIS_KEY = "{store_id}_optimize_cnt"  # 门店当日优化（提交订单）次数


ORDER_FILE_COLUMNS_MAPPING = {
    "sku_id": "SKU ID",
    "sku_name": "SKU名称",
    "optimized_replenishment": "建议补货量",
    "store_inventory": "当前可用库存",
    "replenishment": "补货量",
    "category": "类别",
    "unit_price": "单价（不含税）",
    "inventory_turnover_days": "库存周转天数",
    "optimized_inventory_turnover_days": "建议库存周转天数",
}
