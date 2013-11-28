# -*- coding: utf-8 -*-
from flask import json
from datetime import datetime
import time
from decimal import Decimal


def _transform_iterable_obj(obj):
    if hasattr(obj, '__iter__'):
        return [i for i in obj]
    else:
        raise _CantEncodeObjException()

_predefined_json_encoders = [
    (datetime, lambda value: time.mktime(value.timetuple())),
    (Decimal, lambda v: float(v))
]

_predefined_common_json_encoders = [
    _transform_iterable_obj
]


class JSONEncodeManager(object):
    """json 编码管理器
    通过它，用户可以方便地创建自定义 encoder，以处理默认的 json encoder 无法处理的数据类型


    使用方法：
    json_encode_manager = JSONEncodeManager()
    json_encode_manager.register(some_encoder, some_python_type)
    ...
    json.dumps(data, default=json_encode_manager)


    encoder 有两种：
        第一种是指定数据类型的 encoder。
        只让其处理指定类型及其子类的对象

        另一种称之为 common_encoder。
        这种 encoder 不指定数据类型。无论碰到什么值，都会尝试调用它。适用于一个 encoder 要处理多种数据类型的情况。
        common_encoder 在发现一个值不应由它来处理时，应抛出一个 TypeError 异常，这样系统才能了解情况，并把值交给下一个 encoder
        否则，无论它返回什么(包括 None)，系统都会认为这个值就是正确的计算结果，并将其返回

        指定了数据类型的 encoder 会被优先调用

    系统已经预定义了一些 encoders，分别放在 _predefined_json_encoders 和 _predefined_common_json_encoders 内。
    这两个数组中的 encoder 会被自动载入。
    """
    def __init__(self):
        self.encoders = []
        self.common_encoders = []

        self.flask_json_encoder = json.JSONEncoder()

    def register(self, encoder, target_class=None):
        if target_class:
            self.encoders.append((target_class, encoder))
        else:
            self.common_encoders.append(encoder)

    def __call__(self, o):
        encoders = []
        encoders.extend(self.encoders)
        encoders.extend(_predefined_json_encoders)
        encoders.extend(self.common_encoders)
        encoders.extend(_predefined_common_json_encoders)

        for encoder in encoders:
            if isinstance(encoder, tuple):
                if isinstance(o, encoder[0]):
                    return encoder[1](o)
            else:
                try:
                    return encoder(o)
                except _CantEncodeObjException:
                    pass
        return self.flask_json_encoder.default(o)


class _CantEncodeObjException(Exception):
    pass