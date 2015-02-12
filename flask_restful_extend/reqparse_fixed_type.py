# -*- coding: utf-8 -*-
"""
Call `fix_argument_convert()` function before use these type constructors.
Otherwise, they can't handle None value properly,
 the `Argument.convert()` will raise an exception when `arg_value is None`
"""
from datetime import datetime, date
import six


def fix_none(target_type):
    """Let a type constructor can handle None value:
        doing type conversion only when it is not None,
        when the value is None, return it directly."""
    return lambda value: target_type(value) if value is not None else None


def fix_number(target_type):
    return lambda value: None if isinstance(value, (str, six.text_type)) and len(value) == 0 else target_type(value)


fixed_datetime = fix_none(lambda time_str: datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S'))
fixed_date = fix_none(lambda time_str: date.fromtimestamp(time_str))
fixed_str = fix_none(six.text_type)
fixed_int = fix_none(fix_number(int))
fixed_float = fix_none(fix_number(float))
fixed_bool = fix_none(bool)


