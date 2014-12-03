# -*- coding: utf-8 -*-
from flask import json
from datetime import datetime
import time
from decimal import Decimal


def _transform_iterable_obj(obj):
    if hasattr(obj, '__iter__'):
        return [i for i in obj]
    else:
        raise CantEncodeObjException()

_predefined_json_encoders = [
    (datetime, lambda value: time.mktime(value.timetuple())),
    (Decimal, lambda v: float(v))
]

_predefined_common_json_encoders = [
    _transform_iterable_obj
]


class JSONEncodeManager(object):
    """Python's default json encoder was difficult to extend.
    Use this, you can simply register custom encoder, to handle the data types that default json encoder can't encode.

    Usage：
        json_encode_manager = JSONEncodeManager()
        json_encode_manager.register(some_encoder, some_python_type)
        ...
        json.dumps(data, default=json_encode_manager)

    For JSONEncodeManager, there are two kinds of `encoder`:
        The first one was `specialized`.
         It can only encode object instance of one specific type or it's subtype.
         The manager will call it only if the type of data matches its register type.

        The other one was `generalized`, called `common_encoder`.
         A common_encoder can encode multiple type of data (eg. tuple and list).

         JSONEncodeManager will pass any type of data to these encoder.
         The encoder should raise a `CantEncodeObjException` exception, if it think this value shouldn't handle by itself.
         System will catch this exception, and pass data to next encoder.

    `specialized` encoder has higher priority than `common_encoder`.

    System has already define some encoders, in `_predefined_json_encoders` and `_predefined_common_json_encoders`
    These encoders will be registered automatically.
    """
    def __init__(self):
        self.encoders = []
        self.common_encoders = []

        self.flask_json_encoder = json.JSONEncoder()

    def register(self, encoder, target_class=None):
        if target_class:
            self.encoders.append((target_class, encoder))
        else:
            self.common_encoders.append(encoder)

    def __call__(self, o):
        encoders = []
        encoders.extend(self.encoders)
        encoders.extend(_predefined_json_encoders)
        encoders.extend(self.common_encoders)
        encoders.extend(_predefined_common_json_encoders)

        for encoder in encoders:
            if isinstance(encoder, tuple):
                if isinstance(o, encoder[0]):
                    return encoder[1](o)
            else:
                try:
                    return encoder(o)
                except CantEncodeObjException:
                    pass
        return self.flask_json_encoder.default(o)


class CantEncodeObjException(Exception):
    pass