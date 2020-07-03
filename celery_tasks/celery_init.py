# coding: utf-8
import sys
from os.path import abspath, dirname

from celery import Celery
from flask import Flask

from common import db
from config import app_config

sys.path.insert(0, dirname(dirname(abspath(__file__))))


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app_config.CELERY_RESULT_BACKEND,
        broker=app_config.CELERY_BROKER_URL,
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


app = Flask(__name__)
app.config.from_object(app_config)
db.init_app(app)
celery = make_celery(app)


celery.autodiscover_tasks(
    ["celery_tasks.configuration_tasks", "celery_tasks.email_tasks",]
)
