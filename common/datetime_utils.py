# coding: utf-8
import datetime


def get_today_date():
    return datetime.date.today()


def get_current_datetime(_datetime_format="%Y-%m-%d %H:%M"):
    now = datetime.datetime.now()
    return format_datetime(now, _datetime_format)


def format_datetime(_datetime: datetime.datetime, _format):
    return _datetime.strftime(_format)


def get_past_3weeks_Monday_and_Sunday(_today):
    """
    获取过去 3个周的周一和周日日期
    含当前周周一和 _today
    """
    past_3weeks_date_range = [
        (
            _today
            - datetime.timedelta(_today.weekday() + 7 * i + 7),  # 获取当周的周一日期
            _today - datetime.timedelta(_today.weekday() + 7 * i + 1),
        )  # 获取当周的周日日期
        for i in range(3)
    ]
    past_3weeks_date_range.insert(
        0, (_today - datetime.timedelta(_today.weekday()), _today)
    )
    return past_3weeks_date_range


def format_week(_date: datetime.date):
    """
    日期 format 周显示
    eg: 2020-w23
    """
    return "{}-w{}".format(_date.year, _date.isocalendar()[1])
