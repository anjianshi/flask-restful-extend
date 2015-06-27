# -*- coding: utf-8 -*-
from .my_test_case import MyTestCase
from flask import request
from flask.ext import restful
import flask_restful_extend as restful_extend
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
        self.assertEqual(expect_text_result, rv.data.decode("utf-8"))

    def test_basic(self):
        def gen():
            l = [1, 2, 3]
            for i in l:
                yield i

        now = datetime.now()

        samples = [
            (105.132, '105.132'),
            ('abc', '"abc"'),
            (u'你好', u'"你好"'),
            (True, 'true'),
            (None, 'null'),

            ([1, 'a', 10.5], '[1, "a", 10.5]'),

            (now, str(time.mktime(now.timetuple()))),
            (Decimal(10.5), '10.5'),
            (gen(), '[1, 2, 3]'),
        ]

        for data, result in samples:
            self.verify(data, result)

    def test_custom_encoder(self):
        class CustomDataType(object):
            def __init__(self, a, b):
                self.a = a
                self.b = b

        self.api.json_encoder.register(lambda obj: obj.a + obj.b, CustomDataType)
        self.verify(CustomDataType(Decimal(10.5), 1), '11.5')


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
        self.assertEqual(rv.data.decode("utf-8"), '{}("{}")'.format(self.js_callback, self.return_data))

        rv = self.client.get('/')
        self.assertEqual(rv.content_type, 'application/json')
        self.assertEqual(rv.data.decode("utf-8"), '"{}"'.format(self.return_data))

    def test_str_source(self):
        restful_extend.support_jsonp(self.api, self.callback_arg_name)
        self.verify()

    def test_fn_source(self):
        restful_extend.support_jsonp(self.api, lambda: request.args.get(self.callback_arg_name, False))
        self.verify()


