# coding: utf-8

from common import DBBase, db, ma


class Store(db.Model, DBBase):
    """
    门店主数据表
    """

    __tablename__ = "store"

    store_id = db.Column(
        db.Integer, primary_key=True, autoincrement=False, nullable=False
    )
    store_name = db.Column(db.String(128), nullable=False)
    # 年销售量
    gsv = db.Column(db.Float, nullable=True)
    province = db.Column(db.String(128), nullable=False)
    city = db.Column(db.String(64), nullable=False)
    region = db.Column(db.String(64), nullable=False)
    # 开店日期
    opening_dte = db.Column(db.DateTime)


class Hub(db.Model, DBBase):
    """
    仓库数据表 / 补货关系表
    """

    __tablename__ = "hub"

    hub_id = db.Column(
        db.String(16), primary_key=True, autoincrement=False, nullable=False
    )
    store_id = db.Column(db.String(16), nullable=False)
    hub_name = db.Column(db.String(16), nullable=False)


class StoreSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Store
        fields = ("store_id", "store_name")
