# -*- coding: utf-8 -*-
import unittest
from flask import Flask

__all__ = ['MyTestCase']


class MyTestCase(unittest.TestCase):
    def setup_app(self):
        app = Flask(__name__)
        app.config['TESTING'] = True

        self.app = app
        self.client = app.test_client()