# -*- coding: utf-8 -*-
import unittest
from project import app
import api_route
from api_exceptions import exception_data_list
from flask import json


class APITestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def test_exception_handle(self):
        for i in range(0, len(exception_data_list) - 1):
            data = exception_data_list[i]

            rv = self.app.get('/api/?index={}'.format(i))
            self.assertEqual(rv.status_code, data[0].code)
            self.assertEqual(json.loads(rv.data)['message'], data[1])

        rv = self.app.get('/api/?index={}'.format(len(exception_data_list) - 1))
        self.assertEqual(rv.status_code, 401)
        self.assertFalse(rv.headers.get('WWW-Authenticate', False))

