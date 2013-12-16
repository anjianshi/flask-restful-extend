# -*- coding: utf-8 -*-
import unittest
from project import app
import MySQLdb
from model_model import *
import model_route
from flask import json
from flask_restful_extend.extend_model import ModelInvalid


conn = MySQLdb.connect(host="localhost", user="root", passwd="609888", charset='utf8')


class SQLAlchemyTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

        cur = conn.cursor()
        cur.execute('DROP DATABASE flask_restful_extend_test')
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



    """def trans_entity_data(self, student, student_id):
        trans_student = dict(id=student_id)
        for key, value in student.iteritems():
            if key == 'created':
                value = time.mktime(value.timetuple())
            elif key == 'points':
                value = float(value)
            elif isinstance(value, str):
                value = unicode(value)
            trans_student[unicode(key)] = value
        return trans_student"""

    def test_marshal(self):
        return
        # 测试对单个实例的转换，以及对 datetime 和 float 等类型及其它类型的 null 值的处理
        self.assertEqual(
            self.trans_student_data(sample_data['students'][2], 3),
            json.loads(self.app.get('/marshal/?type=1').data)
        )


        # 测试对多个实例的转换
        trans_data = []
        i = 1
        for student in sample_data['students']:
            trans_data.append(self.trans_student_data(student, i))
            i += 1

        self.assertItemsEqual(trans_data, json.loads(self.app.get('/marshal/?type=2').data))

