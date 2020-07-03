# coding: utf-8
"""
提供项目整体可对外，和公共 api接口，不与子模板相关的通用接口.
"""
import os

from flask_restful import Resource
from flask_restful import reqparse
from werkzeug.datastructures import FileStorage

from applications.IR.api import config
from applications.IR.api.errors import DownloadTemplateFileDoesNotExistError
from applications.IR.api.service import (
    APIDownloadService,
    FileLoadService,
)
from common import EXCEL_FILE_SUFFIX
from config import RESPONSE_CREATED_SUCCESS_CODE


class TempFileLoadViewAPI(Resource):
    """
    提供临时文件上传、下载接口，系统统一api。

    文件上传流程如下：
        用户上传 origin_excel
                |
                |
        读取到内存 _dataframe，进行数据校验 -------> 校验（对转换为系统所需格式）不通过，raise 给前端 error 报错
                |
                |
        校验通过：1.保存原始 origin_excel至 config.TMP 文件夹（临时保存）；2.转换结果保存为对应 csv文件，保存至 config.TMP 文件夹
                |
                | 点击保存文件确认之后
                |
        移动 config.TMP/origin_excel 至 config.CONFIRM/origin_excel，删除 config.TMP下文件；
        转换结果 config.TMP/converted.csv 写入数据库保存，删除 converted.csv 文件

    文件下载流程如下：
        判断 config.TMP文件夹下文件是否存在 -------> 存在则直接返回下载文件（证明有临时保存版本）
                |
                | 不存在文件
                |
        取 config.CONFIRM 文件夹下对应文件 -------> 存在则直接返回下载最后一次保存的配置文件
                |
                | 不存在文件
                |
        下载对应模板文件
    """

    def __init__(self):
        self.service = FileLoadService()
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "file", type=FileStorage, location="files", required=False
        )

        super(TempFileLoadViewAPI, self).__init__()

    def get(self, file_name):
        """
        如果有临时保存文件版本，则下载临时保存文件，
        如果没有临时保存文件版本，则下载最后一次保存成功 confirm文件，
        如果没有保存过的配置文件，则下载对应模板文件。
        """
        tmp_file_path = os.path.join(
            config.TMP_SAVE_PATH, file_name + EXCEL_FILE_SUFFIX
        )
        confirm_file_path = os.path.join(
            config.CONFIRM_SAVE_PATH, file_name + EXCEL_FILE_SUFFIX
        )
        template_file_path = os.path.join(
            config.TEMPLATE_FILE_DIR, config.TEMPLATE_FILE_NAME.get(file_name),
        )
        if os.path.exists(tmp_file_path):
            file_path = tmp_file_path
        elif os.path.exists(confirm_file_path):
            file_path = confirm_file_path
        elif os.path.exists(template_file_path):
            file_path = template_file_path
        else:
            raise DownloadTemplateFileDoesNotExistError
        return APIDownloadService.download(file_path)

    def post(self, file_name):
        """
        文件上传 method
        """
        args = self.reqparse.parse_args()
        origin_file = args.get("file")
        self.service.save_tmp_file(_file=origin_file, file_name=file_name)
        return {}, RESPONSE_CREATED_SUCCESS_CODE
