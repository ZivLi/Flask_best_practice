# coding: utf-8

from replenish.config import SAFETY_STOCK_MODEL_CONFIG
from replenish.data_holder import (
    order_template_holder,
    forecast_holder,
    hub_inv_holder,
    hist_inv_holder,
)
from replenish.model.safety_stock_model import SafetyStockModel
from replenish.utils import ensure_float


def get_predict_quantity(
    order_template, forecast, hub_inventory, safety_days=7
):
    """
    获取sku的建议补货数量
    @param order_template: DataFrame, sku_id, sku_name, category, unit_price, store_inventory
    @param forecast: DataFrame, sku_id, qty_mean, qty_std
    @param hub_inventory: DataFrame, sku_id, qty, location_id
    @param safety_days: int, default=7
    @return dict  {sku_id: quantity}
    """
    # data preprocess
    order_template_holder.load_and_process(order_template)
    forecast_holder.load_and_process(forecast)
    hub_inv_holder.load_and_process(hub_inventory)

    # run safety stock model
    model = SafetyStockModel(safety_days)
    repl_by_sku = model.run(
        order_template_holder, forecast_holder, hub_inv_holder
    )

    return repl_by_sku


def get_storage_days(order_info, forecast, safety_days):
    """
    获取 sku 的库存天数, 库存天数 = （经销商库存 + 实际补货数量）/ 预测每天卖出数量
    特殊情况：1、sku_id不在预测结果中， 返回 -1；2、sku_id在预测结果中为负数，返回一个固定值 300
    @param order_info: list, [{'sku_id': 1003785, 'store_inventory': 3, 'replenishment': 12}]
    @param forecast: Dataframe, sku_id, qty_mean, qty_std
    @param safety_days: int
    @return dict {sku_id: days}
    """

    MAX_DAYS = 300
    params = SAFETY_STOCK_MODEL_CONFIG
    params["safety_days"] = safety_days

    forecast_holder.load_and_process(forecast)
    forecast_mean_std = forecast_holder.get_forecast_mean_std(params)

    def get_days(row):
        # 如果有在途数据，也需要算上在途数量
        total_inventory = ensure_float(row["store_inventory"]) + ensure_float(
            row["replenishment"]
        )
        if row["sku_id"] in forecast_holder.sku_list:
            daily_forecast = forecast_mean_std[row["sku_id"]][0] / safety_days
            # 如果预测值为负数，返回一个最大天数 300
            days = (
                int(total_inventory / daily_forecast)
                if daily_forecast > 0
                else MAX_DAYS
            )
            return days
        else:
            return -1

    return {item["sku_id"]: get_days(item) for item in order_info}


def get_storage_level(order_info, forecast):
    """
    库存水平天数接口 sku总库存 / sku 总需求
    @param order_info: list, [{'sku_id': 1003785, 'store_inventory': 3, 'replenishment': 12}]
    @param forecast: Dataframe, sku_id, qty_mean, qty_std
    @return storage_level: tuple, (level_before, level_after)
    """
    forecast_holder.load_and_process(forecast)
    daily_forecast = forecast_holder.get_daily_forecast()

    def get_level(storage_flag):
        inventory_total, forecast_total = 0.0, 1.0  # 避免除以0
        for row in order_info:
            store_inv = row["store_inventory"]
            if storage_flag == "after":
                # 如果有在途数据，也需计算
                store_inv += row["replenishment"]
            inventory_total += store_inv
            forecast_total += daily_forecast.get(row["sku_id"], 0)
        return inventory_total / forecast_total

    return get_level("before"), get_level("after")


def get_expired_goods_info(order_info, forecast, hist_inventory):
    """
    坏货率计算：计算过去三周的坏货率、补货之后的坏货率
    过去三周坏货率：可以直接根据门店仓库信息计算
    补货之后坏货率：需根据预测卖出的均值计算未来的坏货
        坏货数量 = 仓库期初库存 + 补货数量 - 保质期内卖出数量，坏货率 = 坏货金额 / 补货后仓库总金额
    @param order_info: list, [{'sku_id': 1033, 'store_inventory': 3, 'replenishment': 12, "unit_price": 23, "shelf_life": 365}]
    @param forecast: Dataframe, sku_id, qty_mean, qty_std
    @param hist_inventory: Dataframe, 过去四周的门店库存数据 columns: week, quality, qty, amount
    @return: dict {"week": ["2020-w20"], "data": [{"unit": "金额", "value":500, "minus": 400, "data":[1000, 1100, 100, 500]}]}
    """
    hist_inv_holder.load_and_process(hist_inventory)
    forecast_holder.load_and_process(forecast)
    daily_forecast = forecast_holder.get_daily_forecast()

    # 历史 week 坏货
    expired_info = hist_inv_holder.get_hist_expired_info()

    # 当前 week 坏货
    cur_expired_info = hist_inv_holder.get_cur_expired_info()

    # 补货后坏货
    for row in order_info:
        # 根据预测计算 产品保质期内总共卖出的数量
        inv_forecast_sellout = (
            daily_forecast.get(row["sku_id"], 0) * row["shelf_life"]
        )
        # 预测坏货
        inv_end = max(
            0,
            row["store_inventory"]
            + row["replenishment"]
            - inv_forecast_sellout,
        )
        cur_expired_info["expired_amount"] += inv_end * row["unit_price"]
        cur_expired_info["expired_qty"] += inv_end
        cur_expired_info["total_amount"] += (
            row["replenishment"] * row["unit_price"]
        )
    # 防止库存为0的情况
    cur_expired_info["ratio"] = (
        cur_expired_info["expired_amount"] / cur_expired_info["total_amount"]
        if cur_expired_info["total_amount"] != 0
        else 0
    )
    expired_info[hist_inv_holder.cur_week] = cur_expired_info
    return expired_info
    # expired_info 解析为前端需要的格式
    # return parse_expired_info(expired_info)
