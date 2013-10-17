from flask.ext import restful
from flask import request
from flask.ext.restful import reqparse

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
  

def populate_model(model_inst, excludes=[]):
    """
    根据 model_inst 对应的 model 的定义，从 request.json 中提取、转换用户输入，并填充进 model_inst
    todo: 若 model_inst 不是新的，有些字段不应在 arg parser 中检查 required 而应该在填充完成后，对 model_inst 进行检查
    :param model_inst: 
    :param excludes: 
    :return model_inst:
    """
    
    parser = reqparse.RequestParser()
    
    for col in model_inst.__table__.columns:
        if not col.primary_key and col.name not in excludes:
            parser.add_argument(col.name, type=col.type.python_type, required=not col.nullable, location='json')
            
    args = parser.parse_args()
    for key, value in args.iteritems():
        setattr(model_inst, key, value)
    
    return model_inst