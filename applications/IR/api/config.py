# coding: utf-8
from config import BASEDIR


DYNAMIC_DATA_FILE_NAME = {
    "hub_inventory": "库存数据表.xlsx",
    "store_inventory": "库存数据表.xlsx",
    "purchase_data_table": "进货数据表.xlsx",
    "sales_data_sheet": "销售数据表.xlsx",
    "promotion_table": "促销计划表.xlsx",
}


STATIC_DATA_FILE_NAME = {
    "product_master_data": "商品主数据.xlsx",
    "store_owner_data": "门店主数据.xlsx",
    "replenishment_relationship_configuration_table": "补货关系配置表.xlsx",
    "SKU_configuration": "SKU配置表.xlsx",
}


TEMPLATE_FILE_NAME = {**DYNAMIC_DATA_FILE_NAME, **STATIC_DATA_FILE_NAME}


TEMPLATE_FILE_DIR = BASEDIR + "/templates"
TMP_SAVE_PATH = TEMPLATE_FILE_DIR + "/tmp"
CONFIRM_SAVE_PATH = TEMPLATE_FILE_DIR + "/confirm"
