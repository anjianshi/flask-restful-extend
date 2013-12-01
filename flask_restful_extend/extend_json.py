# -*- coding: utf-8 -*-

from flask import request, current_app, make_response
from json_encode_manager import JSONEncodeManager
import json


def enhance_json_encode(api_instance, extra_settings=None):
    """用 :class:`JSONEncodeManager` 代替 Flask-RESTful 默认的 output_json 函数。"""
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


def support_jsonp(api_instance, callback_name_source='jsonp'):
    """让 API instance 能够自动处理 jsonp 请求。

    callback_name_source 的值可以是一个字符串或者一个回调函数。
    当它是字符串时，系统会在 query string 中寻找对应名称的参数。若存在，则把当前请求视为 jsonp 请求，并把它的值当作 js 回调函数的名称。
    如果 callback_name_source 是一个回调函数，系统会把它的返回值作为 js 回调函数名称。当请求类型不是 jsonp 时，这个回调函数应该返回 False。

    默认支持的格式：url?jsonp=js_callback_name
    """
    output_json = api_instance.representations['application/json']

    @api_instance.representation('application/json')
    def handle_jsonp(data, code, headers=None):
        resp = output_json(data, code, headers)

        if code == 200:
            callback = request.args.get(callback_name_source, False) if not callable(callback_name_source) \
                else callback_name_source()
            if callback:
                resp.set_data(str(callback) + '(' + resp.get_data() + ')')

        return resp
