# coding: utf-8
import re
from itertools import chain
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from applications.user.models import User, Role, user_datastore, UserSchema
from common import db
from applications.user.config import User_Status, FORGET_PASSWORD_FRONTEND_PAGE
from applications.user.error import (
    UserEmailDoesNotExistError,
    TokenInvalidError,
    UserNameIncorrectError,
    UserPasswordIncorrectError,
    UserAccountApplyingError,
    UserDeactivateError,
    parse_user_exist_error,
)
from celery_tasks.email_tasks import (
    send_reset_password_email,
    send_user_approved_email,
    send_module_apply_email,
)
from config import app_config


class UserService:

    _schema = UserSchema(many=True)
    _user_model = User
    _role_model = Role

    def __init__(self, user_id, obj=None):
        self._obj = (
            obj
            if isinstance(obj, self._user_model)
            else self._user_model.query.get(user_id)
        )

    def update(self, **kwargs):
        """
        修改用户信息
        """
        if kwargs["status"] is not None:
            if kwargs["status"] == User_Status.DEACTIVATE.value:
                # 修改用户 active 为 false，表示用户账号信息已禁用（不改变 status值）方便重启用户使用。
                user_datastore.deactivate_user(self._obj)
            elif kwargs["status"] == User_Status.APPROVED.value:
                if self._obj.active:
                    # 注册用户审批通过时
                    self._obj.status = User_Status.APPROVED.value
                else:
                    # 已禁用用户账号重启，改变 active 为 true，status 保持原 approved。
                    user_datastore.activate_user(self._obj)
                send_user_approved_email.delay(self._obj.email, self._obj.name)

        if kwargs["roles"] is not None:
            old_role_set, new_role_set = (
                {role.id for role in self._obj.roles},
                set(kwargs["roles"]),
            )
            # 新增权限添加，移除权限删除
            add_roles, remove_roles = (
                new_role_set - old_role_set,
                old_role_set - new_role_set,
            )

            for add_role in add_roles:
                user_datastore.add_role_to_user(
                    self._obj, app_config.ROLES[add_role]
                )
            for remove_role in remove_roles:
                user_datastore.remove_role_from_user(
                    self._obj, app_config.ROLES[remove_role]
                )
        db.session.commit()

    @classmethod
    def create(cls, **kwargs):
        try:
            kwargs["roles"] = [
                app_config.ROLES[role] for role in kwargs["roles"]
            ]
            user_datastore.create_user(
                status=User_Status.APPROVED.value, **kwargs
            )
            db.session.commit()
        except IntegrityError as error:
            raise parse_user_exist_error(error)

    @classmethod
    def login(cls, name, password):
        user = cls._user_model.query.filter_by(name=name).first()
        if user is None:
            raise UserNameIncorrectError
        if not user.is_active:
            raise UserDeactivateError
        if not user.validate_password(password):
            raise UserPasswordIncorrectError
        if user.status is User_Status.APPLYING.value:
            raise UserAccountApplyingError
        return user

    @classmethod
    def register(cls, name, email, password):
        try:
            user_datastore.create_user(
                name=name,
                email=email,
                password=password,
                status=User_Status.APPLYING.value,
            )
            db.session.commit()
        except IntegrityError as error:
            raise parse_user_exist_error(error)

    @classmethod
    def send_reset_password_email(cls, email):
        user = User.query.filter_by(email=email).first()
        if user is None:
            raise UserEmailDoesNotExistError

        token = user.generate_confirmation_token()
        reset_password_link = FORGET_PASSWORD_FRONTEND_PAGE + token
        send_reset_password_email.delay(email, reset_password_link)

    @classmethod
    def reset_password(cls, token, new_password):
        try:
            user_id = cls._user_model.get_id_by_token(token)
            user = cls._user_model.query.get(user_id)
            user.password = new_password
            db.session.commit()
        except Exception:
            raise TokenInvalidError

    @classmethod
    def is_token_valid(cls, token):
        # 如果 token 过期，user id == None
        return cls._user_model.get_id_by_token(token) is not None

    @classmethod
    def list(cls, **kwargs):
        page, per_page = kwargs.pop("page"), kwargs.pop("per_page")
        # 用户列表不显示管理员信息
        _query = cls._user_model.query.filter_by(is_admin=False)
        # 按照用户注册的先后顺序排序
        query = _query.order_by(cls._user_model.created_at.desc())

        # 过滤用户状态筛选条件
        status = kwargs.get("status")
        if status is not None:
            if status == User_Status.DEACTIVATE.value:
                query = query.filter_by(active=False)
            elif status in (
                User_Status.APPLYING.value,
                User_Status.APPROVED.value,
            ):
                query = query.filter_by(status=status)

        # 过滤拥有某些模块权限的用户条件
        if kwargs["role"] is not None:
            users_roles = cls._role_model.query.filter(
                cls._role_model.id.in_(kwargs["role"])
            ).all()
            users = chain(*(user_role.users for user_role in users_roles))
            query = query.filter(
                cls._user_model.id.in_((user.id for user in users))
            )

        # 用户名、邮件模糊搜索
        if kwargs["keyword"] is not None:
            name_keyword = "%{}%".format(kwargs["keyword"])
            query = query.filter(
                or_(
                    cls._user_model.name.like(name_keyword),
                    cls._user_model.email.like(name_keyword),
                )
            )

        pagination = query.paginate(page, per_page)
        return {
            "currentPageNum": pagination.page,
            "currentNum": pagination.total,  # 当前条件下用户数
            "totalNum": _query.count(),  # 系统总用户数
            "users": cls._schema.dump(pagination.items),
            "hasPrev": pagination.has_prev,
            "hasNext": pagination.has_next,
        }


class ModuleService:
    @classmethod
    def permission_apply(cls, apply_info):
        send_module_apply_email.delay(apply_info)
