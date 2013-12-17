# -*- coding: utf-8 -*-
import unittest
from project import app
import MySQLdb
from model_model import *
import model_route
from flask import json
from flask_restful_extend.extend_model import ModelInvalid
import time
from flask import url_for


conn = MySQLdb.connect(host="localhost", user="root", passwd="609888", charset='utf8')


class SQLAlchemyTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

        cur = conn.cursor()
        cur.execute('DROP DATABASE IF EXISTS flask_restful_extend_test')
        cur = conn.cursor()
        cur.execute('CREATE DATABASE flask_restful_extend_test')

        db.create_all()

        for parent in sample_data['parents']:
            p = Parent(**parent)
            db.session.add(p)

        for entity in sample_data['normal_entities']:
            e = Entity(**entity)
            db.session.add(e)

        db.session.commit()

    def tearDown(self):
        pass

    def test_model_validate(self):
        entities = [e for e in Entity.query]
        self.assertEqual(len(entities), 4)

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

        # todo: 测试 join query

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
