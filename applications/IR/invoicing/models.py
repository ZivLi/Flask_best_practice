# coding: utf-8
from applications.IR.invoicing import config
from common import ModelBase, db
from sqlalchemy import func


class InvoicingModelBase(ModelBase):
    """
    进销存相关表都会用到的 base 字段
    """

    sku_id = db.Column(db.String(16), nullable=False)
    qty = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime)

    @classmethod
    def last_inventory_date(cls, date_range=None):
        """
        查询库存更新的最后日期，如果有 date_range，则查询为 range 内结果
        """
        _query = db.session.query(func.max(cls.date))
        if date_range:
            _query = _query.filter(cls.date.between(*date_range))
        return _query.first()[0]


class SellIn(db.Model, InvoicingModelBase):
    """
    进货数据表
    """

    __tablename__ = "sell_in"
    __table_args__ = (db.Index("ix_store_id_date", "store_id", "date"),)

    store_id = db.Column(db.Integer, nullable=False)


class SellOut(db.Model, InvoicingModelBase):
    """
    销售数据表
    """

    __tablename__ = "sell_out"
    __table_args__ = (db.Index("ix_store_id_date", "store_id", "date"),)

    store_id = db.Column(db.Integer, nullable=False)
    is_return = db.Column(
        db.Boolean,
        nullable=False,
        server_default=db.text(config.SELL_OUT_RETURN_STATUS.NORMAL_TEXT.value),
    )
    price = db.Column(db.Float, nullable=False)


class InventoryModelBase(InvoicingModelBase):
    """
    库存相关表会用到的 base 字段扩展
    """

    production_dte = db.Column(db.DateTime)


class StoreInventory(db.Model, InventoryModelBase):
    """
    门店库存数据表
    """

    __tablename__ = "store_inventory"
    __table_args__ = (db.Index("ix_location_id_date", "location_id", "date"),)

    # location_id is Foreign store.store_id
    location_id = db.Column(db.Integer, nullable=False)


class HubInventory(db.Model, InventoryModelBase):

    __tablename__ = "hub_inventory"
    __table_args__ = (db.Index("ix_location_id_date", "location_id", "date"),)

    # location_id is Foreign hub.hub_id
    location_id = db.Column(db.String(16), nullable=False)


class PromotionPlan(db.Model, ModelBase):
    """
    促销计划表
    """

    __tablename__ = "promotion"
    __table_args__ = (db.Index("ix_store_id_sku_id", "store_id", "sku_id"),)

    store_id = db.Column(db.Integer, nullable=False)
    sku_id = db.Column(db.Integer, nullable=False)
    start_dte = db.Column(db.DateTime)
    end_dte = db.Column(db.DateTime)
    discount = db.Column(db.Float, nullable=False)
