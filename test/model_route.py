# -*- coding: utf-8 -*-
from flask import request
from flask.ext import restful
from flask_restful_extend import marshal_with_model
from project import api
from model_model import *


class MarshalRoute(restful.Resource):
    @marshal_with_model(Entity)
    def get(self):
        response_type = int(request.args.get('type'))
        if response_type == 1:
            return Entity.query.get(3)
        elif response_type == 2:
            return Entity.query

api.add_resource(MarshalRoute, '/marshal/')
