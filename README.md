在 Flask-RESTful 的基础上，进一步优化对 REST API 的支持，并修复它的一些不合理的行为。  

### Improve error handling  
**ErrorHandledApi**


#### JSON extend  
**enhance\_json\_encode** (extend\_json.py, json\_encode\_manager.py)  
Extend json encode support, support more data type by default,
and you can simply add support for new data type.
  
**support\_jsonp** (extend\_json.py)  
Respond jsonp request automatically


#### SQLAlchemy related extend  
**marshal\_with\_model** (marshal.py)  
Extend Flask-RESTFul's `marshal_with` decorator's behavior.  
Auto define fields for ORM model.

**register\_model\_converter** (model\_converter.py)  
register a URL Converter for specific model  

**make\_request\_parser**, **populate\_model** (model\_reqparse.py)  
基于 model class / instance 创建 RequestParser 实例  

**fix\_argument\_convert** (model\_reqparse.py)  
修改 reqparse.Argument.convert 的一些默认行为，使其更合理、统一 

**fixed_type** (reqparse\_fixed\_type.py)  
经过定制的一系列 arg value 类型转换函数  
代替 int、str、datetime... 作为 Argument type 参数的值，能够提供一些附加功能  
具体请看相关代码
（需调用 fix\_argument\_convert() 后才能正常使用）

**model\_validates** (model_validates.py)  
Simplify and extend SQLAlchemy's attribute validates process.  
This function has no relationship with Flask-RESTful.


关于各功能的细节，请查看源代码中的注释。  