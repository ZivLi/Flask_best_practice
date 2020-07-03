# coding: utf-8
from common import ModelBase, db


class Forecast(db.Model, ModelBase):
    """
    预测结果输出表
    """

    __tablename__ = "forecast"
    __table_args__ = (
        db.Index(
            "ix_version_store_id_forecast_week",
            "version",
            "store_id",
            "predict_week",
        ),
    )

    version = db.Column(db.String(36), nullable=False)
    store_id = db.Column(db.Integer, nullable=False)
    predict_week = db.Column(db.String(8), nullable=False)
    sku_id = db.Column(db.String(16), nullable=False)
    run_week = db.Column(db.String(8), nullable=False)
    price = db.Column(
        db.Float, nullable=False
    )  # 预测结果实际用到的 sku price，可能与产品主数据中不同
    qty_mean = db.Column(db.Float, nullable=False)
    qty_std = db.Column(db.Float, nullable=False)
