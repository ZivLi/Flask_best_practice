# coding: utf-8


# 所有校验方法返回 true/false，在对应 service层 raise error，保证整体结构统一性。
class FileValidations:
    @staticmethod
    def is_hub_inventory_valid(df):
        # TODO 实际的数据校验逻辑实现
        # return 'location ID' in df.columns
        return True

    @staticmethod
    def is_store_inventory_valid(df):
        # TODO 实际的数据校验逻辑实现
        # return 'location ID' in df.columns
        return True

    @staticmethod
    def is_purchase_data_table_valid(df):
        # TODO 实际的数据校验逻辑实现
        # return 'location ID' in df.columns
        return True

    @staticmethod
    def is_sales_data_sheet_valid(df):
        # TODO 实际的数据校验逻辑实现
        # return 'location ID' in df.columns
        return True

    @staticmethod
    def is_promotion_table_valid(df):
        # TODO 实际的数据校验逻辑实现
        # return 'location ID' in df.columns
        return True

    @staticmethod
    def is_product_master_data_valid(df):
        # TODO 实际的数据校验逻辑实现
        # return 'location ID' in df.columns
        return True

    @staticmethod
    def is_store_owner_data_valid(df):
        # TODO implement me.
        return True

    @staticmethod
    def is_replenishment_relationship_configuration_table_valid(df):
        # TODO implement me.
        return True

    @staticmethod
    def is_SKU_configuration_table_valid(df):
        # TODO implement me.
        return True
