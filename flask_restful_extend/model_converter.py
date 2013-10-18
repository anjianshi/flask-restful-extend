# -*- coding: utf-8 -*-
from werkzeug.routing import BaseConverter
from werkzeug.exceptions import NotFound

def register_model_converter(model, app):
    """
    为 model 添加 url converter
    
    添加后的使用方法：
    （冒号左侧的部分是表名，不是类名）
    @route('/goods/<goods:goods>')
    def get_goods_detail(goods):
        pass
    
    只支持单主键，且主键字段名为 id 的 model
    须在 view method 加载前调用
    """
    if hasattr(model, 'id'):
        class Converter(_ModelConverter):
            _model = model
        app.url_map.converters[model.__name__] = Converter


class _ModelConverter(BaseConverter):
    _model = None
    
    def to_python(self, inst_id):
        instance = self._model.query.get(inst_id)
        if instance is None:
            raise NotFound(u'{}(id={})不存在，请求不合法'.format(self._model.__name__, inst_id))
        return instance
    
    def to_url(self, inst):
        return str(inst.id)