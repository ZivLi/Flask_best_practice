# coding: utf-8
import enum


@enum.unique
class SELL_OUT_RETURN_STATUS(enum.Enum):
    """
    Sell out 类型. 参考 common.ModelBase 注释.
    """

    SALES_RETURN = False  # 退货单
    NORMAL = True  # 正常单
    SALES_RETURN_TEXT = "False"
    NORMAL_TEXT = "True"
