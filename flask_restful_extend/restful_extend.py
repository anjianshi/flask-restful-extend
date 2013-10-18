# -*- coding: utf-8 -*-

from flask.ext import restful
from flask import request

class RESTfulExtend(object):
  def __init__(self, api_instance, support_jsonp=True, fix_unauthorized=False):
    # let flask-restful can support jsonp
    # use jsonp_callback_getter() method to confirm was current request is jsonp request.
    # if then, the method should return the callback (a string), else it return false.
    # default support format: url?jsonp=callback_name
    # you can extend the class, and rewrite jsonp_callback_getter() method, to handle another format 
    if support_jsonp:
      api_instance.representation('application/json')(self.output_json_with_jsonp)

    # let flask-restful don't popup an auth dialog when app call abort(401)
    if fix_unauthorized:
      restful.unauthorized = lambda resp, realm: resp

  def output_json_with_jsonp(self, data, code, headers=None):
    resp = restful.output_json(data, code, headers)

    if code == 200:
      callback = self.jsonp_callback_getter()
      if callback:
        resp.headers['Content-Type'] = 'application/javascript'
        resp.set_data(str(callback) + '(' + resp.get_data() + ')')

    return resp

  @staticmethod
  def jsonp_callback_getter():
    return request.args.get('jsonp', False)
