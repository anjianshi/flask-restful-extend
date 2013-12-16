# -*- coding: utf-8 -*-
import flask_restful_extend as restful_extend
from project import api
from json_data import encode_map, CustomDataType, CustomDataType2
from flask_restful_extend.json_encode_manager import _CantEncodeObjException
from flask import request
from flask.ext import restful


restful_extend.enhance_json_encode(api)
api.json_encoder.register(lambda obj: dict(a=obj.a, b=obj.b), CustomDataType)


def custom_common_encoder(obj):
    if isinstance(obj, CustomDataType2):
        return dict(c=obj.c, d=obj.d)
    else:
        raise _CantEncodeObjException()
api.json_encoder.register(custom_common_encoder)


class JSONRoute(restful.Resource):
    def get(self):
        index = int(request.args.get('result'))
        return encode_map[index][0]

api.add_resource(JSONRoute, '/json/')