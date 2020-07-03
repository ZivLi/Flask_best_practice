# coding: utf-8
import math
import datetime
import json
import pandas as pd
from tempfile import NamedTemporaryFile, TemporaryDirectory
import zipfile
from io import BytesIO
from sqlalchemy import func
from applications.IR.optimization.models import (
    Optimization,
    OptimizedOrder,
    OptimizationSchema,
)
from flask_security.core import current_user
from applications.IR.store import Store
from applications.IR.sku import SKU
from applications.IR.forecast.service import ForecastService
from applications.IR.invoicing.service import (
    StoreInventoryService,
    HubInventoryService,
)
from applications.IR.optimization.config import (
    OPTIMIZATION_STATUS,
    OPTIMIZATION_ORDER_TYPE,
    OPTIMIZATION_SAFETY_DAYS_DEFAULT,
)
from common import db, redis_client
from common.datetime_utils import get_today_date, get_current_datetime
from replenish import service as replenish_service
from applications.IR.optimization.config import (
    OPTIMIZE_COUNT_REDIS_KEY,
    ORDER_FILE_COLUMNS_MAPPING,
)
from applications.IR.api.service import APIDownloadService


class OptimizationService:

    _schema = OptimizationSchema()
    _model = Optimization

    def __init__(
        self, order_id=None, store_id=None, sku_id=None, safety_days=None
    ):
        self.safety_days = safety_days or OPTIMIZATION_SAFETY_DAYS_DEFAULT

        if order_id is not None:
            self._init_by_order_id(order_id)
        elif store_id is not None:
            self._init_by_store_id(store_id, sku_id)

    def _init_by_order_id(self, order_id):
        # 根据订单号获取已完成订单 _obj
        self._obj = self._model.query.filter_by(order_id=order_id).first()
        self.version = self._obj.version
        self.store_id = self._obj.store_id

    def _init_by_store_id(self, store_id, sku_id):
        # 根据门店信息，初始化对应的预测版本信息，库存信息。work for 生成初始化订单，预测优化结果等场景
        self.store_id = store_id
        self.sku_id = sku_id

        self.get_inventory_info()
        self.get_forecast_info()
        self._obj = self.get_optimization_obj_by_store_id()

    def get_optimization_obj_by_store_id(self):
        # 如果是通过 store id 来查找实例化 optimization 的，则查询的为非提交（确认保存）的最后一次结果。
        # 理论上只能有一个在当前 forecast version 下的非提交状态的 optimization
        return (
            self._model.query.filter_by(
                version=self.version, store_id=self.store_id
            )
            .filter(self._model.status != OPTIMIZATION_STATUS.FINISHED.value)
            .first()
        )

    def get_inventory_info(self):
        # 获取门店库存信息
        self.store_inventory_service = StoreInventoryService(
            store_id=self.store_id, sku_id=self.sku_id
        )
        self.store_inventory_df = self.get_store_inventory()

    def get_forecast_info(self):
        # 获取最新一版预测结果
        forecast_service = ForecastService()
        self.version = forecast_service.version
        self.forecast_df = forecast_service.get_forecast_results(
            self.store_id, self.sku_id
        )

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, version):
        self._version = version

    @property
    def optimized_order_version(self):
        return f"{self._version}_{self.store_id}"

    @staticmethod
    def simplify_status(status):
        """
        return: True / False
        True 表示当前优化状态为修改中，未最终确认
        False 表示
            - 未生成过初始化第一版结果
            - 上次优化已经最终提交完成
        """
        return status in (
            OPTIMIZATION_STATUS.INIT.value,
            OPTIMIZATION_STATUS.UNDETERMINED.value,
        )

    @classmethod
    def list(cls, **kwargs):
        page, per_page = kwargs.pop("page"), kwargs.pop("per_page")
        args = [
            cls._model.updated_at,
            cls._model.order_id,
            (
                db.cast(cls._model.store_id, db.String(10)) + Store.store_name
            ).label("store"),
            cls._model.current_inventory_turnover_days,
            cls._model.optimized_inventory_turnover_days,
        ]
        # # 订单列表只展示已完成状态的订单
        filter_spec = [(cls._model.status, OPTIMIZATION_STATUS.FINISHED.value)]
        df = cls._model.model_query(
            args=args,
            join_ons=[(Store, Store.store_id == cls._model.store_id)],
            order_keys=cls._model.updated_at.desc(),
            filter_spec=filter_spec,
            df=True,
        )

        df["updated_at"] = df.apply(
            lambda row: row.updated_at.strftime("%Y年%m月%d"), axis=1
        )
        return {
            "currentPageNum": page,
            "totalNum": df.__len__(),
            "optimizations": df[
                (page - 1) * per_page : page * per_page
            ].to_dict("record"),
        }

    def submit_optimization(self):
        """
        提交订单，修改优化状态为完成
        """
        self._obj.status = OPTIMIZATION_STATUS.FINISHED.value

        # 更新优化目标信息数据
        target_info = {"estimation": self.get_optimization_estimation()}
        if self._obj.target_info:
            target_info.update(json.loads(self._obj.target_info))
        self._obj.target_info = json.dumps(target_info)

        db.session.commit()

    def gen_order_id(self):
        """
        生成规则: 年+月+日+当天第几个订单
        eg. 20200530001
        """
        _today = get_today_date()
        optimize_count_key = OPTIMIZE_COUNT_REDIS_KEY.format(
            store_id=self.store_id
        )

        if not redis_client.exists(optimize_count_key):
            # 如果当日没有生成过优化（提交）订单，初始化缓存次数，并设置过期时间为明天0点
            redis_client.set(optimize_count_key, 0)
            tomorrow = _today + datetime.timedelta(days=1)
            expire_at = datetime.datetime(
                tomorrow.year, tomorrow.month, tomorrow.day
            )
            redis_client.expireat(optimize_count_key, expire_at)
        # 从缓存获取当日该门店已优化（提交）次数, 并自增 + 1
        optimize_cnt = redis_client.incr(optimize_count_key)

        order_id = "{store_id}_{today}{cnt}".format(
            store_id=self.store_id,
            today=_today.strftime("%Y%m%d"),
            cnt=str(optimize_cnt).zfill(3),
        )
        return order_id

    def gen_init_optimization(self, order_id=None):
        # 如果之前生成过优化结果，则首先删除之前的优化结果
        if self._obj:
            self.delete_optimization()
        # 如果安全库存天数不是默认 7 天，根据新的安全库存天数重跑优化结果，并把状态更新为修改未确定中
        if self.safety_days is not OPTIMIZATION_SAFETY_DAYS_DEFAULT:
            status = OPTIMIZATION_STATUS.UNDETERMINED.value
        else:
            status = OPTIMIZATION_STATUS.INIT.value

        sku_replenish_quantity = self.cal_sku_replenish_quantity()

        # 通过计算的 sku 对应建议补货库存量，封装 sku 补货量信息，供计算周转天数等其他接口使用
        self.replenish_info = self.format_replenish_info(sku_replenish_quantity)

        sku_storage_days = self.cal_sku_replenish_storage_days()
        # 库存周转天数向上取整
        current_turnover_days, optimized_turnover_days = (
            math.ceil(day) for day in self.cal_turnover_days()
        )

        merge_on_col = "sku_id"
        replenish_df = pd.DataFrame(
            {
                merge_on_col: list(sku_replenish_quantity.keys()),
                "optimized_replenishment": list(
                    sku_replenish_quantity.values()
                ),
            }
        )
        turnover_days_df = pd.DataFrame(
            {
                merge_on_col: list(sku_storage_days.keys()),
                "optimized_inventory_turnover_days": list(
                    sku_storage_days.values()
                ),
            }
        )
        sku_qty_price_df = self.store_inventory_df[
            [merge_on_col, "unit_price", "store_inventory"]
        ]

        optimized_order_df = replenish_df.merge(
            turnover_days_df, on=merge_on_col
        ).merge(sku_qty_price_df, on=merge_on_col)

        # 如果重置或者指定 order_id 情况下，使用 order_id 参数值。否则生成新的 order id。
        order_id = order_id or self.gen_order_id()

        optimized_order_df["order_id"] = order_id
        optimized_order_df["modify"] = 0
        # 将对应 version 优化结果写入数据库
        OptimizedOrder.create(optimized_order_df)

        # 初始生成优化结果，用 sku 单价 * 建议补货量 = 订单总金额
        amount_total = sum(
            optimized_order_df.unit_price
            * optimized_order_df.optimized_replenishment
        )
        # value 为单值的 dict 不能直接转为 dataframe
        optimization_data_df = pd.DataFrame.from_dict(
            dict(
                store_id=self.store_id,
                version=self.version,
                current_inventory_turnover_days=current_turnover_days,
                optimized_inventory_turnover_days=optimized_turnover_days,
                safe_inventory_days=self.safety_days,
                order_amount_total=amount_total,
                order_id=order_id,
                status=status,
            ),
            orient="index",
        ).T
        # 创建优化结果基础信息
        self._model.create(optimization_data_df)

        # 更新优化 _obj 对象为新生成的优化结果对象
        self._init_by_order_id(order_id)

    def cal_optimization_amount_total(self):
        amount = (
            db.session.query(
                func.sum(
                    OptimizedOrder.unit_price * OptimizedOrder.replenishment
                ).label("total")
            )
            .filter_by(version=self.optimized_order_version)
            .first()
        )
        return amount.total

    def reset_optimization(self):
        """
        撤销操作先把当前的优化结果全部删除，再通过初始默认值重新生成一版优化结果
        """
        self.gen_init_optimization(self._obj.order_id)

    def delete_optimization(self):
        OptimizedOrder.delete([(OptimizedOrder.order_id, self._obj.order_id)])
        self._model.delete([(self._model.id, self._obj.id)])

    def format_replenish_info(self, sku_replenish_quantity):
        replenish_info = self.store_inventory_df[
            ["sku_id", "store_inventory"]
        ].to_dict("record")
        for info in replenish_info:
            info["replenishment"] = sku_replenish_quantity.get(
                info["sku_id"], 0
            )
        return replenish_info

    def get_store_inventory(self, **kwargs):
        store_inventory_df = self.store_inventory_service.get_last_store_inventory(
            with_sku_info=True, **kwargs
        )
        return self.rename_store_inventory_df_cols(store_inventory_df)

    @staticmethod
    def rename_store_inventory_df_cols(store_inventory_df):
        return store_inventory_df.rename(
            columns={"price": "unit_price", "qty": "store_inventory"}
        )

    def cal_sku_replenish_quantity(self):
        """
        计算某个门店的 sku 的建议补货量, 如果 sku_id 为 None，则计算当前门店下所有 sku
        """
        # 获取门店对应仓库库存信息
        hub_inventory_df = HubInventoryService(
            store_id=self.store_id, sku_id=self.sku_id
        ).get_last_hub_inventory()
        replenish_quantities = replenish_service.get_predict_quantity(
            self.store_inventory_df,
            self.forecast_df,
            hub_inventory_df,
            self.safety_days,
        )
        return {
            **{
                sku_id: 0
                for sku_id in self.store_inventory_df.sku_id.tolist()
                - replenish_quantities.keys()
            },
            **replenish_quantities,
        }

    def cal_sku_replenish_storage_days(self):
        """
        计算某个门店的 sku 的库存可周转天数
        """
        return replenish_service.get_storage_days(
            self.replenish_info, self.forecast_df, self.safety_days
        )

    def cal_turnover_days(self):
        """
        计算某个门店库存信息，当前库存可周转天数，补货后库存周转天数
        """
        return replenish_service.get_storage_level(
            self.replenish_info, self.forecast_df
        )

    # @classmethod
    # def get_store_optimization_status_bak(cls):
    #     # 查询门店信息结果附加对应门店的优化状态(选取对应门店最新的优化结果状态数据)
    #     sub_query = db.session.query(func.max(cls._model.id).label('optimization_id')).group_by(cls._model.store_id).subquery()
    #     optimization_query = db.session.query(cls._model.store_id, cls._model.status).join(sub_query, sub_query.c.optimization_id==cls._model.id).subquery()

    #     stores_query = db.session.query(
    #         Store.store_id, Store.store_name,
    #         optimization_query.c.status.label('is_optimizing')).outerjoin(optimization_query, optimization_query.c.store_id==Store.store_id)

    #     stores = cls._model.convert_query_to_df(stores_query)
    #     stores['is_optimizing'] = \
    #         stores['is_optimizing'].map(OptimizationService.simplify_status)
    #     return stores

    @classmethod
    def get_store_optimization_status(cls):
        """
        获取当前最新预测版本下所有优化中（初始生成/修改中）的门店 id，
        merge 全部 store，返回所有门店当前优化状态
        """
        version = ForecastService().version
        optimization_query = db.session.query(
            cls._model.status.label("is_optimizing"), cls._model.store_id
        ).filter(cls._model.version == version)
        optimization_df = cls._model.convert_query_to_df(optimization_query)

        store_query = db.session.query(Store.store_id, Store.store_name)
        store_df = Store.convert_query_to_df(store_query)

        stores = pd.merge(store_df, optimization_df, on="store_id", how="left")
        stores["is_optimizing"] = stores["is_optimizing"].map(
            OptimizationService.simplify_status
        )
        return stores

    def get_optimization_results(self, only_order_sku=False):
        """
        查询订单详情结果
        :param only_order_sku: 只关心订单中 sku 结果（下载接口提供）
        """
        # 如果是生成初始化优化结果，self._obj 为 None，需要重新查询获取对象
        optimization_obj = self._obj or self.get_optimization_obj_by_store_id()

        # 获取优化结果对应的 sku 结果集
        args = [
            OptimizedOrder.id,
            OptimizedOrder.sku_id,
            OptimizedOrder.optimized_replenishment,
            OptimizedOrder.modify,
            OptimizedOrder.replenishment,
            OptimizedOrder.unit_price,
            OptimizedOrder.store_inventory,
            OptimizedOrder.inventory_turnover_days,
            OptimizedOrder.optimized_inventory_turnover_days,
            SKU.sku_name,
            SKU.category,
        ]
        optimized_sku_df = OptimizedOrder.model_query(
            args=args,
            join_ons=[(SKU, SKU.sku_id == OptimizedOrder.sku_id)],
            filter_spec=[(OptimizedOrder.order_id, self._obj.order_id)],
            df=True,
        )

        if only_order_sku:
            return optimized_sku_df
        else:
            optimization_results = self._schema.dump(optimization_obj)
            optimization_results.update(
                dict(optimized_sku_info=optimized_sku_df.to_dict("record"))
            )
            return optimization_results

    def get_optimization_estimation(self):
        self.store_inventory_df = self.get_store_inventory(
            sku_info=[SKU.shelf_life]
        )

        history_inventory_df = self.store_inventory_service.get_past_4_weeks_inventory_status(
            self.store_inventory_df[["sku_id", "shelf_life"]]
        )

        sku_optimized_replenish_df = OptimizedOrder.model_query(
            args=[OptimizedOrder.sku_id, OptimizedOrder.replenishment],
            filter_spec=[(OptimizedOrder.order_id, self._obj.order_id)],
            df=True,
        )

        order_info = pd.merge(
            self.store_inventory_df[
                ["sku_id", "store_inventory", "unit_price", "shelf_life"]
            ],
            sku_optimized_replenish_df,
            on="sku_id",
        ).to_dict("record")

        estimation = replenish_service.get_expired_goods_info(
            order_info, self.forecast_df, history_inventory_df
        )
        return estimation

    def modify_sku_replenishment(self, sku_modify_info):
        sku_optimized_updates = []
        for modify_info in sku_modify_info:
            # 封装更新数据库数据信息
            sku_optimized_update = {
                key: modify_info.pop(key)
                for key in ("id", "optimized_replenishment", "modify")
            }
            sku_optimized_updates.append(sku_optimized_update)
            # 封装 replenish_service.get_storage_days 接收 order info 参数格式
            modify_info["replenishment"] = sku_optimized_update.get(
                "optimized_replenishment"
            ) + sku_optimized_update.get("modify")

        sku_storage_days = replenish_service.get_storage_days(
            sku_modify_info, self.forecast_df, self._obj.safe_inventory_days
        )
        for sku_optimized in sku_modify_info:
            sku_optimized.update(
                dict(
                    inventory_turnover_days=sku_storage_days.get(
                        sku_optimized.get("sku_id")
                    )
                )
            )

        OptimizedOrder.update(sku_optimized_updates)

        # 将对应的优化状态修改为编辑修改中，待确定状态
        self._obj.status = OPTIMIZATION_STATUS.UNDETERMINED.value
        self._obj.order_amount_total = self.cal_optimization_amount_total()
        db.session.commit()

    def format_download_order_file_name(self, order_type):
        return f"{self.store_id}_{self._obj.order_id}{OPTIMIZATION_ORDER_TYPE[order_type]}.csv"

    @classmethod
    def order_download(cls, order_ids, order_type):
        """
        订单下载
        :param order_ids: list。如果 len(order_ids) > 1，则是批量下载
        :param order_type: 建议订单 / 最终订单
        """

        def _filter_order_type(df, _type):
            """
            :param df: order sku dataframe
            :param _type:
                - 如果是建议订单，则保留初始生成的优化结果
                - 如果是最终订单，则保留修改后的订单 sku 结果
            """
            drop_cols = (
                ["id", "modify", "replenishment", "inventory_turnover_days"]
                if _type is OPTIMIZATION_STATUS.INIT.value
                else [
                    "id",
                    "modify",
                    "optimized_replenishment",
                    "optimized_inventory_turnover_days",
                ]
            )

            return df.drop(columns=drop_cols).rename(
                columns=ORDER_FILE_COLUMNS_MAPPING
            )

        # 单个订单下载
        if len(order_ids) == 1:
            # 获取对应订单结果
            order_id = order_ids[0]
            service = cls(order_id=order_id)

            order_sku_df = service.get_optimization_results(only_order_sku=True)
            order_sku_df = _filter_order_type(order_sku_df, order_type)
            order_file_name = service.format_download_order_file_name(
                order_type
            )

            # 临时文件保存结果，供 APIDownloadService 提供下载
            with NamedTemporaryFile("w+b", suffix=".csv", delete=True) as tf:
                order_sku_df.to_csv(tf.name)
                return APIDownloadService.download(
                    tf.name, file_name=order_file_name
                )
        # 批量下载
        elif len(order_ids) > 1:
            # 临时文件夹保存结果文件集，方便后续 zip 打包操作
            with TemporaryDirectory() as td:
                order_file_names = []
                for order_id in order_ids:
                    # 获取对应订单结果
                    service = cls(order_id=order_id)
                    order_sku_df = service.get_optimization_results(
                        only_order_sku=True
                    )
                    order_sku_df = _filter_order_type(order_sku_df, order_type)
                    # 生成订单文件名
                    order_file_name = service.format_download_order_file_name(
                        order_type
                    )
                    order_file_names.append(order_file_name)

                    order_sku_df.to_csv(td + order_file_name)

                memory_file = BytesIO()
                with zipfile.ZipFile(
                    memory_file, "w", zipfile.ZIP_DEFLATED
                ) as zf:
                    for order_filename in order_file_names:
                        with open(td + order_filename, "rb") as fp:
                            zf.writestr(order_filename, fp.read())
                # 回归 seek 指针到文件头
                memory_file.seek(0)

                now = get_current_datetime(_datetime_format="%Y%m%d%H%M")
                zip_file_name = f"{current_user.name}{now}{OPTIMIZATION_ORDER_TYPE[order_type]}.zip"
                return APIDownloadService.download(
                    memory_file, file_name=zip_file_name
                )
