# coding: utf-8
import datetime
import bisect as bs
import pandas as pd
import numpy as np
from sqlalchemy import func
from common import db
from applications.IR.invoicing.models import (
    HubInventory,
    StoreInventory,
)
from applications.IR.store.service import HubService
from applications.IR.sku import SKU
from replenish import config as replenish_config
from common.datetime_utils import (
    get_today_date,
    get_past_3weeks_Monday_and_Sunday,
    format_week,
)


class StoreInventoryService:
    _model = StoreInventory

    def __init__(self, store_id=None, sku_id=None):
        self.store_id = store_id
        self.sku_id = sku_id
        # 根据 store id，sku id 封装基础查询过滤条件
        self.filter_spec = self._gen_base_filter_spec(store_id, sku_id)

    def _gen_base_filter_spec(self, store_id, sku_id):
        return self._model.format_filter_spec(
            [
                _spec
                for _spec in [
                    (self._model.location_id, store_id),
                    (self._model.sku_id, sku_id),
                ]
                if _spec[1]
            ]
        )

    def get_last_store_inventory(self, with_sku_info=False, **kwargs):
        """
        查询出最大的库存日期 StoreInventory.date，作为过滤条件查询最新的库存结果

        params kwargs 可接受参数:
        - inventory_arg: list [StoreInventory.sku_id, StoreInventory.qty] 额外的门店库存信息字段
        - sku_info: list  [SKU.sku_name, SKU.category, SKU.price, SKU.sku_id] 额外的 sku 信息字段


        (以后可能会用到的扩展实现)
        获取 store 保存数据的最新 sku 库存数据。
        先查询出每个 sku，store（location_id）的最大主键 id 值，
        然后再用 id 反查对应的 qty 值。再 server 层解决 sql 嵌套查询

        sku_inventory_max_ids = self._model.model_query(
            args=[self._model.sku_id, self._model.location_id],
            aggregated_args=[func.max(self._model.id)],
            filter_spec=self.filter_spec)
        sku_inventory_max_ids = (_id for *_, _id in sku_inventory_max_ids)

        store_inventory_df = self._model.model_query(
            args=args,
            filter_spec=[self._model.id.in_(sku_inventory_max_ids)],
            df=True)
        """

        args = [self._model.sku_id] + kwargs.get("inventory_arg", [])
        # 如果有多门店，则查询结果加上门店数据维度
        if isinstance(self.store_id, list):
            args.append(self._model.location_id)

        # 	    store_inventory sku_id
        # 	0  7.000000         10178359
        # 	1  0.222222         10207191
        # 	2  1.000000         10101849
        # 	3  1.000000         10197731
        # 	4  0.100000         10178954

        sub_query = db.session.query(
            func.max(self._model.date).label("last_inventory_date")
        ).subquery()
        store_inventory_query = (
            db.session.query(
                func.sum(self._model.qty).label("store_inventory"), *args
            )
            .join(
                sub_query, sub_query.c.last_inventory_date == self._model.date
            )
            .filter(*self.filter_spec)
            .group_by(*args)
        )
        store_inventory_df = self._model.convert_query_to_df(
            store_inventory_query
        )

        # 封装查询的 sku 信息
        if with_sku_info:
            """
            base_sku_info_df:
                        sku_name   category   unit_price    sku_id
            0     士力架花生35克散1x250  Chocolate  614.20  10027339
            1    德芙牛奶7.5g散1x1000  Chocolate  424.00  10034301
            2   德芙脆香米12g散新 1X600  Chocolate    0.00  10043726
            3  德芙摩卡榛14.5g散新1X600  Chocolate  204.80  10043728
            4  德芙果仁葡萄14.5g新1X600  Chocolate  842.28  10043730
            """
            # 默认查询 sku 信息这些，如果有补充在 kwargs 中 sku info 增加
            sku_info = [
                SKU.sku_name,
                SKU.category,
                SKU.price.label("unit_price"),
                SKU.sku_id,
            ] + kwargs.get("sku_info", [])

            sku_info_df = SKU.model_query(args=sku_info, df=True)
            # 全量 sku 信息，返回门店库存值，如果没有最新库存，补 0
            store_inventory_df = pd.merge(
                store_inventory_df, sku_info_df, how="right", on="sku_id"
            )
            store_inventory_df["store_inventory"] = store_inventory_df[
                "store_inventory"
            ].fillna(0.0)

        return store_inventory_df

    def get_past_4_weeks_inventory_status(self, sku_shelf_life):
        """
        获取过去4周（含当前周）中，每周的期末库存。
        例如：当前日期为 5.25日，则分别计算前三周(包含当前周)中最后有库存的日期当天的库存情况
        """
        _today = get_today_date()
        past_3weeks_date_range = get_past_3weeks_Monday_and_Sunday(_today)
        inventory_dates, inventory_weeks = zip(
            *[
                (
                    self._model.last_inventory_date(
                        (Monday_of_week, Sunday_of_week)
                    ),
                    format_week(Monday_of_week),
                )
                for Monday_of_week, Sunday_of_week in past_3weeks_date_range
            ]
        )

        # 封装当周没有库存更新的 no_inventory_week_df
        no_inventory_weeks = [
            week
            for index, week in enumerate(inventory_weeks)
            if inventory_dates[index] is None
        ]
        no_inventory_week_df = pd.DataFrame(
            dict(
                week=no_inventory_weeks,
                quality=replenish_config.HISTORY_INVENTORY_CONFIG.get(
                    "sku_quality_mapping"
                ).get("NA"),
                qty=np.nan,
                amount=np.nan,
            )
        )
        # 如果最近四周都没有库存更新，则直接返回 no_inventory_week_df
        """
        no_inventory_week_df:
            week   quality   qty   amount
        2020-w31    0        nan     nan
        2020-w32    0        nan     nan
        2020-w33    0        nan     nan
        2020-w34    0        nan     nan
        """
        if not any(inventory_dates):
            return no_inventory_week_df

        args = [
            self._model.sku_id,
            self._model.qty,
            self._model.amount,
            self._model.date,
            self._model.production_dte,
        ]
        """
        CAST (expression AS data_type)
        参数说明：
        expression：任何有效的 SQLServer 表达式。
        AS：用于分隔两个参数，在 AS 之前的是要处理的数据，在AS之后是要转换的数据类型。
        data_type：目标系统所提供的数据类型，包括bigint和sql_variant，不能使用用户定义的数据类型。
        """
        filter_spec = self.filter_spec + [
            db.cast(self._model.date, db.DATE).in_(
                (db.cast(_date, db.DATE) for _date in inventory_dates if _date)
            )
        ]
        inventory_df = self._model.model_query(
            args=args, filter_spec=filter_spec, df=True
        )
        inventory_df = inventory_df.merge(sku_shelf_life, on="sku_id")
        inventory_df["quality"] = inventory_df.apply(
            lambda row: self.map_inventory_freshness(
                row.date, row.production_dte, row.shelf_life
            ),
            axis=1,
        )

        sum_cols, group_cols = ["qty", "amount"], ["date", "quality"]
        inventory_status_df = (
            inventory_df[sum_cols + group_cols]
            .groupby(group_cols)
            .agg({col: "sum" for col in sum_cols})
            .reset_index()
        )
        inventory_status_df["week"] = inventory_status_df["date"].map(
            lambda _date: format_week(_date)
        )
        del inventory_status_df["date"]

        return pd.concat(
            [inventory_status_df, no_inventory_week_df], sort=False
        )

    @staticmethod
    def map_inventory_freshness(
        inventory_date: datetime.date,
        sku_production_dte: datetime.date,
        sku_shelf_life,
    ):
        """
        sku新鲜度计算公式：新鲜度 =（上传日期 - 生产日期）/ sku保质期
        正品仓：新鲜度 < 2/3
        临期仓： 2/3 < 新鲜度 < 1
        过期仓：新鲜度 > 1
        """
        freshness = (inventory_date - sku_production_dte).days / sku_shelf_life

        freshness_num = [0, 2 / 3, 1]
        freshness_level = list(
            replenish_config.HISTORY_INVENTORY_CONFIG[
                "sku_quality_mapping"
            ].values()
        )
        # 二分查找找到对应所属范围索引
        level_func = lambda num: freshness_level[bs.bisect(freshness_num, num)]

        return level_func(freshness)


class HubInventoryService:
    _model = HubInventory

    def __init__(self, hub_id=None, store_id=None, sku_id=None):
        self.hub_id = hub_id or self.get_hub_id(store_id)
        self.sku_id = sku_id

    @staticmethod
    def get_hub_id(store_id):
        return list(HubService.get_hub_id_by_store_id(store_id))

    def get_last_hub_inventory(self):
        args = [self._model.location_id, self._model.sku_id]
        aggregated_args = [func.sum(self._model.qty).label("qty")]
        filter_spec = [
            (self._model.location_id, self.hub_id),
            (self._model.date, self._model.last_inventory_date()),
        ]
        if self.sku_id is not None:
            filter_spec.append((self._model.sku_id, self.sku_id))
        return self._model.model_query(
            args=args,
            aggregated_args=aggregated_args,
            filter_spec=filter_spec,
            df=True,
        )
