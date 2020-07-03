# coding: utf-8

from common import DBBase, db


class SKU(db.Model, DBBase):
    """
    商品主数据表
    """

    __tablename__ = "sku"

    sku_id = db.Column(
        db.String(16), primary_key=True, autoincrement=False, nullable=False
    )
    category = db.Column(db.String(64), nullable=False)
    brand = db.Column(db.String(64), nullable=False)
    sub_brand = db.Column(db.String(64), nullable=False)
    barcode = db.Column(db.BigInteger, nullable=False)
    sku_name = db.Column(db.String(128), nullable=False)
    name_en = db.Column(db.String(128), nullable=False)
    cost = db.Column(db.Float, nullable=False)
    shelf_life = db.Column(db.Integer, nullable=False)
    pack_size = db.Column(db.String(64), nullable=False)
    net_weight = db.Column(db.Float, nullable=False)
    moq = db.Column(db.Float, nullable=False)
    moa = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    is_seasonal = db.Column(db.Boolean, nullable=False)
    status = db.Column(db.Boolean, nullable=False)
