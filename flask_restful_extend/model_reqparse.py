# -*- coding: utf-8 -*-
__all__ = ['make_request_parser', 'po']
from flask.ext.restful import reqparse
from flask import request
import reqparse_fixed_type as fixed_type


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
    """修改 reqparse.Argument.convert 的默认行为

    不再为 string_types 特别处理 None 值
    （注意，这种情况下，把 None 传给 str Argument 会得到 'None'，而不是像其他类型那样抛出一个错误）

    顺带解决了把`函数`（而不是`类`）作为 Argument 的 type 参数时，
    一旦 arg value is None，就会因为 issubclass() 调用而抛出异常的问题
    """
    def _convert(self, value, op):
        try:
            return self.type(value, self.name, op)
        except TypeError:
            try:
                return self.type(value, self.name)
            except TypeError:
                return self.type(value)
    reqparse.Argument.convert = _convert


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
        # 创建新数据库实例时，若一个字段既没有默认值，又不允许 NULL，则把它对应 arg 设为 required
        if not is_inst and col.default is None and col.server_default is None and not col.nullable:
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
    当参数未赋值时，会抛出异常而不是应用默认值。因此，default 参数在这里无效

    **关于值类型**
    （`arg` 指 Argument 实例，`参数` 指构建 arg 时给出的参数）
    以 QueryString / FormData 形式提交的请求，每个 arg 的值在格式化之前都只能是字符串或空字符串。
    对于 action != store 的 arg，可以指定多个值（?a=1&a=2），通过 type 指定的类型会分别应用到每个值上

    以 JSON 形式提交的请求，arg 的值在格式化之前就可以是任意类型，但不支持给单个 arg 指定多个值（因此，action 参数不起作用）
    虽然可以把参数值设为数组来达到同样的效果，但这需要把 type 指定为 list，也就无法再给列表内部的值指定类型了。

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