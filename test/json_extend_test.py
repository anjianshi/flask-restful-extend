# -*- coding: utf-8 -*-
from res import *
from flask import request
from flask.ext import restful
import flask_restful_extend as restful_extend
from flask_restful_extend.json_encode_manager import CantEncodeObjException
from datetime import datetime
import time
from decimal import Decimal


class JSONEncoderTestCase(MyTestCase):
    def setUp(self):
        self.setup_app()

        testcase = self
        testcase.json_data = None

        class Routes(restful.Resource):
            def get(self):
                return testcase.json_data

        self.api = restful.Api(self.app)
        self.api.add_resource(Routes, '/')

        restful_extend.enhance_json_encode(self.api)

    def verify(self, data, expect_text_result):
        self.json_data = data
        rv = self.client.get('/')
        self.assertEqual(rv.content_type, 'application/json')
        self.assertEqual(rv.data, expect_text_result)

    def test_basic_type(self):
        dataset = [
            (1, '1'),
            (500, '500'),
            (105.132, '105.132'),
            ('abc', '"abc"'),
            (u'你好', u'"你好"'.encode('utf8')),
            (True, 'true'),
            (None, 'null'),
        ]

        for data, result in dataset:
            self.verify(data, result)

    def test_composite_data_type(self):
        dataset = [
            ([1, 'a', 10.5], '[1, "a", 10.5]'),

            # can't use a tuple that length < 3 as a return value,
            # else flask-restful will resolve it as (return_value, http_status_code, other_sth)
            (('b', 5, True, 1.2), '["b", 5, true, 1.2]'),

            (dict(c=1, b=[1, 'a', True]), '{"c": 1, "b": [1, "a", true]}'),
        ]

        for data, result in dataset:
            self.verify(data, result)

    def test_predefined_encoder(self):
        def gen():
            l = [1, 2, 3]
            for i in l:
                yield i

        now = datetime.now()

        dataset = [
            (now, str(time.mktime(now.timetuple()))),
            (Decimal(10.5), '10.5'),
            (gen(), '[1, 2, 3]'),
        ]

        for data, result in dataset:
            self.verify(data, result)

    def test_custom_encoder(self):
        # specialized
        class CustomDataType(object):
            def __init__(self, a, b):
                self.a = a
                self.b = b

        self.api.json_encoder.register(lambda obj: dict(a=obj.a, b=obj.b), CustomDataType)

        # test if exception throw in common_encoder can be handle well
        def custom_common_encoder1(obj):
            raise CantEncodeObjException()

        self.api.json_encoder.register(custom_common_encoder1)

        # common_encoder
        class CustomDataType2(object):
            def __init__(self, c, d):
                self.c = c
                self.d = d

        def custom_common_encoder(obj):
            if isinstance(obj, CustomDataType2):
                return dict(c=obj.c, d=obj.d)
            else:
                raise CantEncodeObjException()

        self.api.json_encoder.register(custom_common_encoder)

        dataset = [
            (CustomDataType(Decimal(10.5), 1), '{"a": 10.5, "b": 1}'),
            (CustomDataType2(Decimal(20.0), 'a'), '{"c": 20.0, "d": "a"}'),
        ]

        for data, result in dataset:
            self.verify(data, result)


class JSONPTestCase(MyTestCase):

    callback_arg_name = 'jsonp_callback'
    js_callback = 'doIt'
    return_data = 'custom_result'

    def setUp(self):
        self.setup_app()

        testcase = self

        class Routes(restful.Resource):
            def get(self):
                return testcase.return_data

        self.api = restful.Api(self.app)
        self.api.add_resource(Routes, '/')

    def verify(self):
        rv = self.client.get('/?{}={}'.format(self.callback_arg_name, self.js_callback))
        self.assertEqual(rv.content_type, 'application/json')
        self.assertEqual(rv.data, '{}("{}")'.format(self.js_callback, self.return_data))

        rv = self.client.get('/')
        self.assertEqual(rv.content_type, 'application/json')
        self.assertEqual(rv.data, '"{}"'.format(self.return_data))

    def test_str_source(self):
        restful_extend.support_jsonp(self.api, self.callback_arg_name)
        self.verify()

    def test_fn_source(self):
        restful_extend.support_jsonp(self.api, lambda: request.args.get(self.callback_arg_name, False))
        self.verify()


