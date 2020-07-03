# coding: utf-8


class DownloadTemplateFileDoesNotExistError(Exception):
    status_code = 404
    message = "下载模板文件不存在"


class FileValidationError(Exception):
    status_code = 502
    message = "文件格式错误，请重新上传"


class ConfigureFileDoesNotExistError(Exception):
    status_code = 404
    message = "暂无配置文件"


class FileDoesNotExistError(Exception):
    status_code = 404
    message = "指定文件不存在"
