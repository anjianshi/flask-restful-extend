# -*- coding: utf-8 -*-
from flask import json
import types
from datetime import datetime
import time
from decimal import Decimal


def _transform_iterable_obj(obj):
    if hasattr(obj, '__iter__'):
        return [i for i in obj]
    else:
        raise TypeError()

_predefined_json_encoders = [
    (datetime, lambda value: time.mktime(value.timetuple())),
    (Decimal, lambda v: float(v))
]
_predefined_common_json_encoders = [
    _transform_iterable_obj
]


class JSONEncodeManager(object):
    def __init__(self):
        # 用户可以创建自定义的 encoder，以处理默认的 json encoder 无法处理的数据类型
        #
        # encoder 有两种：
        #   第一种是指定了数据类型的 encoder。
        #   只让其处理指定类型及其子类的对象
        #
        #   另一种没有指定数据类型，则每处理一个值，都会调用它。适用于一个 encoder 要处理多种数据类型的情况。
        #   这种类型的 encoder 在发现一个值不应由它来处理时，应抛出一个 TypeError 异常，
        #   这样系统才能了解情况，并把值传给下一个 encoder
        #   否则，无论 encoder 返回什么(包括 None)，系统都会认为这个值就是正确的计算结果，并将其返回
        #
        #   指定了数据类型的 encoder 会优先调用
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
                except TypeError:
                    pass
        return self.flask_json_encoder.default(o)