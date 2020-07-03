# coding: utf-8
import re


class UserNameExistError(Exception):
    status_code = 501
    message = "该用户名已存在"


class UserEmailExistError(Exception):
    status_code = 501
    message = "该邮箱已注册"


CreateUserErrors = {
    "name": UserNameExistError,
    "email": UserEmailExistError,
}


def parse_user_exist_error(error):
    # 检查用户名 / 邮箱是否已存在
    error_field = re.findall(r"key \'(.*)\'\"\)", str(error))[0]
    return CreateUserErrors[error_field]


class AnonymousUserError(Exception):
    status_code = 502
    message = "匿名用户未登录"


class UserEmailDoesNotExistError(Exception):
    status_code = 503
    message = "该邮箱不存在"


class TokenInvalidError(Exception):
    status_code = 504
    # 前端自动跳转 token 过期重新获取重置密码链接页面，不依赖于后端返回 msg
    message = "token已过期，请重新申请链接"


class UserNameIncorrectError(Exception):
    status_code = 505
    message = "该用户名不存在"


class UserPasswordIncorrectError(Exception):
    status_code = 506
    message = "密码错误"


class UserAccountApplyingError(Exception):
    status_code = 507
    message = "用户注册审批中"


class UserDeactivateError(Exception):
    status_code = 508
    message = "此账号已到期，请联系管理员。"
