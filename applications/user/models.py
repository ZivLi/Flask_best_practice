# coding: utf-8
from common import login_manager, db, ModelBase, ma
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous.exc import SignatureExpired, BadSignature
from flask import current_app
from flask_restful import fields
from flask_security import RoleMixin, UserMixin, SQLAlchemyUserDatastore
from flask_security.utils import hash_password, verify_password

roles_users = db.Table(
    "users_roles",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("role_id", db.Integer(), db.ForeignKey("role.id")),
)


class Role(db.Model, RoleMixin, ModelBase):

    __tablename__ = "role"

    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(80))


class User(db.Model, UserMixin, ModelBase):

    __tablename__ = "user"

    name = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    # true: 为正常账号用户, false: 为禁用账号用户
    active = db.Column(db.Boolean())
    # 账号申请审批状态
    status = db.Column(db.Integer)
    is_admin = db.Column(db.Boolean(), default=False)
    roles = db.relationship(
        "Role",
        secondary=roles_users,
        backref=db.backref("users", lazy="dynamic"),
    )

    @property
    def is_active(self):
        return self.active

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    @property
    def password(self):
        raise AttributeError("password is not readable")

    @password.setter
    def password(self, password):
        self.password_hash = hash_password(password)

    def validate_password(self, password):
        return verify_password(password, self.password_hash)

    # 有效期为 24 小时
    def generate_confirmation_token(self, expiration=24 * 3600):
        """
        生成 confirm 链接校验 token
        """
        serializer = Serializer(current_app.config["SECRET_KEY"], expiration)
        return serializer.dumps({"confirm": self.id}).decode("utf-8")

    @staticmethod
    def get_id_by_token(token):
        serializer = Serializer(current_app.config["SECRET_KEY"])
        try:
            data = serializer.loads(token)
            return data.get("confirm")
        except (SignatureExpired, BadSignature):
            return None


user_datastore = SQLAlchemyUserDatastore(db, User, Role)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        fields = ("id", "name", "email", "status", "roles", "active")

    roles = ma.auto_field()


class RoleSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Role
        include_fk = True
