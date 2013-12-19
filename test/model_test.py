# -*- coding: utf-8 -*-
import unittest
from project import app
from model_model import *
from model_data import *
import model_route
from flask import json, url_for
from flask_restful_extend.extend_model import ModelInvalid
from flask_restful_extend.model_reqparse import _ExtendedArgument
import time


class SQLAlchemyTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def tearDown(self):
        pass

    def test_model_validate(self):
        entities = list(Entity.query)
        self.assertEqual(len(entities), len(sample_data['normal_entities']))

        for data in sample_data['invalid_entities']:
            with self.assertRaises(ModelInvalid) as cm:
                Entity(**data)
            e = cm.exception
            self.assertRegexpMatches(e.message, '^db model validate failed:')

    def test_marshal(self):
        # 测试：
        # 1. 对单个实例的转换
        # 2. 对 datetime 和 float 等类型的处理
        # 3. 对各种类型的 null 值的处理
        self.assertEqual(
            self.trans_entity_data(sample_data['normal_entities'][0], 1),
            json.loads(self.app.get('/marshal/?type=1').data)
        )
        self.assertEqual(
            self.trans_entity_data(sample_data['normal_entities'][1], 2),
            json.loads(self.app.get('/marshal/?type=2').data)
        )

        # 测试对多个实例的转换
        trans_data = []
        i = 1
        for data in sample_data['normal_entities']:
            trans_data.append(self.trans_entity_data(data, i))
            i += 1
        self.assertItemsEqual(trans_data, json.loads(self.app.get('/marshal/?type=3').data))

        # 测试 excludes 功能
        data = self.trans_entity_data(sample_data['normal_entities'][0], 1)
        del data['cstr_n'], data['cbl']
        self.assertEqual(data, json.loads(self.app.post('/marshal/').data))

    def trans_entity_data(self, entity, entity_id):
        trans_entity = {unicode('id'): entity_id}
        for key, value in entity.iteritems():
            if key in ['cts', 'cts_n']:
                value = time.mktime(value.timetuple())
            elif key in ['cfl', 'cfl_n']:
                value = float(value)
            elif key in ['cstr', 'cstr_n']:
                value = unicode(value)
                if key == 'cstr_n':
                    value = value.upper()
            elif key == 'cint_n':
                value = value + 1 if value != 20 else 19
            trans_entity[unicode(key)] = value

        for field in ['cint_n', 'cstr_n', 'cfl_n', 'cbl_n', 'cts_n']:
            if field not in trans_entity:
                trans_entity[unicode(field)] = None

        return trans_entity

    def test_converter(self):
        # to_python
        rv = self.app.get('/conv/1')
        self.assertEqual(
            self.trans_entity_data(sample_data['normal_entities'][0], 1),
            json.loads(rv.data)
        )

        # to_url
        with app.test_request_context():
            self.assertEqual(
                url_for('converterroute', entity=Entity.query.get(2)),
                '/conv/2'
            )

    def test_reqparse_extendedArgument(self):
        # todo: 测试 原版的 req parser 是否已经能正确、自动的从 requests.json 中取值，
        # 而不用自己再在函数里设定一次 location=json 了？

        with app.test_request_context(method='POST', data='{"foo1": "bar"}', content_type='application/json') as ctx:
            req = ctx.request
            arg = _ExtendedArgument('foo')
            print arg.parse(req)