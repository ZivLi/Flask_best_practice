# coding: utf-8
import os

from celery_tasks.celery_init import celery, app_config


@celery.task()
def configuration_save(configuration_settings, user):
    """
    保存配置会触发的异步任务包括：
        保存上传文件到 db 【backend_db, cache_db】---> 跑预测模型
    """
    # TODO 默认预测周期为 7天
    predict_week = 7
    # si: signature immutable，不需要将前一个 task 运行结果传给后面的 task 作为首参
    task_chain = save_configuration_files_to_db.s(
        configuration_settings, user
    ) | run_predict_model.si(predict_week)
    task_chain()


@celery.task()
def save_configuration_files_to_db(configuration_settings, user):
    from applications.IR.configuration.service import ConfigurationService

    # 初始化保存配置任务，设置配置状态为写入数据库 ing
    ConfigurationService.init_task(configuration_settings)
    # 保存上传配置文件到后端数据库，更新中配置状态
    ConfigurationService.save_file_data_to_db(user)


@celery.task(bind=True)
def run_predict_model(self, predict_week):
    # 用跑预测的 celery task id 作为版本信息
    version = self.request.id

    command = f"docker run --rm --network='host' harbor.ainnovation.com/whale/whale-cli:prod \
        --redis_host={app_config.REDIS_HOST} \
        --redis_port={app_config.REDIS_PORT} \
        --redis_passwd={app_config.REDIS_PWD} \
        --rdb_url={app_config.SQLALCHEMY_DATABASE_URI} \
        --num_predict_weeks={predict_week//7} \
        --version_num={version}"
    os.system(command)
