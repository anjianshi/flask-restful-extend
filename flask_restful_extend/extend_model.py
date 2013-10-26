# -*- coding: utf-8 -*-
"""
class Student(db.Model):
    ...

    validate_rules = [
        # column_names (str or list of str),
        # validate_func (name in predefined_validate_funcs, or custom function)
        # args will pass to validate_func
        ('age', 'min', 0)

        ('name', cust_func, arg_1, arg_2, ...)
    ]

    def cust_func(value, arg_1, arg_2, ...):
        # if valid, return True else return False
        return True

        # if you want transform the value of the column, 
        # return a dict, format like this:
        # dict(value=xxx)
        # then the column's value after call the validate_func, is xxx
        # 如果一个 validate_func 只进行转换操作，不进行检查，最好在命名时，加上 trans_ 前缀，这样可以更清晰的反映它的用途。
"""

from flask.ext import sqlalchemy as flask_as
from sqlalchemy.orm import validates as _orm_validates
from werkzeug.exceptions import BadRequest
import re


predefined_validate_funcs = {
    'min': lambda value, min_val: value >= min_val,
    'max': lambda value, max_val: value <= max_val,
    'min_length': lambda value, min_val: len(value) >= min_val,
    'match': lambda value, pattern: re.match(pattern, value),
    'trans_upper': lambda value: dict(value=value.upper())
}


_OrigMeta = flask_as._BoundDeclarativeMeta
class _ExtendedMeta(_OrigMeta):
    @classmethod
    def _make_validate_handler(cls, rule):
        column_names = rule[0]
        validate_func = rule[1]
        validate_args = rule[2:]

        if not isinstance(column_names, list):
            column_names = [column_names]

        if isinstance(validate_func, str):
            validate_func_name = validate_func
            validate_func = predefined_validate_funcs[validate_func]
        else:
            validate_func_name = validate_func.__name__
            
        @_orm_validates(*column_names)
        def f(self, column_name, value):
            # 如果字段值为 None，不进行检查，由 sqlalchemy 根据字段的 nullable 属性确定是否合法
            if value is not None:
                validate_result = validate_func(value, *validate_args)
                
                if isinstance(validate_result, dict) and 'value' in validate_result:
                    return validate_result['value']
                elif not validate_result:
                    #todo: better error reporting for front end
                    print(
                        u'db model validate failed: col={}, value={}, func={}, arg={}'.format(
                            column_name, value, validate_func_name,
                            ','.join([str(arg) for arg in validate_args])
                        )
                    )
                    raise BadRequest()
            return value
        return f
    
    def __new__(cls, name, bases, d):
        rule_count = 0

        for rule in d.get('validate_rules', []):
            while True:
                rule_count += 1
                rule_func_name = 'validate_rule_{}'.format(rule_count)
                if not d.get(rule_func_name):
                    d[rule_func_name] = cls._make_validate_handler(rule)
                    break

        return _OrigMeta.__new__(cls, name, bases, d)


def extend_model():
    """must called before create db instance"""
    flask_as._BoundDeclarativeMeta = _ExtendedMeta