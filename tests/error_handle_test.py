# -*- coding: utf-8 -*-
from my_test_case import MyTestCase
from flask import json
from flask.ext import restful
import flask_restful_extend as restful_extend
from werkzeug.exceptions import BadRequest, Unauthorized


class ErrorHandleTestCase(MyTestCase):
    def setUp(self):
        self.setup_app()

        testcase = self
        testcase.exception_to_raise = None

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

    def test_httpexception(self):
        self.verify(BadRequest)

    def test_std_python_exception_with_code_attribute(self):
        class CustomException(Exception):
            code = 500
        self.verify(CustomException)

    def test_exceptions_that_has_both_data_and_description_attribute(self):
        class CustomException2(BadRequest):
            def __init__(self, data):
                self.data = dict(message=data)
        self.verify(CustomException2)

    def test_unauthorized_handle(self):
        """test has `ErrorHandledApi` disabled the unauthorized dialog"""

        self.verify(Unauthorized,
                    lambda rv: self.assertFalse(rv.headers.get('WWW-Authenticate', False)))