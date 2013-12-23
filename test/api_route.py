# -*- coding: utf-8 -*-
from flask import request
from flask.ext import restful
from project import api
from api_exceptions import exception_data_list


class APIRoute(restful.Resource):
    def get(self):
        exec_index = int(request.args.get('index'))
        exception_cls, message = exception_data_list[exec_index]
        raise exception_cls(message)

api.add_resource(APIRoute, '/api/')