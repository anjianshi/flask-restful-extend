在 Flask-RESTful 的基础上，进一步优化对 REST API 的支持，并修复它的一些不合理的行为。  

### API 扩展  
**ErrorHandledApi**
增强错误处理


#### JSON 扩展  
**enhance\_json\_encode** (extend\_json.py, json\_encode\_manager.py)  
增强对 json 的处理，默认支持更多数据类型，并可方便的处理新的类型  
  
**support\_jsonp** (extend\_json.py)  
自动响应 jsonp 请求  


#### SQLAlchemy 扩展  
**marshal\_with\_model** (marshal.py)  
根据给出的 model 类，对视图函数进行 marshal 操作。  
省去了手动设定 field\_definition 的麻烦  

**register\_model\_converter** (model\_converter.py)  
注册一个能解析出指定 model 的 URL Converter  

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