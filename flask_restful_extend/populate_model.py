# -*- coding: utf-8 -*-
from flask.ext.restful import reqparse

def populate_model(model_or_inst, excludes=None, only=None, return_args=False):
    """
    传入一个 model 类(model)或者 model 实例(model_inst)
    根据对应的 model 的定义，构建 RequestParser，
    并用它从 request.json 中提取、转换用户输入，
    最终填充进 model_inst (若传入的是 model 类，会创建一个它的实例作为 model_inst)
    
    model 的主键不会被添加到 RequestParser 的 args 列表里
    若传入的是 model 类，还会根据 model column 的 nullable 属性，对用户传入的参数添加 required 检查
    (若传入的是 model_inst，则不会进行此项检查。因为这种情况下，应该允许用户忽略对某个字段的赋值)
    
    若想用用户提交的数据创建新实例，应直接传入 model 类；若想用用户提交的数据修改现有实例，应传入 model_inst
    
    excludes 和 only 用于控制哪些 column 应该被处理
     return_args 若为 True，则不会进行填充操作，返回解析出来的 args
    """
    if excludes is None:
        excludes = []
    if only is None or len(excludes):
        only = []
    
    is_inst = hasattr(model_or_inst, '_sa_instance_state')
    model_inst = model_or_inst if is_inst else model_or_inst()
    
    parser = reqparse.RequestParser()
    for col in model_inst.__table__.columns:
        if col.name in only or (not col.primary_key and col.name not in excludes):
            kwargs = {
                "type": col.type.python_type,
                "location": 'json'
            }
            if not is_inst and not col.nullable:
                kwargs["required"] = True
            parser.add_argument(col.name, **kwargs)
    args = parser.parse_args()
    
    if return_args:
        return args
    
    for key, value in args.iteritems():
        setattr(model_inst, key, value)
    
    return model_inst