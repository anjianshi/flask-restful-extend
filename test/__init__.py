# -*- coding: utf-8 -*-
# 确保测试时载入的是本地的 flask-restful-extend 而不是通过 pip 安装到全局范围的
import sys
sys.path.insert(1, sys.path[0] + '/../')

import unittest
import model_model as model
from project import *

from error_handle_test import ErrorHandleTestCase
from json_extend_test import JSONEncoderTestCase, JSONPTestCase
from model_test import SQLAlchemyTestCase
from reqparse_test import ReqParseTestCase

"""
from flask.ext import restful


class MyRoute(restful.Resource):
    def get(self):
        from flask_restful_extend.extend_model import ModelInvalid
        raise ModelInvalid('abc error')

api.add_resource(MyRoute, '/test/')


class TestTestCase(unittest.TestCase):
    def test_route(self):
        self.app = app.test_client()
        rv = self.app.get('/test/')
        print rv.data
"""

if __name__ == '__main__':
    unittest.main()