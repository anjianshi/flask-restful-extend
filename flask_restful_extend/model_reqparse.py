# -*- coding: utf-8 -*-
__all__ = ['fix_argument_convert', 'make_request_parser', 'populate_model']
from flask.ext.restful import reqparse
from flask import request
from . import reqparse_fixed_type as fixed_type
import inspect
import six


_type_dict = {
    # python_type_name: fixed_type
    'datetime': fixed_type.fixed_datetime,
    'date': fixed_type.fixed_date,
    'str': fixed_type.fixed_str,
    'int': fixed_type.fixed_int,
    'float': fixed_type.fixed_float,
    'bool': fixed_type.fixed_bool
}


def fix_argument_convert():
    """Change `reqparse.Argument.convert`'s original behavior.

    No special handle None value for `string_types`
    (Notice: After this, if you pass None value to a `str Argument`, you will got a string 'None',
             rather then raise an exception as in other types)
    """
    orig_convert = reqparse.Argument.convert

    def _convert(self, value, op):
        if value is None and inspect.isclass(self.type) and issubclass(self.type, six.string_types):
            return 'None'
        else:
            return orig_convert(self, value, op)
    reqparse.Argument.convert = _convert


def make_request_parser(model_or_inst, excludes=None, only=None, for_populate=False):
    """Pass a `model class` or `model instance` to this function,
     then, it will generate a `RequestParser` that extract user request data from `request.json`
     according to the model class's definition.

    Parameter `excludes` and `only` can be `str` or list of `str`,
     then are used to specify which columns should be handled.
    If you passed `excludes` and `only` at same time, only `excludes` will be used.
    And, the primary key of the model will not be added to `RequestParser`'s argument list,
     unless you explicitly specify it use `only` parameter.

    If you pass in a model class, but not a model instance, the function will doing `required` checking,
     for columns that nullable=False.
    (If you pass in a model instance, the `required` checking will not proceed. Because in this situation,
     we should allow the user to ignore the assignment to a field)
    """
    is_inst = _is_inst(model_or_inst)

    if isinstance(excludes, six.string_types):
        excludes = [excludes]
    if excludes and only:
        only = None
    elif isinstance(only, six.string_types):
        only = [only]

    parser = RequestPopulator() if for_populate else reqparse.RequestParser()
    for col in model_or_inst.__table__.columns:
        if only:
            if col.name not in only:
                continue
        elif (excludes and col.name in excludes) or col.primary_key:
                continue

        col_type = col.type.python_type
        kwargs = {
            "type": _type_dict.get(col_type.__name__, col_type) if hasattr(col_type, '__name__') else col_type
        }
        # When the context was to creating a new model instance, if a field has no default value, and is not nullable,
        #  mark it's corresponding argument as `required`.
        # 创建新数据库实例时，若一个字段既没有默认值，又不允许 NULL，则把它对应 arg 设为 required
        if not is_inst and col.default is None and col.server_default is None and not col.nullable:
            kwargs["required"] = True
        parser.add_argument(col.name, **kwargs)
    return parser


def populate_model(model_or_inst, excludes=None, only=None):
    """
    Call `make_request_parser()` to build a `RequestParser`, use it extract user request data,
      and padding the data into model instance.
    If user passed a model class, instead of model instance, create a new instance use the extracted data.
    """
    inst = model_or_inst if _is_inst(model_or_inst) else model_or_inst()

    parser = make_request_parser(model_or_inst, excludes, only, for_populate=True)
    req_args = parser.parse_args()

    for key, value in req_args.items():
        setattr(inst, key, value)

    return inst


def _is_inst(model_or_inst):
    return hasattr(model_or_inst, '_sa_instance_state')


class RequestPopulator(reqparse.RequestParser):
    """Under the original process, whether client hasn't assign a value, or assign a null value,
     the argument's value will be None.
    That's no problem, generally. But in populate operation (eg. updating model instance's fields),
     it will cause problem.
    When we are do populating, we should not update the field if the client hasn't assign a value to it.
    And update it only if the client really assign a new value.

    The `RequestPopulator` parser is created specifically for the populate operation.
    In this parser, arguments that has not assigned a value,
     will not appear in argument list (implemented through `PopulatorArgument`).
    So the model fields corresponding to these arguments can keep its original value.
    """
    def __init__(self, *args, **kwargs):
        kwargs['argument_class'] = PopulatorArgument
        super(RequestPopulator, self).__init__(*args, **kwargs)

    def parse_args(self, req=None):
        if req is None:
            req = request

        namespace = self.namespace_class()

        for arg in self.args:
            try:
                value = arg.parse(req)
                namespace[arg.dest or arg.name] = value
            except ArgumentNoValue:
                pass

        return namespace


class PopulatorArgument(reqparse.Argument):
    """Argument type that created specifically for populate operation.
    When the argument is not assigned, it will raise an exception rather than applying default value.
    (So, the `default` parameter will not be used)

    **关于值类型**
    （`arg` 指 Argument 实例，`参数` 指构建 arg 时给出的参数）
    以 QueryString / FormData 形式提交的请求，每个 arg 的值在格式化之前都只能是字符串或空字符串。
    对于 action != store 的 arg，可以指定多个值（?a=1&a=2），通过 type 指定的类型会分别应用到每个值上

    以 JSON 形式提交的请求，arg 的值在格式化之前就可以是除数组外任意类型，
    如果 arg 的值是一个数组， Flask-RESTFul 会视为对这个参数进行了多次赋值，并将 type 指定的类型会分别应用到每个值上
    例如 json 的 {"a": ["x", "y"]} 相当于 QueryString 的 ?a=x&a=y

    **关于值解析**
    解析前端提交的参数值时，不会对参数值有任何额外的处理（如预先进行一次类型转换），或者额外的行为（如碰到 None 就调用构造器调用），
    一定是直接把它传给参数的构造器。
    因此，只要参数的构造器本身不支持处理给定的值，就好报 400 错误。（例如：int 构造器既不支持空字符串，也不支持 None，那么碰到它们就会报错）
    这样做可以避免歧义，例如 int 本身不支持空字符串，如果特意为了它把空字符串转成 None 或者 0，会使不了解内情的人误解，或者与他们预期的行为不符。
    当然，可以通过自定义一个构造器来进行额外的处理，因为它明摆着是做了额外处理的，所以不会有误解的问题。
    P.S. flask-restful 在碰到 text 参数且值为 None 时，会返回 None，
         这个行为不符合上面的规则，可调用 fix_argument_convert() 修复它
    """
    def __init__(self, *args, **kwargs):
        # 把 action 强制设定为 append，以便解析参数值的时候判断此参数有没有被赋值
        # 记录原来的 action 是为了在最后仍能以用户期望的格式返回参数值
        self.real_action = kwargs.get('action', 'store')
        kwargs['action'] = 'append'

        super(PopulatorArgument, self).__init__(*args, **kwargs)

    def parse(self, req):
        results = super(PopulatorArgument, self).parse(req)[0]

        # 因为把 action 强制设定为了 append，因此在提交了参数值的情况下，results 一定是一个数组，
        # 不会和 self.default 是同一个值
        # （即使 self.default 也是数组，也不会和 results 是同一个数组）
        # 因此就可以通过这一点来判断当前请求中，到底有没有提交此参数的值
        if results is self.default:
            raise ArgumentNoValue()
        elif self.real_action == 'store' or (self.real_action != 'append' and len(results) == 1):
            return results[0]
        else:
            return results


class ArgumentNoValue(Exception):
    pass
