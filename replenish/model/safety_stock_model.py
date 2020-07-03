# coding: utf-8

import numpy as np
import scipy.stats

from replenish.config import SAFETY_STOCK_MODEL_CONFIG


class SafetyStockModel:
    # 安全库存模型

    def __init__(self, safety_days):
        self.params = SAFETY_STOCK_MODEL_CONFIG
        self.params["safety_days"] = safety_days

    def run(self, order_template_holder, forecast_holder, hub_inv_holder):
        # get sku list
        order_skus = order_template_holder.sku_list
        forecast_skus = forecast_holder.sku_list
        sku_list = set(order_skus) & set(forecast_skus)

        # get store_inv, hub_inv
        store_inv = order_template_holder.store_sku_inv
        hub_inv = hub_inv_holder.data

        self.params["store_inv"] = store_inv
        self.params["hub_inv"] = hub_inv

        # forecast mean and std by sku-id
        forecast_mean_std = forecast_holder.get_forecast_mean_std(self.params)
        forecast_mean_std = {sku: forecast_mean_std[sku] for sku in sku_list}

        return self._run_replenish(forecast_mean_std, self.params)

    def _run_replenish(self, forecast_data, params):
        result = {}
        # 提前期均值和方差
        lt_mean, lt_std = params["rep_LT"][0][0], params["rep_LT"][0][1]
        service_level = params["service_level"]

        for sku in forecast_data:
            forecast_mean, forecast_std = forecast_data[sku]

            # 计算服务标准差个数
            sf = scipy.stats.norm.ppf(service_level)

            # 安全库存公式
            ss = np.sqrt(
                lt_mean * (forecast_std / params["safety_days"]) ** 2
                + lt_std ** 2 * (forecast_mean / params["safety_days"]) ** 2
            )
            ss = np.round(sf * ss)

            sku_store_inv = params["store_inv"].get(sku, 0)
            sku_hub_inv = params["hub_inv"].get(sku, 0)
            res = (
                ss
                + forecast_mean
                + forecast_mean * lt_mean / params["safety_days"]
            )

            # 应补货数量
            result[sku] = self._get_repl_quantity(
                res, sku_store_inv, sku_hub_inv
            )
        return result

    @staticmethod
    def _get_repl_quantity(repl, store_inv, hub_inv):
        """
        实际补货量 = 预测卖出的数量 - 经销商库存 （如果有在途数据，也需要减去）
        并且实际补货量 应小于仓库数量
        """
        repl = max(repl - store_inv, 0)
        return min(repl, hub_inv)
