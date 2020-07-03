# coding: utf-8
import enum
from config import app_config


@enum.unique
class User_Status(enum.Enum):
    """
    用户账号状态
    """

    DEACTIVATE = -1  # 账号已禁用
    APPLYING = 0  # 账号申请中（待审批）
    APPROVED = 1  # 账号审批通过，正常使用


FORGET_PASSWORD_FRONTEND_ROUTE = "/user/reset/password/"
FORGET_PASSWORD_FRONTEND_PAGE = (
    app_config.FRONTEND_DOMAIN + FORGET_PASSWORD_FRONTEND_ROUTE
)
