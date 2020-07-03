# coding: utf-8
from applications.demo import config
from applications.demo.models import DemoModel


class DemoService:

    _model = DemoModel

    def __init__(self, obj=None):
        super(DemoService, self).__init__(obj)

        pass

    @staticmethod
    def is_demo_true(x):
        return x == config.DEMOCONFIG.TRUE.value
