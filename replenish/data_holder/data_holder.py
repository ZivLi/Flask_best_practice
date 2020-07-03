# coding: utf-8

from replenish.config import (
    FORECAST_CONFIG,
    HUB_INVENTORY_CONFIG,
    HISTORY_INVENTORY_CONFIG,
    ORDER_TEMPLATE_CONFIG,
)


class BaseDataHolder:
    def __init__(self, config):
        self._data = None
        self._config = config

    @property
    def data(self):
        return self._data.copy()

    def load_and_process(self, data, *args, **kwargs):
        # dataframe 的columns 类型转换
        type_map = {}
        for col_name, dtype in self._config["type_mapping"].items():
            if col_name in data.columns:
                type_map[col_name] = dtype
        data = data.astype(type_map)
        self._data = self.process(data, *args, **kwargs)

    def process(self, data, *args, **kwargs):
        return data

    @property
    def sku_list(self):
        return list(self._data.sku_id)

    @property
    def store_sku_inv(self):
        sku_inv_dic = {}
        for i, row in self._data.iterrows():
            sku_inv_dic[row.sku_id] = row.store_inventory
        return sku_inv_dic


class OrderTemplateHolder(BaseDataHolder):
    def __init__(self):
        super().__init__(ORDER_TEMPLATE_CONFIG)

    def process(self, data, *args, **kwargs):
        data = data.fillna(0.0)
        return data


class ForecastHolder(BaseDataHolder):
    def __init__(self):
        super().__init__(FORECAST_CONFIG)

    def get_forecast_mean_std(self, params):
        """
        获取预测销量的均值标准差
        """
        data = self.data
        forecast_dict = dict()
        for i, row in data.iterrows():
            forecast_dict[row.sku_id] = [
                self._mean_std(row.qty_mean, params),
                self._mean_std(row.qty_std, params),
            ]
        return forecast_dict

    @staticmethod
    def _mean_std(data, params):
        # TODO 第一版预测天数默认是7天，此处只根据safety_days处理得出预测的均值、标准差
        return data / params["repl_days"] * params["safety_days"]

    def get_daily_forecast(self):
        # TODO 第一版 以预测均值 / 7 得出每天预测的平均数量
        data = self.data
        daily_forecast_mean = {}
        for _, row in data.iterrows():
            # 预测值为负，当做 0 处理
            daily_forecast_mean[row.sku_id] = (
                row.qty_mean / 7 if row.qty_mean > 0 else 0
            )
        return daily_forecast_mean


class HubInventoryHolder(BaseDataHolder):
    def __init__(self):
        super().__init__(HUB_INVENTORY_CONFIG)

    def process(self, data, *args, **kwargs):
        # dataframe to dict,  {sku_id:  qty_sum}
        return data.groupby(["sku_id"])["qty"].sum().to_dict()


class HistoryInventoryHolder(BaseDataHolder):
    def __init__(self):
        super().__init__(HISTORY_INVENTORY_CONFIG)
        self.bad_inv = self._config["sku_quality_mapping"].get("过期")
        self.cur_week = None
        self.hist_week = None

    def process(self, data, *args, **kwargs):
        data = data.sort_values(["week"])
        weeks = list(data["week"].unique())
        *self.hist_week, self.cur_week = weeks
        return data

    def get_hist_expired_info(self):
        expired_info_dict = {}
        data = self.data
        if self.hist_week is None:
            return {}
        for week in self.hist_week:
            stock_info = data[data["week"] == week]
            expired_info_dict[week] = self._get_expired_dateil(stock_info)
        return expired_info_dict

    def get_cur_expired_info(self):
        data = self.data
        stock_info = data[data["week"] == self.cur_week]
        expired_info = self._get_expired_dateil(stock_info)
        return expired_info

    def _get_expired_dateil(self, stock_data):
        # 当前 week 缺失数据
        if stock_data.quality.sum() < 1:
            return {
                k: 0.0
                for k in [
                    "expired_qty",
                    "expired_amount",
                    "total_amount",
                    "ratio",
                ]
            }
        expired = stock_data[stock_data["quality"] == self.bad_inv]
        total_amount = stock_data.amount.sum()
        expired_qty = expired.qty.sum()
        expired_amount = expired.amount.sum()
        return {
            "expired_qty": expired_qty,
            "expired_amount": expired_amount,
            "total_amount": total_amount,
            # 防止门店库存为0的情况
            "ratio": expired_amount / total_amount if total_amount != 0 else 0,
        }


order_template_holder = OrderTemplateHolder()
forecast_holder = ForecastHolder()
hub_inv_holder = HubInventoryHolder()
hist_inv_holder = HistoryInventoryHolder()
