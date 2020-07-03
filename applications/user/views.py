# coding: utf-8
from flask_security.utils import login_user, logout_user
from applications.user.service import UserService, ModuleService
from flask_restful import Resource, reqparse
from flask_security.core import current_user
from config import RESPONSE_CREATED_SUCCESS_CODE
from applications.user.error import AnonymousUserError


class UserLoginViewAPI(Resource):
    """
    用户登陆接口
    """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "name", type=str, location="json", required=True
        )
        self.reqparse.add_argument(
            "password", type=str, location="json", required=True
        )
        super(UserLoginViewAPI, self).__init__()

    def post(self):
        args = self.reqparse.parse_args()
        name, password = args.get("name"), args.get("password")
        user = UserService.login(name, password)
        login_user(user)


class UserLogoutViewAPI(Resource):
    """
    用户登出接口
    """

    def get(self):
        logout_user()


class UserRegisterViewAPI(Resource):
    """
    用户注册接口
    """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "name", type=str, location="json", required=True
        )
        self.reqparse.add_argument(
            "password", type=str, location="json", required=True
        )
        self.reqparse.add_argument(
            "email", type=str, location="json", required=True
        )
        super(UserRegisterViewAPI, self).__init__()

    def post(self):
        args = self.reqparse.parse_args()
        name = args.get("name")
        email = args.get("email")
        password = args.get("password")
        UserService.register(name, email, password)
        return {}, RESPONSE_CREATED_SUCCESS_CODE


class ForgetPasswordViewAPI(Resource):
    """
    忘记密码，发送重置邮件
    """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "email", type=str, location="json", required=True
        )
        super(ForgetPasswordViewAPI, self).__init__()

    def post(self):
        args = self.reqparse.parse_args()
        email = args.get("email")

        UserService.send_reset_password_email(email)


class UserResetPasswordViewAPI(Resource):
    """
    重置密码
    """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "token", type=str, location="json", required=True
        )
        self.reqparse.add_argument(
            "password", type=str, location="json", required=True
        )
        super(UserResetPasswordViewAPI, self).__init__()

    def put(self):
        args = self.reqparse.parse_args()
        token = args.get("token")
        new_password = args.get("password")

        UserService.reset_password(token, new_password)


class TokenCheckViewAPI(Resource):
    """
    校验 token 是否过期接口
    """

    def __init__(self):
        super(TokenCheckViewAPI, self).__init__()

    def get(self, token):
        return UserService.is_token_valid(token)


class ModuleApplyViewAPI(Resource):
    """
    模块权限申请接口
    """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "organization", type=str, location="json", required=True
        )
        self.reqparse.add_argument(
            "name", type=str, location="json", required=True
        )
        self.reqparse.add_argument(
            "phone", type=str, location="json", required=True
        )
        self.reqparse.add_argument(
            "enterprise_email", type=str, location="json", required=True
        )
        self.reqparse.add_argument(
            "position", type=str, location="json", required=True
        )
        self.reqparse.add_argument(
            "scene", type=str, location="json", required=True
        )
        super(ModuleApplyViewAPI, self).__init__()

    def post(self):
        args = self.reqparse.parse_args()
        ModuleService.permission_apply(args)


class UserBaseInfoViewAPI(Resource):
    """
    首页用户基础信息接口
    """

    def get(self):
        # 如果是未登录的匿名用户，需要跳转回登录页面
        if current_user.is_anonymous:
            raise AnonymousUserError
        else:
            return {
                "name": current_user.name,
                "is_admin": current_user.is_admin,
                "roles": [role.id for role in current_user.roles],
            }


class UserViewAPI(Resource):
    def __init__(self):
        self.service = UserService
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "roles", type=list, location="json", required=False
        )
        self.reqparse.add_argument(
            "status", type=int, location="json", required=False
        )
        super(UserViewAPI, self).__init__()

    def put(self, user_id):
        """
        更新用户信息
        """
        args = self.reqparse.parse_args()
        user_service = UserService(user_id)
        return user_service.update(**args)


class UserListViewAPI(Resource):
    """
    用户列表页接口
    """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(UserListViewAPI, self).__init__()

    def _init_get(self):
        self.reqparse.add_argument("keyword", type=str, required=False)
        self.reqparse.add_argument("status", type=int, required=False)
        self.reqparse.add_argument("role", type=str, required=False)
        # 默认显示第1页，每页30条数据
        self.reqparse.add_argument("page", type=int, required=False, default=1)
        self.reqparse.add_argument(
            "per_page", type=int, required=False, default=30
        )

    def _init_post(self):
        self.reqparse.add_argument(
            "name", type=str, location="json", required=True
        )
        self.reqparse.add_argument(
            "password", type=str, location="json", required=True
        )
        self.reqparse.add_argument(
            "email", type=str, location="json", required=True
        )
        self.reqparse.add_argument(
            "roles", type=list, location="json", required=False, default=[]
        )

    def get(self):
        self._init_get()
        args = self.reqparse.parse_args()
        users = UserService.list(**args)
        return users

    def post(self):
        """
        新增用户
        """
        self._init_post()
        args = self.reqparse.parse_args()
        UserService.create(**args)
        return {}, RESPONSE_CREATED_SUCCESS_CODE
