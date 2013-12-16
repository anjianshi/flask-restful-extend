# -*- coding: utf-8 -*-
from datetime import datetime
import time
from decimal import Decimal

_time = datetime.now()


def gen():
    l = [1, 2, 3]
    for i in l:
        yield i


class CustomDataType(object):
    def __init__(self, a, b):
        self.a = a
        self.b = b


class CustomDataType2(object):
    def __init__(self, c, d):
        self.c = c
        self.d = d



encode_map = [
    # 基本类型
    (1, '1'),
    (500, '500'),
    (105.132, '105.132'),
    ('abc', '"abc"'),
    (u'你好', u'"你好"'.encode('utf8')),
    (True, 'true'),
    (None, 'null'),

    # 复合类型
    ([1, 'a', Decimal(10.5)], '[1, "a", 10.5]'),
    (dict(c=1, b=Decimal(10.5)), '{"c": 1, "b": 10.5}'),

    # 需调用 flask-restful-extend 内置的 encoder 的类型
    (_time, str(time.mktime(_time.timetuple()))),
    (Decimal(10.5), '10.5'),
    (gen(), '[1, 2, 3]'),

    # 需调用自定义 encoder 的类型
    # encoder
    (CustomDataType(Decimal(10.5), 1), '{"a": 10.5, "b": 1}'),
    # common encoder
    (CustomDataType2(Decimal(20.0), 'a'), '{"c": 20.0, "d": "a"}'),
]



