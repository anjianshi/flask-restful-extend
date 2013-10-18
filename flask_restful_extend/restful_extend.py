
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


def populate_model(model_or_inst, excludes=[]):
    """
    传入一个 model 类(model)或者 model 实例(model_inst)
    根据对应的 model 的定义，构建 RequestParser，
    并用它从 request.json 中提取、转换用户输入，
    最终填充进 model_inst (若传入的是 model 类，会创建一个它的实例作为 model_inst)
    
    model 的主键不会被添加到 RequestParser 的 args 列表里
    若传入的是 model 类，还会根据 model column 的 nullable 属性，对用户传入的参数添加 required 检查
    (若传入的是 model_inst，则不会进行此项检查。因为这种情况下，应该允许用户忽略对某个字段的赋值)
    
    若想用用户提交的数据创建新实例，应直接传入 model 类；若想用用户提交的数据修改现有实例，应传入 model_inst
    """
    
    is_inst = hasattr(model_or_inst, '_sa_instance_state')
    model_inst = model_or_inst if is_inst else model_or_inst()
    
    parser = reqparse.RequestParser()
    for col in model_inst.__table__.columns:
        if not col.primary_key and col.name not in excludes:
            kwargs = {
                "type": col.type.python_type,
                "location": 'json'
            }
            if not is_inst and not col.nullable:
                kwargs["required"] = True
            parser.add_argument(col.name, **kwargs)
    
    for key, value in parser.parse_args().iteritems():
        setattr(model_inst, key, value)
    
    return model_inst