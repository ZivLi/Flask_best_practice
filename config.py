import os
from urllib import parse
from collections import OrderedDict


BASEDIR = os.path.abspath(os.path.dirname(__file__))


ROLES_ABBREVIATION = OrderedDict(
    {
        "DP": "Demand Planning",  # 需求规划
        "SP": "Scenario Planning",  # 产能规划
        "IR": "Intelligent replenishment",  # 智能补货
        "NP": "Network Planning",  # 智慧网络
        "CT": "Control Tower",  # 供应控制塔
    }
)


class Config:
    DEBUG = True
    SECRET_KEY = os.getenv("SECRET_KEY", "tWq9wiwrcGNSmTWH6Ti9")
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SECURITY_PASSWORD_SALT = os.getenv(
        "SECURITY_PASSWORD_SALT", "qtv3qhnGNZ5JwiSmYSiW"
    )
    SESSION_COOKIE_HTTPONLY = False
    ROLES = {
        _index + 1: role
        for _index, role in enumerate(ROLES_ABBREVIATION.keys())
    }


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://{mysql_uri}"
    REDIS_HOST = '{redis_host}'
    REDIS_PORT = '{redis_port}'
    REDIS_PWD = "{redis_pwd}"
    CELERY_REDIS_PWD = parse.quote("{redis_pwd}")
    CELERY_RESULT_BACKEND = (
        f"redis://:{CELERY_REDIS_PWD}@{REDIS_HOST}:{REDIS_PORT}/1"
    )
    CELERY_BROKER_URL = CELERY_RESULT_BACKEND
    FRONTEND_DOMAIN = "{frontend_domain}"


config_by_env = dict(
    dev=DevelopmentConfig,
)
app_config = config_by_env[os.getenv("FLASK_ENV", "dev")]


RESPONSE_SUCCESS_CODE = 200
RESPONSE_CREATED_SUCCESS_CODE = 201
RESPONSE_DELETED_SUCCESS_CODE = 202
RESPONSE_SUCCESS_MSG = "Success."


SYSTEM_ADMINISTRATOR = {
    "name": "admin",
    "password": "adminpwd",
    "email": "admin@sina.com",
}
