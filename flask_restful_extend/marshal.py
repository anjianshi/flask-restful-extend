# -*- coding: utf-8 -*-
from flask.ext.restful import fields as _fields, marshal_with as _marshal_with
from functools import wraps
import time


def marshal_with_model(model, excludes=None, only=None):
    """With this decorator, you can return ORM model instance, or ORM query in view function directly.
    We'll transform these objects to standard python data structures, like Flask-RESTFul's `marshal_with` decorator.
    And, you don't need define fields at all.

    You can specific columns to be returned, by `excludes` or `only` parameter.
    (Don't use these tow parameters at the same time, otherwise only `excludes` parameter will be used.)

    Notice: this function only support `Flask-SQLAlchemy`

    Example:
        class Student(db.Model):
            id = Column(Integer, primary_key=True)
            name = Column(String(100))
            age = Column(Integer)

        class SomeApi(Resource):
            @marshal_with_model(Student, excludes=['id'])
            def get(self):
              return Student.query

        # response: [{"name": "student_a", "age": "16"}, {"name": "student_b", "age": 18}]
    """
    if isinstance(excludes, str) or isinstance(excludes, unicode):
        excludes = [excludes]
    if excludes and only:
        only = None
    elif isinstance(only, str) or isinstance(only, unicode):
        only = [only]

    field_definition = {}
    for col in model.__table__.columns:
        if only:
            if col.name not in only:
                continue
        elif excludes and col.name in excludes:
                continue

        field_definition[col.name] = _type_map[col.type.python_type.__name__]

    def decorated(f):
        @wraps(f)
        @_marshal_with(field_definition)
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)
            return result if not _fields.is_indexable_but_not_string(result) else [v for v in result]
        return wrapper
    return decorated


def quick_marshal(*args, **kwargs):
    """In some case, one view functions may return different model in different situation.
    Use `marshal_with_model` to handle this situation was tedious.
    This function can simplify this process.

    Usage：
    quick_marshal(args_to_marshal_with_model)(db_instance_or_query)
    """
    @marshal_with_model(*args, **kwargs)
    def fn(value):
        return value
    return fn


def _wrap_field(field):
    """Improve Flask-RESTFul's original field type"""
    class WrappedField(field):
        def output(self, key, obj):
            value = _fields.get_value(key if self.attribute is None else self.attribute, obj)

            # For all fields, when its value was null (None), return null directly,
            #  instead of return its default value (eg. int type's default value was 0)
            # Because sometimes the client **needs** to know, was a field of the model empty, to decide its behavior.
            return None if value is None else self.format(value)
    return WrappedField


class _DateTimeField(_fields.Raw):
    """Transform `datetime` and `date` objects to timestamp before return it."""
    def format(self, value):
        try:
            return time.mktime(value.timetuple())
        except OverflowError:
            # value 是按照 0 时区计算的，但是 mktime 却会根据本地时区（东八区）计算，
            # 因此当value比unix纪元后的8小时要早时，得出的时间戳是负数的(东八区比0时区早8小时，0时区的8点是东八区的0点)
            # 在 windows 下，会直接报错，而不是返回负数时间戳，因此这里要捕获这类错误。
            # 因为这种时间出现基本都是在调试的时候，所以直接返回 0 时间戳就行了。
            return 0

        except AttributeError as ae:
            raise _fields.MarshallingException(ae)


class _FloatField(_fields.Raw):
    """Flask-RESTful will transform float value to a string before return it.
    This is not useful in most situation, so we change it to return float value directly"""

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
    'datetime': _wrap_field(_DateTimeField),
    'date': _wrap_field(_DateTimeField)
}