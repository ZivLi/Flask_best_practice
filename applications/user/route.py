# coding: utf-8
from flask import Blueprint
from flask_restful import Api

from applications.user.views import (
    UserLoginViewAPI,
    UserRegisterViewAPI,
    ForgetPasswordViewAPI,
    UserResetPasswordViewAPI,
    TokenCheckViewAPI,
    UserLogoutViewAPI,
    ModuleApplyViewAPI,
    UserBaseInfoViewAPI,
    UserListViewAPI,
    UserViewAPI,
)

user_bp = Blueprint("", __name__)
user_api = Api(user_bp)


user_api.add_resource(
    ModuleApplyViewAPI, "/module/apply", endpoint="/module/apply"
)
user_api.add_resource(
    UserLogoutViewAPI, "/auth/logout", endpoint="/auth/logout"
)
user_api.add_resource(
    UserResetPasswordViewAPI,
    "/auth/reset-password",
    endpoint="/auth/reset-password",
)
user_api.add_resource(
    ForgetPasswordViewAPI,
    "/auth/forget-password",
    endpoint="/auth/forget-password",
)
user_api.add_resource(UserLoginViewAPI, "/auth/login", endpoint="/auth/login")
user_api.add_resource(
    UserRegisterViewAPI, "/auth/register", endpoint="/auth/register"
)
user_api.add_resource(
    TokenCheckViewAPI, "/auth/valid/<string:token>", endpoint="/auth/valid"
)
user_api.add_resource(
    UserBaseInfoViewAPI, "/user/base_info", endpoint="/user/base_info"
)
user_api.add_resource(UserViewAPI, "/user/<int:user_id>", endpoint="/user")
user_api.add_resource(UserListViewAPI, "/users", endpoint="/users")
