# -*- coding: utf-8 -*-
from flask.ext.restful import reqparse
from datetime import datetime
from flask import request
import six


def _is_inst(model_or_inst):
    return hasattr(model_or_inst, '_sa_instance_state')


_type_dict = {
    "datetime": lambda time_str: datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S'),
    "str": unicode,
    "float": lambda value: None if isinstance(value, (str, unicode)) and len(value) == 0 else float(value),
    "int": lambda value: None if isinstance(value, (str, unicode)) and len(value) == 0 else int(value)
}


class _ExtendedArgument(reqparse.Argument):
    def parse(self, request, source=None):
        # todo: 用更好的方法，代替把原函数照搬复制过来然后中间插入代码的行为。因为这样做，原函数的代码被更新时，这里的代码不会跟着更新。

        # === custom ===
        # 提升性能。 req parser 为了确认某个参数是否存在于请求中，需要调用此参数的 source() 方法。
        # 而此参数的 parse() 方法在解析参数值时还要再调用一次 source() 这就导致性能下降。
        # 因此，把执行机制改成：req parser 在调用参数的 parse() 方法时，把刚才已经提取好的 source 传给它， parse() 方法就不用在调用一次 source() 了。

        if source is None:
            source = self.source(request)
        # === end ===

        results = []

        for operator in self.operators:
            name = self.name + operator.replace("=", "", 1)
            if name in source:
                # Account for MultiDict and regular dict
                if hasattr(source, "getlist"):
                    values = source.getlist(name)
                else:
                    values = [source.get(name)]

                for value in values:
                    # === custom ===
                    # 若传入的是 null (None)，不对其进行格式化，以避免报错
                    # 最终，其值会被设为 self.default (默认是 None)
                    if value is None:
                        continue
                    # === end ===

                    if not self.case_sensitive:
                        value = value.lower()
                    if self.choices and value not in self.choices:
                        self.handle_validation_error(ValueError(
                            u"{0} is not a valid choice".format(value)))
                    try:
                        value = self.convert(value, operator)
                    except Exception as error:
                        if self.ignore:
                            continue

                        self.handle_validation_error(error)

                    results.append(value)

        if not results and self.required:
            if isinstance(self.location, six.string_types):
                error_msg = u"{0} is required in {1}".format(
                    self.name,
                    self.location
                )
            else:
                error_msg = u"{0} is required in {1}".format(
                    self.name,
                    ' or '.join(self.location)
                )
            self.handle_validation_error(ValueError(error_msg))

        if not results:
            return self.default

        if self.action == 'append':
            return results

        if self.action == 'store' or len(results) == 1:
            return results[0]
        return results


class RequestParser(reqparse.RequestParser):
    def __init__(self, namespace_class=reqparse.Namespace):
        super(RequestParser, self).__init__(_ExtendedArgument, namespace_class)

    def add_argument(self, *args, **kwargs):
        # 对常见的类型进行封装，使其拥有正确的行为
        arg_type = kwargs.pop('type', None)
        if arg_type is not None:
            kwargs['type'] = _type_dict.get(arg_type.__name__, arg_type) if hasattr(arg_type, '__name__') else arg_type

        return super(RequestParser, self).add_argument(*args, **kwargs)

    def parse_args(self, req=None, for_populate=False):
        """Parse all arguments from the provided request and return the results
        as a Namespace
        """
        if req is None:
            req = request

        namespace = self.namespace_class()

        for arg in self.args:
            # === custom ===
            # 在原来的流程下，一个参数无论是用户没提交，还是提交了 null 值，在解析出来的参数列表里都会把它的值设为 None
            # 这在一般情况下没问题，但在 populate 模式下（用于填充 model instance）会出错。
            # 在 populate 模式下，若用户没提交此参数，应忽略它。
            # 只有用户确实提交了 null 时，才把 instance 的对应字段设为 None
            #
            # 因此，现在在 req parser 中，添加了一个 for_populate 参数。
            # 在 for_populate 为 True 的情况下，未出现的参数压根不会让它出现在解析出来的参数列表里。
            # 而 null 值参数就会将参数值设为 None，使得其最终能够被写入数据库。
            #
            # P.S.
            # 若通过 QueryString 或 FormData 方式提交参数值，则解析结果只有可能是字符串值
            # （包括 url?a= ，这里 a 的值是空字符串）
            # 只有通过 JSON 提交，才有可能指定 null 值
            arg_source = arg.source(req)
            if len(arg_source) == 0 and for_populate:
                continue
            else:
                value = arg.parse(req, arg_source)
                namespace[arg.dest or arg.name] = value
            # === end ===

        return namespace


def make_request_parser(model_or_inst, excludes=None, only=None):
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

    parser = RequestParser()
    for col in model_or_inst.__table__.columns:
        if only:
            if col.name not in only:
                continue
        elif (excludes and col.name in excludes) or col.primary_key:
                continue

        kwargs = {"type": col.type.python_type}
        if not is_inst and not col.nullable:
            kwargs["required"] = True
        parser.add_argument(col.name, **kwargs)
    return parser


def populate_model(model_or_inst, excludes=None, only=None):
    """
    调用 make_request_parser() 构建一个 RequestParser 并用它提取用户输入，填充到指定的 model_inst 中。
    (若传入的是 model 类，会创建一个它的实例，并将其作为 model_inst)
    """
    model_inst = model_or_inst if _is_inst(model_or_inst) else model_or_inst()

    parser = make_request_parser(model_or_inst, excludes, only)
    req_args = parser.parse_args(for_populate=True)

    for key, value in req_args.iteritems():
        setattr(model_inst, key, value)

    return model_inst