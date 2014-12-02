# -*- coding: utf-8 -*-
"""Simplify and extend SQLAlchemy's attribute validates process"""

__all__ = ['complex_validates']

from sqlalchemy.orm import validates
import re


predefined_predicates = {
    'min': lambda value, min_val: value >= min_val,
    'max': lambda value, max_val: value <= max_val,
    'min_length': lambda value, min_val: len(value) >= min_val,

    # When define a CHAR-like column, we have generally already specify a max length.
    # So, do we really need the max_length predicate? Yes, we need.
    # Cause the database will just cut sting when it is too lang, and will not raise an error,
    # so we won't noticed. But use this predicate, it will raise and Exception, and stop the whole action,
    # so we can handle the sting safety.
    'max_length': lambda value, max_val: len(value) <= max_val,

    'match': lambda value, pattern: re.match(pattern, value),

    # If a predicate will change the original value, we'd better add `trans_` prefix to it's name,
    # so we can know it's use clearly.
    'trans_upper': lambda value: dict(value=value.upper())
}


class ModelInvalid(Exception):
    code = 400


def complex_validates(validate_rule):
    """Quickly setup attributes validation by one-time, based on `sqlalchemy.orm.validates`.

    Don't like `sqlalchemy.orm.validates`, you don't need create many model method,
    as long as pass formatted validate rule.
    (Cause of SQLAlchemy's validate mechanism, you need assignment this funciton's return value
    to a model property.)

    For simplicity, complex_validates don't support `include_removes` and `include_backrefs` parameters
    that in `sqlalchemy.orm.validates`.

    And we don't recommend you use this function multiple times in one model.
    Because this will bring many problems, like:
    1. Multiple complex_validates's execute order was decide by it's model property name, and by reversed order.
       eg. predicates in `validator1 = complex_validates(...)`
       will be executed **AFTER** predicates in `validator2 = complex_validates(...)`
    2. If you try to validate the same attribute in two (or more) complex_validates, only one of complex_validates
       will be execute. (May be this is a bug of SQLAlchemy?)
    `complex_validates` was currently based on `sqlalchemy.orm.validates`, so it is difficult to solve these problems.
    May be we can try to use `AttributeEvents` directly in further, to provide more reliable function.

    Rule Format
    -----------

    {
        column_name: predicate                          # basic format
        (column_name2, column_name3): predicate         # you can specify multiple column_names to given predicates
        column_name4: (predicate, predicate2)           # you can specify multiple predicates to given column_names
        column_name5: [(predicate, arg1, ... argN)]     # and you can specify what arguments should pass to predicate
                                                        # when it doing validate
        (column_name6, column_name7): [(predicate, arg1, ... argN), predicate2]   # another example
    }

    Notice: If you want pass arguments to predicate, you must wrap whole command by another list or tuple.
            Otherwise, we will determine the argument as another predicate.
            So, this is wrong: { column_name: (predicate, arg) }
            this is right: { column_name: [(predicate, arg)] }

    Predicate
    ---------

    There's some `predefined_predicates`, you can just reference its name in validate rule.

        {column_name: ['trans_upper']}

    Or you can pass your own predicate function to the rule, like this:

        def custom_predicate(value):
            return value_is_legal       # return True or False for valid or invalid value

        {column_name: [custom_predicate]}

    If you want change the value when doing validate, return an `dict(value=new_value)` instead of boolean

        {column_name: lambda value: dict(value = value * 2)}   # And you see, we can use lambda as a predicate.

    And the predicate can receive extra arguments, that passes in rule:

        def multiple(value, target_multiple):
            return dict(value= value * target_multiple)

        {column_name: (multiple, 10)}

    Complete Example
    ----------------

    class People(db.Model):
        name = Column(String(100))
        age = Column(Integer)
        IQ = Column(Integer)
        has_lover = Column(Boolean)

        validator = complex_validates({
            'name': [('min_length', 1), ('max_length', 100)],
            ('age', 'IQ'): [('min', 0)],
            'has_lover': lambda value: return !value    # hate you!
        })"""

    ref_dict = {
        # column_name: (
        #   (predicate, arg1, ... argN),
        #   ...
        # )
    }

    for column_names, predicate_refs in validate_rule.iteritems():
        for column_name in _to_tuple(column_names):
            ref_dict[column_name] = \
                ref_dict.get(column_name, tuple()) + _normalize_predicate_refs(predicate_refs)

    return validates(*ref_dict.keys())(
        lambda self, name, value: _validate_handler(name, value, ref_dict[name]))


def _to_tuple(value):
    return tuple(value) if type(value) in [tuple, list] else (value,)


def _normalize_predicate_refs(predicate_refs):
    """
    In                                  Out
    'trans_upper'                       (('trans_upper',),)
    ('trans_upper', 'trans_lower')      (('trans_upper',), ('trans_lower',))
    [('min', 1)]                        (('min', 1),)
    (('min', 1), 'trans_lower')         (('min', 1), ('trans_lower',))
    """
    return tuple(_to_tuple(predicate_ref) for predicate_ref in _to_tuple(predicate_refs))


def _validate_handler(column_name, value, predicate_refs):
    """handle predicate's return value"""

    # only does validate when attribute value is not None
    # else, just return it, let sqlalchemy decide if the value was legal according to `nullable` argument's value
    if value is not None:
        for predicate_ref in predicate_refs:
            predicate, predicate_name, predicate_args = _decode_predicate_ref(predicate_ref)
            validate_result = predicate(value, *predicate_args)

            if isinstance(validate_result, dict) and 'value' in validate_result:
                value = validate_result['value']
            elif not validate_result:
                raise ModelInvalid(u'db model validate failed: column={}, value={}, predicate={}, arguments={}'.format(
                    column_name, value, predicate_name, ','.join(map(str, predicate_args))
                ))
    return value


def _decode_predicate_ref(rule):
    predicate, predicate_args = rule[0], rule[1:]

    if isinstance(predicate, str):
        predicate_name = predicate
        predicate = predefined_predicates[predicate]
    else:
        predicate_name = predicate.__name__

    return [predicate, predicate_name, predicate_args]
