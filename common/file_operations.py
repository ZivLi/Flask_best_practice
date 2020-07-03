# coding: utf-8
import os

import pandas as pd

from common import CSV_FILE_SUFFIX, EXCEL_FILE_SUFFIX
from common.validations import FileValidations


class FileOperation(FileValidations):
    def __init__(self):
        pass

    def read_file_to_df(self, _file, suffix=None, sheet_name=None):
        """
        读取 _file(可以为 file path，也可以为 file文件流), 根据文件后缀确定是 excel或者 csv文件，
        分别按照读取方法读取转为dataframe
        """
        if suffix is None:
            # 如果 suffix参数为空，则根据需要读取的文件路径后缀进行解析
            suffix = self.get_file_suffix(_file)

        if suffix == EXCEL_FILE_SUFFIX:
            # TODO excel 默认 sheet name 需确定是否为 Sheet1
            _df = pd.read_excel(_file, engine="xlrd")
            if sheet_name is not None:
                _df = _df[sheet_name]
        elif suffix == CSV_FILE_SUFFIX:
            _df = pd.read_csv(_file)
        return _df

    @staticmethod
    def get_file_suffix(_file_path):
        return os.path.splitext(_file_path)[-1]
