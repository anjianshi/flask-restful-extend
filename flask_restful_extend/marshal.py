# -*- coding: utf-8 -*-
from flask.ext.restful import fields as _fields, marshal_with as _marshal_with
from functools import wraps
import time


def _wrap_field(field):
    """对原始的 field 格式化函数进行包裹，以优化其行为"""
    class WrappedField(field):
        def output(self, key, obj):
            value = _fields.get_value(key if self.attribute is None else self.attribute, obj)

            # 对于所有字段，碰到 null(None) 值时，都直接返回 null，而不是返回一个默认值（如： int => 0）
            # 若不这样做，客户端没法确定一个字段（例如值为 0 的 int 字段）到底是赋的值就是0还是没赋值
            return None if value is None else self.format(value)
    return WrappedField


class _DateTimeField(_fields.Raw):
    """碰到 datetime 值时，将其转换为 timestamp 再返回"""
    def format(self, value):
        try:
            return time.mktime(value.timetuple())
        except AttributeError as ae:
            raise _fields.MarshallingException(ae)


class _FloatField(_fields.Raw):
    """Flask-RESTful 对于 float 默认会将其转换成字符串再返回。这样可以就用一些类似科学计数法的方式表达特殊的小数。
    但这个行为在大部分情况下没有意义，还使得客户端必须进行一次类型转换。
    因此，把此行为改成直接返回 float"""
    def format(self, value):
        try:
            return float(value)
        except ValueError as ve:
            raise _fields.MarshallingException(ve)


_type_map = {
    # python_type: flask-restful field
    'str': _wrap_field(_fields.String),
    'int': _wrap_field(_fields.Integer),
    'float': _wrap_field(_FloatField),
    'bool': _wrap_field(_fields.Boolean),
    'datetime': _wrap_field(_DateTimeField)
}


def marshal_with_model(model, excludes=[]):
    """
      todo: 支持 KeyedTuple

      让视图函数能够更方便地返回 ORM model 对象（仅针对 flask-sqlalchemy）
      1. 把 model 中的 column 转换成 flask-restful 能识别的 fields
         可通过 `excludes` 参数指定要排除的 column
      2. 如果视图函数返回的是 query 对象（而不是单个的 model 对象），则把它转化成 list

      例子：
      model：
      Student
        id int
        name string
        age int

      class SomeApi(Resource):
        @marshal_with_model(Student, excludes=['id'])
        def get(self):
          return Student.query

      客户端接收到的返回值：
      [{"name": "student_a", "age": "16"}, {"name": "student_b", "age": 18}]
    """
    field_definition = {}
    for col in model.__table__.columns:
        if col.name not in excludes:
            field_definition[col.name] = _type_map[col.type.python_type.__name__]

    def decorated(f):
        @wraps(f)
        @_marshal_with(field_definition)
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)
            return result if not _fields.is_indexable_but_not_string(result) else [v for v in result]
        return wrapper
    return decorated