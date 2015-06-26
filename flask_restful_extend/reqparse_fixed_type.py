# -*- coding: utf-8 -*-
from datetime import datetime, date
import six


def fix_number(target_type):
    return lambda value: None if isinstance(value, (str, six.text_type)) and len(value) == 0 else target_type(value)


fixed_datetime = lambda time_str: datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
fixed_date = lambda time_str: date.fromtimestamp(time_str)
fixed_int = fix_number(int)
fixed_float = fix_number(float)


