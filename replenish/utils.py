# coding: utf-8
from collections import defaultdict
from copy import copy


def ensure_float(value):
    try:
        value = float(value)
    except ValueError:
        value = 0.0
    return value


def parse_expired_info(expired_info):
    """
    将坏货信息解析为前端需要的格式
    @param expired_info: dict， {'2020-w20': {'expired_qty': 12.0, 'expired_amount': 65.0, 'total_amount': 7972.0, 'ratio': 0.008}}
    @return: {"week": ["2020-w20"], "data": [{"unit": "金额", "value":500, "minus": 400, "data":[1000, 1100, 100, 500]}]}
    """
    expired_qty = defaultdict(list)
    expired_amount = copy(expired_qty)
    expired_ratio = copy(expired_qty)
    all_weeks = []
    for week, week_expired_info in expired_info.items():
        all_weeks.append(week)
        expired_qty["data"].append(week_expired_info["expired_qty"])
        expired_amount["data"].append((week_expired_info["expired_amount"]))
        expired_ratio["data"].append(week_expired_info["ratio"])
    data = [
        get_expired_detail(_dict, _type)
        for _dict, _type in [
            (expired_qty, "expired_qty"),
            (expired_amount, "expired_amount"),
            (expired_ratio, "expired_ratio"),
        ]
    ]
    return {"week": all_weeks, "data": data}


def get_expired_detail(expired_dict, expired_type):
    type_map = {
        "expired_qty": "箱数",
        "expired_amount": "金额",
        "expired_ratio": "%",
    }
    expired_dict["unit"] = type_map.get(expired_type)
    expired_dict["value"] = expired_dict["data"][-1]
    # 当前 week 与上一个 week 差值
    expired_dict["minus"] = (
        expired_dict["value"] - expired_dict["data"][-2]
        if len(expired_dict["data"]) >= 2
        else expired_dict["value"]
    )
    return expired_dict
