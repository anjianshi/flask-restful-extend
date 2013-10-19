# -*- coding: utf-8 -*-
from flask.ext.restful import reqparse


def _is_inst(model_or_inst):
    return hasattr(model_or_inst, '_sa_instance_state')


def make_request_parser(model_or_inst, excludes=None, only=None):
    """
    传入一个 model 类(model)或者 model 实例(model_inst)
    根据对应的 model 的定义，构建一个从 request.json 中提取用户输入的 RequestParser。
    
    excludes 和 only 用于控制哪些 column 应该被处理。若同时传入 excludes 和 only，只有 excludes 会生效。
    model 的主键默认不会被添加到 RequestParser 的 args 列表里。
    可通过在 only 中指定这个主键，强制把它添加进去。
    
    若传入的是 model 类，还会根据 model column 的 nullable 属性，对用户传入的参数添加 required 检查
    (若传入的是 model_inst，则不会进行此项检查。因为这种情况下，应该允许用户忽略对某个字段的赋值)
    """
    is_inst = _is_inst(model_or_inst)
    
    if isinstance(excludes, str) or isinstance(excludes, unicode):
        excludes = [excludes]
    if excludes and only:
        only = None
    elif isinstance(only, str) or isinstance(only, unicode):
        excludes = [excludes]
    
    parser = reqparse.RequestParser()
    for col in model_or_inst.__table__.columns:
        if only:
            if col.name not in only:
                continue
        elif (excludes and col.name in excludes) or col.primary_key:
                continue
            
        kwargs = {
            "type": col.type.python_type,
            "location": 'json'
        }
        if not is_inst and not col.nullable:
            kwargs["required"] = True
        parser.add_argument(col.name, **kwargs)
    return parser


def populate_model(model_or_inst, *args, **kwargs):
    """
    调用 make_request_parser() 构建一个 RequestParser 并用它提取用户输入，填充到指定的 model_inst 中。
    (若传入的是 model 类，会创建一个它的实例，并将其作为 model_inst)
    """
    model_inst = model_or_inst if _is_inst(model_or_inst) else model_or_inst()
    
    parser = make_request_parser(model_or_inst, *args, **kwargs)
    req_args = parser.parse_args()
    
    for key, value in req_args.iteritems():
        setattr(model_inst, key, value)
    
    return model_inst