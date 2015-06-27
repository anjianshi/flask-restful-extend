# -*- coding: utf-8 -*-
from .my_test_case import MyTestCase
from sqlalchemy import Column, Integer, String, Float, Boolean, TIMESTAMP, text
from flask.ext.sqlalchemy import SQLAlchemy
from flask_restful_extend.model_validates import complex_validates, ModelInvalid
from flask_restful_extend import register_model_converter, marshal_with_model, quick_marshal
from flask_restful_extend.model_reqparse import make_request_parser, populate_model, \
    RequestPopulator, PopulatorArgument, ArgumentNoValue
from flask_restful_extend.reqparse_fixed_type import *
from flask.ext import restful
from flask.ext.restful.reqparse import Argument
from flask.ext.restful import fields
from flask import url_for, request
from datetime import datetime
import time
from copy import copy
from copy import deepcopy
import json
import six


class ModelValidateTestCase(MyTestCase):
    def setUp(self):
        self.setup_app()

        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        self.db = SQLAlchemy(self.app)

    def setup_model(self, validate_rule):
        class Student(self.db.Model):
            id = Column(Integer, primary_key=True)
            name = Column(String(100), nullable=False)
            age = Column(Integer)
            notes = Column(String(100))

            validator = complex_validates(validate_rule)

        self.Student = Student
        self.db.create_all()

    def verify_exception(self, data):
        with self.assertRaises(ModelInvalid) as cm:
            self.Student(**data)
        self.assertRegexpMatches(six.text_type(cm.exception), '^db model validate failed:')

    def test_predefined_predicates(self):
        self.setup_model({
            # 对允许 NULL 值和不允许 NULL 值的字段都进行测试
            'name': [('min_length', 5), ('max_length', 10), ('match', '^abc'), 'trans_upper'],
            'notes': [('min_length', 5), ('max_length', 10), ('match', '^abc'), 'trans_upper'],
            'age': [('min', 15), ('max', 20)]
        })

        # ===== 能否正确处理合法值 =====

        valid_data = [
            dict(name='abcdee', age=18, notes='abcdegf'),  # 填充所有字段
            dict(name='abcd13', age=16),        # 填充必填和部分选填字段
            dict(name='abcdefewe'),             # 只填充必填字段

            dict(name='abcd1', age=15),         # 测试各验证器是否正确处理下界值
            dict(name='abcde12345', age=20),    # 测试各验证器是否正确处理上界值

            dict(name=u'abc四五'),               # 测试各验证器是否正确处理中文
            dict(name=u'abc四五六'),
            dict(name=u'abc四五六七八九十'),
        ]
        for data in valid_data:
            self.db.session.add(self.Student(**data))
        self.db.session.commit()

        # 所有数据是否都成功写入
        instances = [i for i in self.Student.query]
        self.assertEqual(len(instances), len(valid_data))

        # 检查 trans_upper 是否正常工作
        for i, instance in zip(range(0, len(instances)-1), instances):
            self.assertEqual(instance.name, valid_data[i]['name'].upper())

        # ===== 能否正确处理非法值 =====

        invalid_data = [
            dict(name='abcd', age=15),         # 低于下界值
            dict(notes=u'abc四'),
            dict(name='abcde123456', age=21),  # 高于上界值
            dict(name=u'abc四五六七八九十A'),

            dict(name='xabc'),                  # not match
            dict(notes=u'你好'),
        ]
        for data in invalid_data:
            self.verify_exception(data)

    def test_custom_predicates(self):
        def trans_int(value):
            """给 value 加 1"""
            return dict(value=value + 1)

        def valid_int(value, arg):
            """检查 value 是不是 arg 的整倍数"""
            return value % arg == 0

        self.setup_model({
            'age': [trans_int, (valid_int, 4)]
        })

        # valid data
        self.Student(name='a', age=7)

        # invalid data
        self.verify_exception(dict(name='a', age=8))

    def test_rule_format(self):
        """各种格式的验证规则是否能被正常解析:
            一次性指定单个、多个字段；
            一次性指定单条，多条，有参数，无参数的验证规则；
            同一个字段在多个条目里被指定规则"""

        def trans_int(value):
            return dict(value=value * 2)

        self.setup_model({
            'name': [('min_length', 5)],
            ('name', 'notes'): [('max_length', 10)],
            'notes': [('trans_upper', )],

            'age': [trans_int]
        })

        # valid data
        self.db.session.add(self.Student(name='abcdefeg', notes='abcde', age=10))
        self.db.session.commit()

        instances = [i for i in self.Student.query]
        self.assertEqual(instances[0].notes, 'ABCDE')
        self.assertEqual(instances[0].age, 20)

        # invalid data
        invalid_data = [
            dict(name='012345678901'),
            dict(name='abcdee', notes='012345678901')
        ]
        for data in invalid_data:
            self.verify_exception(data)


class _ModelTestCase(MyTestCase):
    def setUp(self):
        self.setup_app()
        self.setup_model()

    def setup_model(self):
        time_now = datetime.now()
        timestamp = time.mktime(time_now.timetuple())
        float_default_value = 125.225
        bool_default_value = True

        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        self.db = SQLAlchemy(self.app)

        class TestModel(self.db.Model):
            id = Column(Integer, primary_key=True)

            col_int = Column(Integer, nullable=False)
            col_str = Column(String(100), nullable=False)
            col_float = Column(Float, nullable=False, default=float_default_value)
            col_bool = Column(Boolean, nullable=False, server_default=text(str(int(bool_default_value))))
            col_timestamp = Column(TIMESTAMP, nullable=False)

            col_int_null = Column(Integer)
            col_str_null = Column(String(100))
            col_float_null = Column(Float)
            col_bool_null = Column(Boolean)
            col_timestamp_null = Column(TIMESTAMP)

        self.TestModel = TestModel
        self.db.create_all()

        # ===== padding data =====

        self.data1 = dict(
            id=1,
            col_int=10, col_str="a", col_float=1.5, col_bool=True, col_timestamp=time_now,
            col_int_null=25, col_str_null=u"你好", col_float_null=0.001, col_bool_null=False,
            col_timestamp_null=time_now)
        self.result1 = self.data1.copy()
        self.result1['col_timestamp'] = self.result1['col_timestamp_null'] = timestamp

        # 通过只给 nullable=False 且没有默认值的字段赋值，可以测试 null 值以及字段默认值能否被正常处理
        self.data2 = dict(id=2,
                          col_int=10, col_str="a", col_timestamp=time_now)
        self.result2 = self.data2.copy()
        self.result2.update(dict(
            col_float=float_default_value,
            col_bool=bool_default_value,
            col_timestamp=timestamp,
            col_int_null=None, col_str_null=None, col_float_null=None, col_bool_null=None, col_timestamp_null=None,
        ))

        self.db.session.add(self.TestModel(**self.data1))
        self.db.session.add(self.TestModel(**self.data2))
        self.db.session.commit()

    class FixedRequestContext(object):
        def __init__(self, orig_context):
            self.context = orig_context

        def __enter__(self, *args, **kwargs):
            ret = self.context.__enter__(*args, **kwargs)
            request.unparsed_arguments = dict(Argument('').source(request))
            return ret

        def __exit__(self, *args, **kwargs):
            return self.context.__exit__(*args, **kwargs)

    def fixed_request_context(self, *args, **kwargs):
        return self.FixedRequestContext(self.app.test_request_context(*args, **kwargs))


class MarshalTestCase(_ModelTestCase):
    def setUp(self):
        super(MarshalTestCase, self).setUp()
        self.maxDiff = None

    def verify_marshal(self, model_data, expect_result, excludes=None, only=None, extends=None):
        @marshal_with_model(self.TestModel, excludes=excludes, only=only, extends=extends)
        def fn():
            return model_data

        expect_result = copy(expect_result)
        need_delete = []
        if excludes:
            need_delete = excludes
        elif only:
            need_delete = [k for k in expect_result.keys() if k not in only]
        for key in need_delete:
            del expect_result[key]

        self.assertEqual(fn(), expect_result)

    def test_normal_marshal(self):
        self.verify_marshal(self.TestModel.query.get(1), self.result1)
        self.verify_marshal(self.TestModel.query.get(2), self.result2)

    def test_query_marshal(self):
        self.verify_marshal(self.TestModel.query, [self.result1, self.result2])

    def test_excludes_and_only(self):
        self.verify_marshal(self.TestModel.query.get(1), self.result1, excludes=['id', 'col_int'])
        self.verify_marshal(self.TestModel.query.get(1), self.result1, only=['id', 'col_int'])
        self.verify_marshal(self.TestModel.query.get(1), self.result1,
                            excludes=['id', 'col_int'], only=['col_str_null'])

    def test_extends(self):
        extends = {
            # test extend column
            "extend_col": fields.String,
            # test overwrite exists column
            "col_int": fields.Boolean
        }

        data = deepcopy(self.TestModel.query.get(1))
        result = copy(self.result1)
        data.extend_col = result["extend_col"] = "abc"
        data.col_int = result["col_int"] = True

        self.verify_marshal(data, result, extends=extends)

    def test_quick_marshal(self):
        self.assertEqual(
            quick_marshal(self.TestModel)(self.TestModel.query.get(2)),
            self.result2
        )

    def test_converter(self):
        register_model_converter(self.TestModel, self.app)

        testcase = self

        class Routes(restful.Resource):
            def get(self, model):
                # test to_python
                testcase.assertEquals(model, testcase.TestModel.query.get(1))

                # test to_url
                testcase.assertEqual(
                    url_for('routes', model=testcase.TestModel.query.get(2)),
                    '/2'
                )

        api = restful.Api(self.app)
        api.add_resource(Routes, '/<TestModel:model>')
        self.client.get('/1')


class ReqparseTestCase(_ModelTestCase):
    def __init__(self, *args, **kwargs):
        super(ReqparseTestCase, self).__init__(*args, **kwargs)

    def test_fixed_type(self):
        # 测试类型转换
        time_str = '2013-12-21 14:19:05'
        d = fixed_datetime(time_str)
        self.assertTrue(isinstance(d, datetime))
        self.assertEqual(str(d), time_str)

        self.assertEqual(fixed_int(987), 987)
        self.assertEqual(fixed_int("850"), 850)
        self.assertIsNone(fixed_int(""))
        self.assertIsNone(fixed_int(u""))

        self.assertEqual(fixed_float(987.5), 987.5)
        self.assertEqual(fixed_float("850.3"), 850.3)
        self.assertIsNone(fixed_float(""))
        self.assertIsNone(fixed_float(u""))

        # 测试实际调用时能否正确运行
        with self.fixed_request_context(
                method='POST',
                data='{"n1": 100, "n2": "100", "n3": "", "n4": null}',
                content_type="application/json"):
            self.assertEqual(Argument('n1', type=fixed_int).parse(request)[0], 100)
            self.assertEqual(Argument('n2', type=fixed_int).parse(request)[0], 100)
            self.assertEqual(Argument('n3', type=fixed_int).parse(request)[0], None)
            self.assertEqual(Argument('n4', type=fixed_int).parse(request)[0], None)

    def test_populator_argument(self):
        # 测试 JSON 下的情况
        with self.fixed_request_context(
                method='POST',
                data='{"foo": 100, "bar": "abc", "li": [300, 100, 200]}',
                content_type="application/json"):

            # 确认能否成功取到参数值
            # 因为内部实现中涉及到了 Argument 的 action 属性，同时也要确认一下有没有造成不良影响

            # 1. 默认为 action=store，总是只返回此参数的第一个值
            self.assertEqual(
                PopulatorArgument('foo', type=int).parse(request),
                100)
            self.assertEqual(
                PopulatorArgument('bar').parse(request),
                u'abc')
            self.assertEqual(
                PopulatorArgument('li', type=int).parse(request),
                300)

            # 2. action=append 的情况下，总是返回此参数的值列表
            self.assertEqual(
                PopulatorArgument('bar', action='append').parse(request),
                [u'abc'])
            self.assertEqual(
                PopulatorArgument('li', type=int, action='append').parse(request),
                [300, 100, 200])

            # 3. 在 action 是其他值得情况下，若值数量为1，返回此值；否则返回值列表
            self.assertEqual(
                PopulatorArgument('foo', type=int, action='something').parse(request),
                100)
            self.assertEqual(
                PopulatorArgument('bar', action='something').parse(request),
                u'abc')
            self.assertEqual(
                PopulatorArgument('li', type=int, action='something').parse(request),
                [300, 100, 200])

            # 确认在未给出参数值的情况下，是否会按照预期抛出异常
            with self.assertRaises(ArgumentNoValue):
                PopulatorArgument('no_val_arg').parse(request)

        # 测试 QueryString / FormData 下的情况
        with self.fixed_request_context('/?foo=100&bar=abc&li=300&li=100&li=200', method='GET'):
            # 确认能否成功取到参数值
            # 因为内部实现中涉及到了 Argument 的 action 属性，同时也要确认一下有没有造成不良影响

            # 1. 默认为 action=store，总是只返回此参数的第一个值
            self.assertEqual(
                PopulatorArgument('foo', type=int).parse(request),
                100)
            self.assertEqual(
                PopulatorArgument('bar').parse(request),
                u'abc')
            self.assertEqual(
                PopulatorArgument('li', type=int).parse(request),
                300)

            # 2. action=append 的情况下，总是返回此参数的值列表
            self.assertListEqual(
                PopulatorArgument('foo', type=int, action='append').parse(request),
                [100]
            )
            self.assertListEqual(
                PopulatorArgument('li', type=int, action='append').parse(request),
                [300, 100, 200]
            )
            # 3. 在 action 是其他值得情况下，若值数量为1，返回此值；否则返回值列表
            self.assertEqual(
                PopulatorArgument('foo', type=int, action='something').parse(request),
                100
            )
            self.assertListEqual(
                PopulatorArgument('li', type=int, action='something').parse(request),
                [300, 100, 200]
            )

    def test_request_populator(self):
        with self.fixed_request_context(
                method='POST',
                data='{"foo": 100, "bar": "abc"}',
                content_type="application/json"):
            parser = RequestPopulator()
            parser.add_argument(name='foo', type=int)
            parser.add_argument(name='bar')
            # 此参数不应出现在最终获得的参数列表里，因为没有给它赋值
            parser.add_argument(name='xyz', type=int)
            self.assertEqual(
                parser.parse_args(),
                dict(foo=100, bar="abc"))

    def test_make_request_parser(self):
        # for model
        self._test_make_request_parser(self.TestModel, True)

        # for instance
        self._test_make_request_parser(self.TestModel(), False)

    def _test_make_request_parser(self, model_or_inst, is_model):
        # 创建一个临时的 parser，提取其 args
        common_args = make_request_parser(model_or_inst).args

        # parser args 数量应该比 model col 数量少1，因为主键被排除了
        self.assertEqual(
            len(common_args),
            len(model_or_inst.__mapper__.columns) - 1)

        # 检查是否正确的把 arg type 设置成了 model col type 的 fixed 版本
        expect_types = [
            # arg index, type
            (0, fixed_int),
            (1, six.text_type),
            (2, fixed_float),
            (4, fixed_datetime)
        ]
        for col_index, expect_type in expect_types:
            self.assertEqual(common_args[col_index].type, expect_type)

        # 若给出的是 model，则没有默认值且不允许 NULL 值的字段所对应的 arg 应设为 required
        # 若给出的是 instance，则所有字段都不是 required
        required_arg_index = [0, 1, 4]
        for arg, i in zip(common_args, range(len(common_args))):
            self.assertEqual(arg.required, is_model and i in required_arg_index)

        # 测试 excludes 和 only 参数
        def verify_args(args, remain):
            self.assertEqual(len(args), len(remain))
            for arg, expect_name in zip(args, remain):
                self.assertEqual(arg.name, expect_name)

        # 1. excludes
        excludes = ['col_str', 'col_bool', 'col_int_null', 'col_timestamp_null']
        exclude_remain = ['col_int', 'col_float', 'col_timestamp', 'col_str_null', 'col_float_null', 'col_bool_null']
        verify_args(
            make_request_parser(model_or_inst, excludes=excludes).args,
            exclude_remain)
        # 测试把字符串当做参数值时能否正确处理
        verify_args(
            make_request_parser(model_or_inst, excludes='col_int_null').args,
            ['col_int', 'col_str', 'col_float', 'col_bool', 'col_timestamp',
             'col_str_null', 'col_float_null', 'col_bool_null', 'col_timestamp_null', ])

        # 2. only
        only = [
            'id',  # 测试主键是否能成功进行“强制添加”
            'col_bool', 'col_str_null'
        ]
        verify_args(
            make_request_parser(model_or_inst, only=only).args,
            only)
        # 测试把字符串当做参数值时能否正确处理
        verify_args(
            make_request_parser(model_or_inst, only='col_int_null').args,
            ['col_int_null'])

        # 3. 测试 excludes 和 only 都给出的情况下，是否只有 excludes 生效
        verify_args(
            make_request_parser(model_or_inst, excludes=excludes, only=only).args,
            exclude_remain)

    def test_populate_model(self):
        data = {
            'col_int': 2,
            'col_float': 10.5,
            'col_bool_null': True,
        }

        with self.fixed_request_context(
                method='POST',
                data=json.dumps(data),
                content_type="application/json"):
            # model
            entity = populate_model(self.TestModel, only=[col for col, val in data.items()])
            for col in entity.__mapper__.columns:
                self.assertEqual(
                    getattr(entity, col.name),
                    data.get(col.name, None)
                )

            # inst
            entity = self.TestModel()
            populate_model(entity, only=[col for col, val in data.items()])
            for col in entity.__mapper__.columns:
                self.assertEqual(
                    getattr(entity, col.name),
                    data.get(col.name, None)
                )
