# coding: utf-8
import os
import shutil
from urllib.parse import quote
from io import BytesIO

from flask import make_response
from flask import send_file

from applications.IR.api import config
from applications.IR.api.errors import (
    FileDoesNotExistError,
    FileValidationError,
)
from common import CSV_FILE_SUFFIX, EXCEL_FILE_SUFFIX
from common.file_operations import FileOperation


class FileLoadService:
    def __init__(self):
        self.op = FileOperation()

    def save_tmp_file(self, _file, file_name):
        # """
        # flask.requset.file 是 FileStorage 类型，获取的是文件流格式，只支持 read 一次,
        # 所以在这把文件流 deepcopy 出一个新对象进行内存读取，转换为 dataframe 进行转化，
        # 这么做可以避免先写成磁盘文件，再读取磁盘文件，校验不通过需要再删除的冗余操作.
        # （由于文件过大 deepcopy 会报错，此方法暂时注掉，备用）
        # """
        # _file_stream = copy.deepcopy(_file.stream)
        tmp_save_origin_file_path, tmp_save_converted_csv_path = (
            os.path.join(config.TMP_SAVE_PATH, "".join([file_name, suffix]))
            for suffix in (EXCEL_FILE_SUFFIX, CSV_FILE_SUFFIX)
        )
        _file.save(tmp_save_origin_file_path)
        # 读取文件到内存 dataframe
        df = self.op.read_file_to_df(
            tmp_save_origin_file_path, suffix=EXCEL_FILE_SUFFIX
        )

        # 如果需要做格式转换，把读取到的内容根据对应的规则进行转换 df
        convert_method = f"convert_{file_name}"
        if hasattr(self, convert_method):
            df = getattr(self, convert_method)(df)

        validation_method = f"is_{file_name}_valid"
        try:
            # 根据文件名确定对应的校验方法，如果有需要校验内容，并且校验不通过直接给前端返回报错
            if not getattr(self.op, validation_method)(df):
                raise FileValidationError
        except Exception:
            os.remove(tmp_save_origin_file_path)
            """
            如果上传文件成功且未保存配置的状态下，再次上传此文件校验未通过时需删除上一次生成的 csv 文件，
            防止保存配置时将失效的 csv 文件写入数据库。
            """
            if os.path.exists(tmp_save_converted_csv_path):
                os.remove(tmp_save_converted_csv_path)
            raise FileValidationError

        # 校验通过，将转换后的 dataframe 写到临时保存文件夹下待写入数据库的 csv
        df.to_csv(tmp_save_converted_csv_path, index=False)

    def _download(self, file_name):
        pass

    @staticmethod
    def remove_files(file_name=None, directory_path=None):
        """
        参数 file_name，删除指定文件；
        参数 directory_path，删除文件夹路径下所有文件;
        参数 file_type，指定需要删除的文件类型，eg: .csv, .xlsx, .txt
        """
        try:
            if directory_path and file_name:
                # 如果两个参数都有传值，意味着希望删除指定路径下的某个文件
                file_name = os.path.join([directory_path, file_name])
            if file_name is None:
                shutil.rmtree(directory_path)
                os.mkdir(directory_path)
            else:
                os.remove(file_name)
        except Exception:
            raise FileDoesNotExistError


class APIDownloadService:
    @classmethod
    def download(cls, _file, file_name=None):
        # _file 是文件 path，封装 response
        if isinstance(_file, str):
            if not os.path.exists(_file):
                raise FileDoesNotExistError
            response = make_response(send_file(_file))
        # _file 是 BytesIO 文件流，封装 response
        elif isinstance(_file, BytesIO):
            response = make_response(_file.read())

        # 下载文件名
        file_name = file_name or os.path.basename(_file)
        # 解决下载文件中文无法下载，乱码问题
        response.headers["Content-Disposition"] = (
            "attachment;"
            "filename={utf_filename}".format(
                utf_filename=quote(file_name.encode("utf-8"))
            )
        )
        return response
