# coding: utf-8
import pandas as pd
import json
from datetime import datetime
from itertools import chain

from flask_marshmallow import Marshmallow
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy, inspect
from redis import StrictRedis
from json.decoder import JSONDecodeError

from config import app_config

EXCEL_FILE_SUFFIX = ".xlsx"
CSV_FILE_SUFFIX = ".csv"


db = SQLAlchemy()
ma = Marshmallow()
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.session_protection = "strong"


class DBBase:
    """
    所有表公用字段
    如果 Model 有自己的主键(主要针对于系统的静态数据)，则继承该 class
    """

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(
        db.DateTime, default=datetime.now, onupdate=datetime.now
    )

    # 为了保证索引生效 between and 类型查询尽量放在后面，否则其他索引列失效
    """
    所有字段设置默认值请使用 server_default
    server_default 只接受字符串类型的值, 如果需要设置默认值为整形或布尔型的值，
    请使用 db.text([INT_VALUE]/[BOOL_VALUE]) 进行转换
    """

    @classmethod
    def create(cls, data):
        try:
            if isinstance(data, pd.DataFrame):
                data = data.to_dict("record")
            objects = [cls(**row) for row in data]
            db.session.bulk_save_objects(objects)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    @classmethod
    def create_or_update(cls, df):
        """
        以主键为参考值，决定 dataframe 数据:
            如果已经在表中存在，则进行更新操作;
            若不存在，则新增数据
        """
        primary_key = inspect(cls).primary_key[0].name
        primary_values = list(
            chain(*db.session.query(getattr(cls, primary_key)).all())
        )

        cls.update(df[df[primary_key].isin(primary_values)])
        cls.create(df[~df[primary_key].isin(primary_values)])

    @classmethod
    def delete(cls, filter_spec):
        try:
            db.session.query(cls).filter(
                *DBBase.format_filter_spec(filter_spec)
            ).delete(synchronize_session=False)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    @classmethod
    def update(cls, data):
        try:
            if isinstance(data, pd.DataFrame):
                data = data.to_dict("record")
            db.session.bulk_update_mappings(cls, data)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    @classmethod
    def model_query(
        cls,
        args=None,  # 查询指定列(包含 join model), 也同样被用于 group by 参数
        aggregated_args=[],  # 查询聚合结果列，如 sum，max 等
        filter_spec=None,  # 查询过滤条件(包含 join model)
        join_ons=None,  # Join 表的 set 合集
        order_keys=None,  # 排序 key
        df=False,  # 是否需要将结果直接转换为 dataframe
    ):

        # 组合所有参数部分
        query_args = args if args else [cls]  # 默认返回所有列

        assert isinstance(aggregated_args, list)
        # query 初始化
        query = db.session.query(*(query_args + aggregated_args))

        # （多）表关联查询
        if join_ons:
            for join_model, on_cols in join_ons:
                # join_model: 关联表; on_cols: 关联列
                query = query.join(join_model, on_cols)

        # 查询过滤条件
        if filter_spec:
            spec = DBBase.format_filter_spec(filter_spec)
            query = query.filter(*spec)

        if aggregated_args:
            query = query.group_by(*query_args)

        # 查询结果排序
        # TODO 多级排序优化
        if order_keys is not None:
            query = query.order_by(order_keys)

        # JUST FOR DEBUG 开发环境输出实际执行的 sql 语句
        if app_config.DEBUG:
            try:
                q = query.statement
                print(q.compile(compile_kwargs={"literal_binds": True}))
            except NotImplementedError:
                print(str(query))

        if df:
            return DBBase.convert_query_to_df(query)
        else:
            return query.all()

    @staticmethod
    def format_filter_spec(filter_spec):
        spec = []
        for _filter in filter_spec:
            if not isinstance(_filter, tuple):
                """
                非 tuple 的过滤条件，例如 >, <= 等，保持过滤条件不变
                """
                spec.append(_filter)
            else:
                """
                默认过滤等值查询用 （cls.model.key, value）的方式传参
                判断逻辑如下：
                    - 如果 value 是一个可迭代对象（非 string），
                则封装成 cls.model.key.in_(value)
                    - 如果 value 是一个单独的值，
                则封装为 cls.model.key==value
                """
                key, value = _filter
                if isinstance(value, (tuple, set, list)):
                    spec.append(key.in_(value))
                else:
                    spec.append(key == value)
        return spec

    @staticmethod
    def convert_query_to_df(_query):
        # columns 将查询的结果根据 args 直接转换为 dataframe 的列名
        return pd.DataFrame(
            _query.all(),
            columns=[column["name"] for column in _query.column_descriptions],
        )

    @staticmethod
    def _format_eq_filter_spec(attr, value):
        """
        如果参数 value 是一个可迭代对象（非 string）
        则对应的 filter 方法为 in_
        """
        if isinstance(value, (list, tuple, set)):
            return attr.in_(value)
        else:
            return attr == value


class ModelBase(DBBase):
    """
    对于没有主键或多列唯一性的 Model 创建自增 id 为主键
    """

    id = db.Column(
        db.Integer, autoincrement=True, primary_key=True, nullable=False
    )


class _Redis(StrictRedis):
    """
    重构 Redis 对于 hash 类型的操作方法，让 list，dict，tuple等可迭代数据类型，
    在获取和存储的时候进行自动 json 转换，系统层统一处理。
    """

    def hmset(self, name, mapping):
        for key, value in mapping.items():
            if not isinstance(value, (int, str)):
                mapping[key] = json.dumps(value)
        return super(_Redis, self).hmset(name, mapping)

    def hgetall(self, name):
        mapping = super(_Redis, self).hgetall(name)
        for key, value in mapping.items():
            try:
                # 如果是 json 类型数据，则在这里转换回原数据格式
                mapping[key] = json.loads(value)
            except JSONDecodeError:
                mapping[key] = value
        return mapping


redis_client = _Redis(
    host=app_config.REDIS_HOST,
    port=app_config.REDIS_PORT,
    password=app_config.REDIS_PWD,
    decode_responses=True,
    db=0,
)
