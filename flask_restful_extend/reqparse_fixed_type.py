# -*- coding: utf-8 -*-
"""
需调用 fix_argument_convert() 后才能使用
不然无法处理 None 值，一碰到 arg_value is None 的情况 Argument.convert() 就会抛出异常
"""
from datetime import datetime, date


def fix_none(target_type):
    """让某个构造器能够处理 None 值
    碰到 None 时直接返回，不是 None 时才进行类型转换"""
    return lambda value: target_type(value) if value is not None else None


def fix_number(target_type):
    return lambda value: None if isinstance(value, (str, unicode)) and len(value) == 0 else target_type(value)


fixed_datetime = fix_none(lambda time_str: datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S'))
fixed_date = fix_none(lambda time_str: date.fromtimestamp(time_str))
fixed_str = fix_none(unicode)
fixed_int = fix_none(fix_number(int))
fixed_float = fix_none(fix_number(float))
fixed_bool = fix_none(bool)


