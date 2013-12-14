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

from sqlalchemy.orm.mapper import Mapper
import re


predefined_validate_funcs = {
    'min': lambda value, min_val: value >= min_val,
    'max': lambda value, max_val: value <= max_val,
    'min_length': lambda value, min_val: len(value) >= min_val,
    # 定义数据库字段时，本身就会限制其最大长度。但此验证器仍然有必要存在。
    # 此验证器验证失败时，会终止操作，抛出异常。而数据库在某些情况下可能只是截断字符串，不报错，导致问题不会被发现。
    'max_length': lambda value, max_val: len(value) <= max_val,
    'match': lambda value, pattern: re.match(pattern, value),
    'trans_upper': lambda value: dict(value=value.upper())
}


class ModelInvalid(Exception):
    code = 400


def extend_model():
    """must called before create db instance"""

    def make_validate_handler(rules):
        formatted_rules = []
        for rule in rules:
            validate_func = rule[0]
            if isinstance(validate_func, str):
                validate_func_name = validate_func
                validate_func = predefined_validate_funcs[validate_func]
            else:
                validate_func_name = validate_func.__name__

            formatted_rule = [validate_func, validate_func_name]
            formatted_rule.extend(rule[1:])
            formatted_rules.append(formatted_rule)

        def f(self, column_name, value):
            # 如果字段值为 None，不进行检查，由 sqlalchemy 根据字段的 nullable 属性确定是否合法
            if value is not None:
                for rule in formatted_rules:
                    validate_func = rule[0]
                    validate_func_name = rule[1]
                    validate_args = rule[2:]

                    validate_result = validate_func(value, *validate_args)

                    if isinstance(validate_result, dict) and 'value' in validate_result:
                        value = validate_result['value']
                    elif not validate_result:
                        raise ModelInvalid(u'db model validate failed: col={}, value={}, func={}, arg={}'.format(
                            column_name, value, validate_func_name,
                            ','.join([str(arg) for arg in validate_args])
                        ))
            return value
        return f

    _orig_configure_class_instrumentation = Mapper._configure_class_instrumentation

    def _new_configure_class_instrumentation(self):
        return_value = _orig_configure_class_instrumentation(self)

        if hasattr(self.class_, 'validate_rules'):
            rule_dict = {
                # col_name: [
                #   (cust_func, arg_1, arg_2, ...)
                #   (cust_func2, arg_1, arg_2, ...)
                #   ...
                # ]
            }

            for orig_rule in self.class_.validate_rules:
                column_names = orig_rule[0]
                if not isinstance(column_names, list):
                    column_names = [column_names]

                for name in column_names:
                    rules = rule_dict.get(name, [])
                    rules.append(orig_rule[1:])
                    rule_dict[name] = rules

            for column_name, rules in rule_dict.iteritems():
                method = make_validate_handler(rules)
                self.validators = self.validators.union(
                    {column_name: (method, False)}
                )

        return return_value

    Mapper._configure_class_instrumentation = _new_configure_class_instrumentation