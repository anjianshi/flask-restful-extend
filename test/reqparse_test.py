# -*- coding: utf-8 -*-
import unittest
from project import app
from flask_restful_extend.model_reqparse import fix_argument_convert, make_request_parser, populate_model, RequestPopulator, PopulatorArgument, ArgumentNoValue
from flask_restful_extend.reqparse_fixed_type import *
from flask.ext.restful.reqparse import Argument
from model_model import *
from pprint import pprint
from flask import request, json


fix_argument_convert()


class ReqParseTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def test_fix_argument_convert(self):
        with app.test_request_context(
                method='POST',
                data='{"foo": null}',
                content_type="application/json"):
            # 测试对 None 值的处理
            self.assertEqual(Argument('foo').parse(request), 'None')

            # 测试 type 参数是函数，且 arg value is None 时会不会报错
            self.assertEqual(
                Argument('foo', type=lambda v: 'haha').parse(request),
                'haha'
            )

    def test_fixed_type(self):
        # 测试类型转换
        time_str = '2013-12-21 14:19:05'
        d = fixed_datetime(time_str)
        self.assertTrue(isinstance(d, datetime))
        self.assertEqual(str(d), time_str)

        orig_str = 'abc'
        new_str = fixed_str(orig_str)
        self.assertTrue(isinstance(new_str, unicode))
        self.assertEqual(new_str, unicode(orig_str))

        self.assertEqual(fixed_int(987), 987)
        self.assertEqual(fixed_int("850"), 850)
        self.assertIsNone(fixed_int(""))
        self.assertIsNone(fixed_int(u""))

        self.assertEqual(fixed_float(987.5), 987.5)
        self.assertEqual(fixed_float("850.3"), 850.3)
        self.assertIsNone(fixed_float(""))
        self.assertIsNone(fixed_float(u""))

        self.assertEqual(fixed_bool(True), True)

        # 测试 None 值处理
        for fixed_type in [fixed_datetime, fixed_str, fixed_int, fixed_float, fixed_bool]:
            self.assertIsNone(fixed_type(None))

        # 测试实际调用时能否正确运行
        with app.test_request_context(
                method='POST',
                data='{"n1": 100, "n2": "100", "n3": "", "n4": null}',
                content_type="application/json"):
            self.assertEqual(Argument('n1', type=fixed_int).parse(request), 100)
            self.assertEqual(Argument('n2', type=fixed_int).parse(request), 100)
            self.assertEqual(Argument('n3', type=fixed_int).parse(request), None)
            self.assertEqual(Argument('n4', type=fixed_int).parse(request), None)

    def test_populator_argument(self):
        # 测试 JSON 下的情况
        with app.test_request_context(
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
                PopulatorArgument('li', type=list).parse(request),
                [300, 100, 200])

            # 2. action=append 的情况下，总是返回此参数的值列表
            self.assertEqual(
                PopulatorArgument('bar', action='append').parse(request),
                [u'abc'])
            self.assertEqual(
                PopulatorArgument('li', type=list, action='append').parse(request),
                [[300, 100, 200]])

            # 3. 在 action 是其他值得情况下，若值数量为1，返回此值；否则返回值列表
            # 因为对于 JSON 类型的请求来说，一个参数永远只能有一个值，因此这种情况下返回的一定也永远都是值本身，而不是值列表
            self.assertEqual(
                PopulatorArgument('foo', type=int, action='something').parse(request),
                100)
            self.assertEqual(
                PopulatorArgument('bar', action='something').parse(request),
                u'abc')
            self.assertEqual(
                PopulatorArgument('li', type=list, action='something').parse(request),
                [300, 100, 200])

            # 确认在未给出参数值的情况下，是否会按照预期抛出异常
            with self.assertRaises(ArgumentNoValue):
                PopulatorArgument('no_val_arg').parse(request)

        # 测试 QueryString / FormData 下的情况
        with app.test_request_context('/?foo=100&bar=abc&li=300&li=100&li=200', method='GET'):
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
        with app.test_request_context(
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
        self._test_make_request_parser(Entity, True)

        # for instance
        self._test_make_request_parser(Entity(), False)

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
            (1, fixed_int),
            (2, fixed_str),
            (4, fixed_float),
            (7, fixed_bool),
            (8, fixed_datetime)
        ]
        for col_index, expect_type in expect_types:
            self.assertEqual(common_args[col_index].type, expect_type)

        # 若给出的是 model，则没有默认值且不允许 NULL 值的字段所对应的 arg 应设为 required
        # 若给出的是 instance，则所有字段都不是 required
        required_arg_index = [0, 2, 4]
        for arg, i in zip(common_args, range(len(common_args))):
            self.assertEqual(arg.required, is_model and i in required_arg_index)

        # 测试 excludes 和 only 参数
        def verify_args(args, remain):
            self.assertEqual(len(args), len(remain))
            for arg, expect_name in zip(args, remain):
                self.assertEqual(arg.name, expect_name)

        # 1. excludes
        excludes = ['cint_n', 'cstr', 'cbl', 'cts_n']
        exclude_remain = ['parent_id', 'cstr_n', 'cfl', 'cfl_n', 'cbl_n', 'cts']
        verify_args(
            make_request_parser(model_or_inst, excludes=excludes).args,
            exclude_remain)

        # 2. only
        only = [
            'id',  # 测试主键是否能成功进行“强制添加”
            'cstr_n', 'cbl'
        ]
        verify_args(
            make_request_parser(model_or_inst, only=only).args,
            only)

        # 3. 测试 excludes 和 only 都给出的情况下，是否只有 excludes 生效
        verify_args(
            make_request_parser(model_or_inst, excludes=excludes, only=only).args,
            exclude_remain)

    def test_populate_model(self):
        data = {
            'parent_id': 2,
            'cbl_n': True,
            'cfl': 10.5
        }

        with app.test_request_context(
                method='POST',
                data=json.dumps(data),
                content_type="application/json"):

            # model
            entity = populate_model(Entity, only=[col for col, val in data.iteritems()])
            for col in entity.__mapper__.columns:
                self.assertEqual(
                    getattr(entity, col.name),
                    data.get(col.name, None)
                )

            # inst
            entity = Entity()
            populate_model(entity, only=[col for col, val in data.iteritems()])
            for col in entity.__mapper__.columns:
                self.assertEqual(
                    getattr(entity, col.name),
                    data.get(col.name, None)
                )