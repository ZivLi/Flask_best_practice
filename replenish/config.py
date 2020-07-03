# coding: utf-8

# 安全库存天数默认为7天
SAFETY_DAYS = 7

ORDER_TEMPLATE_CONFIG = {
    "type_mapping": {
        "sku_id": str,
        "sku_name": str,
        "category": str,
        "unit_price": float,
        "store_inventory": float,
        "replenishment": float,
    }
}

FORECAST_CONFIG = {
    "type_mapping": {"sku_id": str, "qty_mean": float, "qty_std": float,}
}

HUB_INVENTORY_CONFIG = {
    "type_mapping": {"sku_id": str, "qty": float, "location_id": str,}
}

HISTORY_INVENTORY_CONFIG = {
    "type_mapping": {
        "week": str,
        "quality": int,
        "qty": float,
        "amount": float,
    },
    "sku_quality_mapping": {"NA": 0, "正品": 1, "临期": 2, "过期": 3,},
}

SAFETY_STOCK_MODEL_CONFIG = {
    "repl_days": 7,
    "rep_LT": [(2, 0)],  # LeadTime
    "service_level": 0.98,
}
