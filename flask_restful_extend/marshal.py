# -*- coding: utf-8 -*-
from flask.ext.restful import fields as _fields, marshal_with as _marshal_with
from functools import wraps
import time


def _wrap_field(field):
    class WrappedField(field):
        def format(self, value):
            return None if value is None else super(WrappedField, self).format(value)

        def output(self, key, obj):
            value = _fields.get_value(key if self.attribute is None else self.attribute, obj)
            return None if value is None else self.format(value)
    return WrappedField


class _DateTimeField(_fields.Raw):
    """Return a timestamp"""

    def format(self, value):
        try:
            return time.mktime(value.timetuple())
        except AttributeError as ae:
            raise _fields.MarshallingException(ae)


class _FloatField(_fields.Raw):
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
      todo: support KeyedTuple

      help view methods return orm model object more easily (only face to flask-sqlalchemy)
      1. transform columns in model to fields that flask-restful can understand.
         use the 'excludes' argument, you can specify columns shouldn't appear in return value
      2. when you return query object directly, auto transform it to list

      example：
      model：
      Student
        id int
        name string
        age int

      class SomeApi(Resource):
        @marshal_with_model(Student, excludes=['id'])
        def get(self):
          return Student.query

      return value to client：
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