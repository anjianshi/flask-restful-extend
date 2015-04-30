# -*- coding: utf-8 -*-

from flask import request, current_app, make_response
from json_encode_manager import JSONEncodeManager
import json


def enhance_json_encode(api_instance, extra_settings=None):
    """use `JSONEncodeManager` replace default `output_json` function of Flask-RESTful
    for the advantage of use `JSONEncodeManager`, please see https://github.com/anjianshi/json_encode_manager"""
    api_instance.json_encoder = JSONEncodeManager()

    dumps_settings = {} if extra_settings is None else extra_settings
    dumps_settings['default'] = api_instance.json_encoder
    dumps_settings.setdefault('ensure_ascii', False)

    @api_instance.representation('application/json')
    def output_json(data, code, headers=None):
        if current_app.debug:
            dumps_settings.setdefault('indent', 4)
            dumps_settings.setdefault('sort_keys', True)

        dumped = json.dumps(data, **dumps_settings)
        if 'indent' in dumps_settings:
            dumped += '\n'

        resp = make_response(dumped, code)
        resp.headers.extend(headers or {})
        return resp


def support_jsonp(api_instance, callback_name_source='callback'):
    """Let API instance can respond jsonp request automatically.

    `callback_name_source` can be a string or a callback.
        If it is a string, the system will find the argument that named by this string in `query string`.
         If found, determine this request to be a jsonp request, and use the argument's value as the js callback name.

        If `callback_name_source` is a callback, this callback should return js callback name when request
         is a jsonp request, and return False when request is not jsonp request.
         And system will handle request according to its return value.

    default support format：url?callback=js_callback_name
    """
    output_json = api_instance.representations['application/json']

    @api_instance.representation('application/json')
    def handle_jsonp(data, code, headers=None):
        resp = output_json(data, code, headers)

        if code == 200:
            callback = request.args.get(callback_name_source, False) if not callable(callback_name_source) \
                else callback_name_source()
            if callback:
                resp.set_data(str(callback) + '(' + resp.get_data().decode("utf-8") + ')')

        return resp
