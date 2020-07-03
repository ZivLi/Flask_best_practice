# coding: utf-8
from common import ModelBase, db, ma

from sqlalchemy.dialects.mysql import TINYINT


class Optimization(db.Model, ModelBase):
    """
    门店优化结果关系表，根据生成的对应优化结果保存基本信息
    """

    __tablename__ = "optimization"

    store_id = db.Column(db.Integer, nullable=False)
    # 对应 forecast.version
    version = db.Column(db.String(64), nullable=False)
    # 当前库存周转天数
    current_inventory_turnover_days = db.Column(db.Integer, nullable=False)
    # 补货后库存周转天数（门店维度）
    optimized_inventory_turnover_days = db.Column(db.Integer, nullable=False)
    # 安全库存天数 默认为 7 天
    safe_inventory_days = db.Column(
        db.Integer, nullable=False, server_default=db.text("7")
    )
    order_amount_total = db.Column(db.Float)
    # 预估的货损率信息和业务配置目标预设的结果，json 字段保存信息.
    target_info = db.Column(db.Text(), nullable=True)
    # 当前优化的状态：初始化，修改中，完成
    status = db.Column(TINYINT(display_width=1))
    # 订单 id，提交订单时自动生成：store_id+年+月+日+当天第几个订单 eg. 1023432_20200531002
    order_id = db.Column(db.String(64), nullable=True, index=True)


def cal_replenishment(context):
    """
    根据优化第一版 AI 优化结果的补货量 + 人工修改值 modify = 优化补货量
    """
    context_row = context.get_current_parameters()
    return context_row["optimized_replenishment"] + context_row["modify"]


def default_inventory_turnover_days(context):
    """
    默认值和优化第一版 AI 优化结果的库存周转天数相同.
    """
    return context.get_current_parameters()["optimized_inventory_turnover_days"]


class OptimizedOrder(db.Model, ModelBase):
    """
    优化结果数据表
    """

    __tablename__ = "optimized_order"

    sku_id = db.Column(db.String(16), nullable=False)
    # 当时可用库存
    store_inventory = db.Column(db.Float)
    # 优化算法根据商品主数据中对应 SKU 单价值
    unit_price = db.Column(db.Float)
    order_id = db.Column(db.String(64), nullable=True, index=True)
    """
    优化算法根据预测结果给出的第一版 AI 优化补货结果
    包括：
        - 补货量
        - 库存周转天数（门店下 SKU 维度）
    """
    optimized_replenishment = db.Column(db.Float)
    optimized_inventory_turnover_days = db.Column(db.Float)

    """
    人工修改过之后的确认版本优化补货结果
    """
    # 人工修改数据 可以 +/-
    modify = db.Column(db.Float, nullable=False, server_default=db.text("0"))
    """
    这里默认 default 值不需要在建表时候自动创建
    所以不用使用 server_default 方法，动态生成对应值即可.
    """
    replenishment = db.Column(
        db.Float,
        nullable=False,
        default=cal_replenishment,
        onupdate=cal_replenishment,
    )
    inventory_turnover_days = db.Column(
        db.Float, nullable=False, default=default_inventory_turnover_days
    )


class OptimizationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Optimization
        fields = (
            "target_info",
            "current_inventory_turnover_days",
            "optimized_inventory_turnover_days",
            "safe_inventory_days",
            "order_id",
            "order_amount_total",
            "status",
        )
