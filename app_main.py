# -*- coding: utf-8 -*-
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_migrate import MigrateCommand
from flask_script import Manager
from flask_script import Server
from flask_security import Security

import applications
from common import db
from common import ma
from common import login_manager
from config import app_config, SYSTEM_ADMINISTRATOR, ROLES_ABBREVIATION


def create_app():
    app = Flask(__name__)
    app.config.from_object(app_config)
    CORS(app, resources={r"/*": {"origins": "*"}})
    db.init_app(app)
    ma.init_app(app)
    login_manager.init_app(app)
    Security(app, applications.user_datastore)
    applications.configure_blueprints(app)
    return app


app = create_app()
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command("runserver", Server(host="0.0.0.0", port=5000))
manager.add_command("db", MigrateCommand)


@app.before_first_request
def before_first():
    """
    检查项目所需的数据库基础信息是否更新为最新数据
    """
    # 初始化系统管理员数据
    admin = applications.user_datastore.find_user(
        name=SYSTEM_ADMINISTRATOR["name"], is_admin=True
    ) or applications.user_datastore.create_user(
        is_admin=True, status=True, **SYSTEM_ADMINISTRATOR
    )

    # 初始化系统权限数据
    for role_id, _role in app_config.ROLES.items():
        role = applications.user_datastore.find_or_create_role(
            _role, id=role_id, description=ROLES_ABBREVIATION[_role]
        )
        # 管理员拥有全部权限
        if role not in admin.roles:
            applications.user_datastore.add_role_to_user(admin, role)

    db.session.commit()


if __name__ == "__main__":
    manager.run()
