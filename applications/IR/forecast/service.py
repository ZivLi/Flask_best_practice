# coding: utf-8
import os
from common import CSV_FILE_SUFFIX
from applications.IR.forecast import Forecast
from applications.IR.sku import SKU
from applications.IR.configuration import config as configuration_config
from applications.IR.forecast import errors
from applications.IR.forecast.config import (
    FORECAST_FILE_TIME_REDIS_KEY,
    FORECAST_STATUS,
)
from applications.IR.invoicing.service import StoreInventoryService
from applications.IR.api import config as api_config
from common import redis_client


class ForecastService:

    _model = Forecast

    def __init__(self, forecast_version=None):
        self.version = forecast_version or self.get_last_forecast_version()
        if self.version is None:
            # no forecast yet.
            raise errors.ForecastVersionDoesNotExistError

    @staticmethod
    def get_last_forecast_version():
        return redis_client.hget(
            configuration_config.CONFIGURATION_REDIS_KEY,
            configuration_config.CONFIGURATION_VERSION_KEY,
        )

    def get_forecast_results(
        self,
        store_id,
        sku_id=None,
        with_sku_info=False,
        with_inventory_info=False,
    ):
        """
        params:
            store_id                获取对应 store 的预测结果
            sku_id                  只查询部分 sku 信息，None 为全部 sku 信息
            with_sku_info           是否需要 Join 商品信息
            with_inventory_info     是否需要 Join 当前（门店）库存信息
        """
        # 默认查询某个门店在某次预测结果中，sku 对应的预测结果
        args = [self._model.qty_mean, self._model.qty_std, self._model.sku_id]
        filter_spec = [
            self._model.version == self.version,
            self._model.store_id == store_id,
        ]
        if sku_id is not None:
            filter_spec.append((self._model.sku_id, sku_id))
        join_ons, order_keys = [], None
        # 封装对应的 sku 信息
        if with_sku_info:
            args.extend([SKU.sku_name, SKU.category, SKU.price])
            join_ons.extend([(SKU, SKU.sku_id == self._model.sku_id)])

        result_df = self._model.model_query(
            args=args,
            filter_spec=filter_spec,
            join_ons=join_ons,
            order_keys=order_keys,
            df=True,
        )

        # 封装对应门店的当前（最后日期）的库存信息
        if with_inventory_info:
            store_inventory_df = StoreInventoryService(
                store_id=store_id, sku_id=result_df.sku_id.tolist()
            ).get_last_store_inventory()
            result_df = result_df.merge(store_inventory_df, on=["sku_id"])

        return result_df

    @classmethod
    def update_forecast_status(cls, version, status):
        if status == FORECAST_STATUS.SUCCESS.value:
            # 如果预测成功，更新 configuration 保存的当前版本信息, 并修改配置状态为完成
            update_configurations = {
                configuration_config.CONFIGURATION_VERSION_KEY: version,
                configuration_config.CONFIGURATION_STATUS_KEY: configuration_config.CONFIGURATION_STATUS.FIRST_FINISHED.value,
                # 更新配置缓存中当前修改的文件预测版本的时间
                **ForecastFileTimeService.set(),
            }
        else:
            update_configurations = {
                configuration_config.CONFIGURATION_STATUS_KEY: configuration_config.CONFIGURATION_STATUS.PREDICT_FAILURE.value
            }
        redis_client.hmset(
            configuration_config.CONFIGURATION_REDIS_KEY, update_configurations
        )

    @classmethod
    def cancel_forecast(cls):
        """
        预测端在生成预测结果之后，去检查当前 status 状态是否正常：
         * configuration 状态为 PREDICT_ING 则直接将预测结果入库，并回调完成接口
         * configuration 状态为 null ，则表明已经放弃预测，无需其他操作
        """
        # 修改配置状态为初始化
        redis_client.hset(
            configuration_config.CONFIGURATION_REDIS_KEY,
            configuration_config.CONFIGURATION_STATUS_KEY,
            configuration_config.CONFIGURATION_STATUS.NULL.value,
        )


class ForecastFileTimeService:
    @classmethod
    def get(cls):
        configuration_settings = redis_client.hgetall(
            configuration_config.CONFIGURATION_REDIS_KEY
        )
        return {
            dynamic_file: configuration_settings.get(dynamic_file, {}).get(
                FORECAST_FILE_TIME_REDIS_KEY
            )
            for dynamic_file in api_config.DYNAMIC_DATA_FILE_NAME.keys()
        }

    @classmethod
    def set(cls):
        forecast_file_times = {}
        configuration_settings = redis_client.hgetall(
            configuration_config.CONFIGURATION_REDIS_KEY
        )
        """
        遍历 TMP_SAVE_PATH 下所有文件，（已经写入数据库的当前版本上传的 [convert].csv 文件）
        更新缓存中对应的文件配置，预测时间为最新写入数据库时候的保存文件时间
        """
        for new_file_for_forecast in os.listdir(api_config.TMP_SAVE_PATH):
            # # mac 环境下本地会生成 .DS_STORE 文件，需要考虑怎么避免这种情况。这个 if 判断只有这一种情况会进入当前分支(开发时，视情况
            # # 使用下面if判断语句)
            # if not new_file_for_forecast.endswith(CSV_FILE_SUFFIX):
            #     continue

            file_name = new_file_for_forecast.rstrip(CSV_FILE_SUFFIX)
            file_configuration = configuration_settings[file_name]
            file_configuration.update(
                {
                    FORECAST_FILE_TIME_REDIS_KEY: file_configuration.get(
                        "updated_at"
                    )
                }
            )
            forecast_file_times[file_name] = file_configuration

            # 删除 TMP_SAVE_PATH 下对应的 csv 文件，以防上传新的配置文件数据重复写入
            file_path = os.path.join(
                api_config.TMP_SAVE_PATH, new_file_for_forecast
            )
            os.remove(file_path)

        return forecast_file_times
