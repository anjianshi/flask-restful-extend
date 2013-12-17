# -*- coding: utf-8 -*-
from flask import request
from flask.ext import restful
from flask_restful_extend import marshal_with_model, register_model_converter
from project import api, app
from model_model import *


class MarshalRoute(restful.Resource):
    @marshal_with_model(Entity)
    def get(self):
        response_type = int(request.args.get('type'))
        if response_type == 1:
            return Entity.query.get(1)
        elif response_type == 2:
            return Entity.query.get(2)
        elif response_type == 3:
            return Entity.query

api.add_resource(MarshalRoute, '/marshal/')

# ======================

register_model_converter(Entity, app)


class ConverterRoute(restful.Resource):
    @marshal_with_model(Entity)
    def get(self, entity):
        return entity

api.add_resource(ConverterRoute, '/conv/<Entity:entity>')
