# -*- coding: utf-8 -*-
from my_test_case import MyTestCase
from flask import json
from flask.ext import restful
import flask_restful_extend as restful_extend
from werkzeug.exceptions import BadRequest, Unauthorized, HTTPException


class ErrorHandleTestCase(MyTestCase):
    def setUp(self):
        self.setup_app()

        testcase = self
        testcase.exception_to_raise = None
        testcase.error_message = "custom_error_msg"

        class Routes(restful.Resource):
            def get(self):
                raise testcase.exception_to_raise

        api = restful_extend.ErrorHandledApi(self.app)
        api.add_resource(Routes, '/')

    def verify(self, exception_cls, extra_verify=None):
        """check if `ErrorHandledApi` can handling this kind of exception
         and return right status code and error message."""

        error_message = "custom_error_msg"
        exception = exception_cls(error_message)
        status_code = exception.code if hasattr(exception, 'code') else 500

        self.exception_to_raise = exception_cls(error_message)
        rv = self.client.get('/')
        self.assertEqual(rv.status_code, status_code)
        self.assertEqual(json.loads(rv.data)['message'], error_message)

        if extra_verify:
            extra_verify(rv)

    def make_exce_request(self, exception_cls):
        """make a request, that raise the specified exception"""
        self.exception_to_raise = exception_cls(self.error_message)
        resp = self.client.get('/')
        return [resp.status_code, json.loads(resp.data)["message"]]

    def test_HTTPException(self):
        [code, msg] = self.make_exce_request(BadRequest)
        self.assertEqual(code, 400)
        self.assertEqual(msg, self.error_message)

    def test_custom_HTTPException(self):
        class CustomHTTPException(HTTPException):
            code = 401
        [code, msg] = self.make_exce_request(CustomHTTPException)
        self.assertEqual(code, 401)
        self.assertEqual(msg, self.error_message)

    def test_HTTPException_that_already_has_data_attr(self):
        """如果一个 HTTPException 已经有 data attribute，那么 flask-restful-extend 就不应该再用 exception 的 describe 去填充 data 了"""
        class CustomHTTPException2(HTTPException):
            code = 403
            data = dict(message="another message")
        [code, msg] = self.make_exce_request(CustomHTTPException2)
        self.assertEqual(code, 403)
        self.assertEqual(msg, "another message")

    def test_std_python_exception(self):
        with self.assertRaises(Exception) as cm:
            self.make_exce_request(Exception)
        self.assertEqual(cm.exception.message, self.error_message)

    def test_custom_python_exception_with_code_attr(self):
        """早期的 flask-restful 的 error_handle 会把所有包含 code attribute 的 exception 作为 HTTPException 来处理，
        但经过 https://github.com/flask-restful/flask-restful/pull/445 这个 issue，它改为只处理真正的 HTTPException 了。
        所以这里要检查一下 flask-restful-extend 是否也遵从了这个行为"""
        class CustomException1(Exception):
            code = 405

        with self.assertRaises(CustomException1) as cm:
            self.make_exce_request(CustomException1)
        self.assertEqual(cm.exception.message, self.error_message)

    def test_unauthorized_handle(self):
        """test has `ErrorHandledApi` disabled the unauthorized dialog"""
        self.verify(Unauthorized,
                    lambda rv: self.assertFalse(rv.headers.get('WWW-Authenticate', False)))
