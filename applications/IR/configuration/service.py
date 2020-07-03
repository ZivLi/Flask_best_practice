# coding: utf-8
import copy
import os
import shutil

from applications.IR.api import config as api_config
from applications.IR.configuration.config import (
    CONFIGURATION_DEFAULT_SETTINGS,
    CONFIGURATION_FILES_MODEL_MAP,
    CONFIGURATION_REDIS_KEY,
    CONFIGURATION_STATUS,
    CONFIGURATION_STATUS_KEY,
    CONFIGURATION_FILE_OPTIONS,
)
from common import CSV_FILE_SUFFIX, EXCEL_FILE_SUFFIX, redis_client
from common.datetime_utils import get_current_datetime
from common.file_operations import FileOperation


class ConfigurationService:
    @classmethod
    def get_status(cls):
        configuration_status = redis_client.hgetall(
            CONFIGURATION_REDIS_KEY
        ).get(CONFIGURATION_STATUS_KEY, CONFIGURATION_STATUS.NULL.value)
        return configuration_status

    @classmethod
    def get_configuration(cls):
        configuration_settings = copy.copy(CONFIGURATION_DEFAULT_SETTINGS)
        if redis_client.exists(CONFIGURATION_REDIS_KEY):
            """
            可能上传配置只上传某些文件，而不是全部上传更新，所以用上传的内容
            update default setting, 保证返回表名 list 是全的。
            """
            configuration_settings.update(
                redis_client.hgetall(CONFIGURATION_REDIS_KEY)
            )
            if (
                configuration_settings[CONFIGURATION_STATUS_KEY]
                == CONFIGURATION_STATUS.FIRST_FINISHED.value
            ):
                """
                如果配置状态为第一次预测完成（FIRST_FINISHED），将此状态返回保证前端展示完成弹窗；
                同时将redis中的配置状态update为配置完成状态（FINISHED）
                """
                update_configuration_status = (
                    CONFIGURATION_STATUS.FINISHED.value
                )
                redis_client.hset(
                    CONFIGURATION_REDIS_KEY,
                    CONFIGURATION_STATUS_KEY,
                    update_configuration_status,
                )
        return configuration_settings

    @classmethod
    def init_task(cls, configuration_settings):
        configuration_settings["status"] = CONFIGURATION_STATUS.SAVEDB_ING.value
        cls.update_configuration_settings_to_redis(configuration_settings)

    @classmethod
    def save_file_data_to_db(cls, user):
        updated_files, updated_at = dict(), get_current_datetime()
        configuration_settings = {
            "status": CONFIGURATION_STATUS.PREDICT_ING.value
        }

        for file_name in os.listdir(api_config.TMP_SAVE_PATH):
            # 遍历临时保存的上传数据文件（已经过校验、转换）csv 格式
            if not file_name.endswith(CSV_FILE_SUFFIX):
                continue

            file_update_informations = {"updated_at": updated_at}
            file_path = os.path.join(api_config.TMP_SAVE_PATH, file_name)
            df = FileOperation().read_file_to_df(file_path)
            # 获取对应 model 和更新方式
            db_model, option = CONFIGURATION_FILES_MODEL_MAP.get(
                file_name.rstrip(CSV_FILE_SUFFIX)
            )
            try:
                if option is CONFIGURATION_FILE_OPTIONS.FULL_UPDATE:
                    db_model.create_or_update(df)
                elif option is CONFIGURATION_FILE_OPTIONS.INCREMENTAL_UPDATE:
                    db_model.create(df)
                    # 动态数据更新增加执行人信息
                    file_update_informations.update({"operator": user})
                """
                如果保存临时文件写入数据库成功，则应该:
                    - move 临时保存的配置文件 excel 到 api_config.CONFIRM_SAVE_PATH 以作为确定更新版
                    - 更新缓存中 CONFIGURATION_SETTINGS 对应文件的更新时间。这里使用全局（函数内）
                updated_at 是为了忽略写入数据库的时间差，让用户不会造成确定更新配置文件成功，
                而时间不同的误解。
                """
                updated_files.update(
                    {
                        file_name.rstrip(
                            CSV_FILE_SUFFIX
                        ): file_update_informations
                    }
                )

                tmp_excel_file_path = file_path.replace(
                    CSV_FILE_SUFFIX, EXCEL_FILE_SUFFIX
                )
                confirm_path = tmp_excel_file_path.replace(
                    api_config.TMP_SAVE_PATH, api_config.CONFIRM_SAVE_PATH
                )
                shutil.move(tmp_excel_file_path, confirm_path)
            except Exception as e:
                configuration_settings[
                    "status"
                ] = CONFIGURATION_STATUS.SAVEDB_FAILURE.value
                continue
                # TODO raise error to log

        if updated_files:
            configuration_settings.update(updated_files)
        cls.update_configuration_settings_to_redis(configuration_settings)

        return (
            configuration_settings["status"]
            == CONFIGURATION_STATUS.PREDICT_ING.value
        )

    @classmethod
    def update_configuration_settings_to_redis(cls, configuration_settings):
        redis_client.hmset(CONFIGURATION_REDIS_KEY, configuration_settings)
