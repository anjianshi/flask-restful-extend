# -*- coding: utf-8 -*-

from flask.ext import restful
from flask import request, current_app, make_response
from json_encode_manager import JSONEncodeManager
import json


class RESTfulExtend(object):
    def __init__(self, api_instance, enhance_json_encode=True, fix_unauthorized=False):
        self.api_instance = api_instance

        # let flask-restful can support jsonp
        # use jsonp_callback_getter() method to confirm was current request is jsonp request.
        # if then, the method should return the callback (a string), else it return false.
        # default support format: url?jsonp=callback_name
        # you can extend the class, and rewrite jsonp_callback_getter() method, to handle another format
        if enhance_json_encode:
            api_instance.json_encoder = JSONEncodeManager()
            api_instance.representation('application/json')(self.output_json_with_jsonp)

    def output_json_with_jsonp(self, data, code, headers=None):
        # encode json (copy from output_json)
        settings = {
            'default': self.api_instance.json_encoder
        }
        if current_app.debug:
            settings.setdefault('indent', 4)
            settings.setdefault('sort_keys', True)
        dumped = json.dumps(data, **settings)
        if 'indent' in settings:
            dumped += '\n'

        resp = make_response(dumped, code)
        resp.headers.extend(headers or {})

        # handle jsonp
        if code == 200:
            callback = self.jsonp_callback_getter()
            if callback:
                resp.headers['Content-Type'] = 'application/javascript'
                resp.set_data(str(callback) + '(' + resp.get_data() + ')')

        return resp

    @staticmethod
    def jsonp_callback_getter():
        return request.args.get('jsonp', False)
