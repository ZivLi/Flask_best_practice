# coding: utf-8
import enum


@enum.unique
class FORECAST_STATUS(enum.Enum):
    """
    预测结果
    """

    FAILURE = 0  # 预测失败
    SUCCESS = 1  # 预测成功


RUNNING_FORECAST_VERSION_REDIS_KEY = "running_forecast_version"
FORECAST_FILE_TIME_REDIS_KEY = "forecast_at"
