在 flask-restful 的基础上，进一步优化对 REST API 的支持，并修复它的一些不合理的行为。

#### JSON 扩展
`enhance_json_encode` (extend\_json.py)
增强对 json 的处理，默认支持更多数据类型，并可方便的处理新的类型

`support_jsonp` (extend\_json.py)
自动响应 jsonp 请求


#### SQLAlchemy 扩展
`marshal_with_model` (marshal.py)
根据给出的 model 类，对视图函数进行 marshal 操作。
省去了手动设定 field\_definition 的麻烦

`register_model_converter` (model\_converter.py)
注册一个能解析出指定 model 的 URL Converter

`make_request_parser`, `populate_model` (model\_reqparse.py)
基于 model class / instance 创建 RequestParser 实例

`extend_model` (extend_model.py)
扩展 SQLAlchemy 的 model 类，简化 model 验证规则的创建过程
此功能与 Flask-RESTful 无关。


关于各功能的细节，请查看源代码中的注释。