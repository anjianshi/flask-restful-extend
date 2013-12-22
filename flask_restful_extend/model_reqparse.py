# -*- coding: utf-8 -*-
__all__ = ['make_request_parser', 'po']
from flask.ext.restful import reqparse
from flask import request
import reqparse_fixed_type as fixed_type

_type_dict = {
    # python_type_name: fixed_type
    'datetime': fixed_type.fixed_datetime,
    'str': fixed_type.fixed_str,
    'int': fixed_type.fixed_int,
    'float': fixed_type.fixed_float,
    'bool': fixed_type.fixed_bool
}


def make_request_parser(model_or_inst, excludes=None, only=None, for_populate=False):
    """
    传入一个 model 类(model)或者 model 实例(model_inst)
    根据对应的 model 的定义，构建一个从 request.json 中提取用户输入的 RequestParser。

    excludes 和 only 用于控制哪些 column 应该被处理。若同时传入 excludes 和 only，只有 excludes 会生效。
    model 的主键默认不会被添加到 RequestParser 的 args 列表里。
    可通过在 only 中指定这个主键，强制把它添加进去。

    若传入的是 model 类，还会根据 model column 的 nullable 属性，对用户传入的参数添加 required 检查
    (若传入的是 model_inst，则不会进行此项检查。因为这种情况下，应该允许用户忽略对某个字段的赋值)
    """
    is_inst = _is_inst(model_or_inst)

    if isinstance(excludes, str) or isinstance(excludes, unicode):
        excludes = [excludes]
    if excludes and only:
        only = None
    elif isinstance(only, str) or isinstance(only, unicode):
        excludes = [excludes]

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
        if not is_inst and not col.nullable:
            kwargs["required"] = True
        parser.add_argument(col.name, **kwargs)
    return parser


def populate_model(model_or_inst, excludes=None, only=None):
    """
    调用 make_request_parser() 构建一个 RequestParser 并用它提取用户输入，填充到指定的 model_inst 中。
    (若传入的是 model 类，会创建一个它的实例，并将其作为 model_inst)
    """
    inst = model_or_inst if _is_inst(model_or_inst) else model_or_inst()

    parser = make_request_parser(model_or_inst, excludes, only, for_populate=True)
    req_args = parser.parse_args()

    for key, value in req_args.iteritems():
        setattr(inst, key, value)

    return inst


def _is_inst(model_or_inst):
    return hasattr(model_or_inst, '_sa_instance_state')


class RequestPopulator(reqparse.RequestParser):
    """在原来的流程下，一个参数无论是用户没提交，还是提交了 null 值，在解析出来的参数列表里都会把它的值设为 None
    这在一般情况下没问题，但在 populate 模式下（用于填充 model instance）会出错。
    在 populate 模式下，若用户没提交此参数，应忽略它。
    只有用户确实提交了 null 时，才把 instance 的对应字段设为 None

    因此，对于这个专为 populate 创建的 parser ，未出现的参数压根不会让它出现在解析出来的参数列表里。
    而 null 值参数就会将参数值设为 None，使得其最终能够被写入数据库。
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
    """为 populate 操作定制的 Argument 类。
    当参数未赋值时，会抛出异常而不是应用默认值。因此，default 参数在这里无效"""
    def __init__(self, *args, **kwargs):
        # 把 action 强制设定为 append，以便解析参数值的时候判断此参数有没有被赋值
        # 记录原来的 action 是为了在最后仍能以用户期望的格式返回参数值
        self.real_action = kwargs.get('action', 'store')
        kwargs['action'] = 'append'

        super(PopulatorArgument, self).__init__(*args, **kwargs)

    def parse(self, req):
        results = super(PopulatorArgument, self).parse(req)

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