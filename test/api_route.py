# -*- coding: utf-8 -*-
from flask import request
from flask.ext import restful
from project import api
from api_exceptions import exception_data_list


class APIRoute(restful.Resource):
    def get(self):
        result_type = int(request.args.get('type'))
        exception_cls, message = exception_data_list[result_type - 1]
        raise exception_cls(message)

api.add_resource(APIRoute, '/api/')