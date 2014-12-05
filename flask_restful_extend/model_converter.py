# -*- coding: utf-8 -*-
from werkzeug.routing import BaseConverter
from werkzeug.exceptions import NotFound


def register_model_converter(model, app):
    """Add url converter for model

    Example:
        class Student(db.model):
            id = Column(Integer, primary_key=True)
            name =  Column(String(50))

        register_model_converter(Student)

        @route('/classmates/<Student:classmates>')
        def get_classmate_info(classmates):
            pass

    This only support model's have single primary key.
    You need call this function before create view function.
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
            raise NotFound(u'{}(id={}) not exists，request invalid'.format(self._model.__name__, inst_id))
        return instance

    def to_url(self, inst):
        return str(inst.id)
