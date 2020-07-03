# coding: utf-8
from sqlalchemy import Column, Integer, String


class DemoModel:
    __tablename__ = "demo_model"

    id = Column(Integer, primary_key=True)
    demo_field = Column(String(128), nullable=False)
