# -*- coding: utf-8 -*-
import unittest
from project import app, api
import flask_restful_extend as restful_extend
from json_data import encode_map
import json_route


class JSONTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def test_json_encode(self):
        """测试各种类型能否正确编码"""
        for index in range(0, len(encode_map)):
            rv = self.app.get('/json/?result=' + str(index))
            self.assertEqual(rv.content_type, 'application/json')
            self.assertEqual(rv.data, encode_map[index][1])

    def test_jsonp(self):
        """测试 jsonp 是否正常工作"""
        restful_extend.support_jsonp(api, 'jsonp_callback')

        rv = self.app.get('/json/?result=3&jsonp_callback=doIt')
        self.assertEqual(rv.content_type, 'application/json')
        self.assertEqual(rv.data, 'doIt({})'.format(encode_map[3][1]))