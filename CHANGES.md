Version 0.3.5 (2015-06-27)
=========================
break changes:

### error_handle 处理逻辑变化
flask-restful-extend error_handle 现在只处理 HTTPException，对于其他 Exception，会直接抛出
因此用户应慎选抛出的异常的类型。对于客户端的不合法请求，抛出 HTTPException；对于服务器内部错误，抛出普通 Exception

### 移除 fix\_argument\_convert()，以及部分 fixed types 
flask-restful 的 reqparse 原来对 None 的处理逻辑是：
`如果 arg type 是 str，则直接返回 None。否则把 None 值传给 type 构造器，尝试构造（如果构造器无法解析 None，则最终会抛出异常）`
现在变成了：
`对于任何 arg type，都直接返回 None。`

而我之前为了应对 flask-restful 的行为，是这样修正的：
```
如果 arg type 是 str，返回一个字符串："None"。否则调用 flask-restful 原生的 reqparse 继续处理。
同时，我预设了一些 fixed types，这些 types 是原生类型的包裹层，能正常处理 None 值（处理方式是直接返回 None）
```
现在，根据 flask-restful 的新行为，我的行为也要跟着变化：
```
不对 str 的 arg type 做特殊处理，和其他类型一样，直接返回 None
fixed types 也无需考虑 None 的事情了，因为出现 None 时会直接跳过，这些构造器不会被调用
注意：原本当 None 值出现了的时候，构造器是会被调用的；但现在它们不会被调用了。如果有些构造器依赖于这一情况（它们专门为 None 值准备了处理逻辑），那么这些逻辑会无效。
```


Version 0.3.1 (2014-12)
=========================

- Refactor SQLAlchemy model validator's implementation.

**Notice:** the use case was change

Before:
```python
class People(db.Model):
    name = Column(String(100))
    age = Column(Integer)
    IQ = Column(Integer)

    validate_rules = [
        ('name', 'min_length', 1)
        ('name', 'max_length', 100)
        (['age', 'IQ', 'min', 0)
    ]
```

After:
```python
class People(db.Model):
    name = Column(String(100))
    age = Column(Integer)
    IQ = Column(Integer)

    validator = complex_validates({
        'name': (('min_length', 1), ('max_length', 100))
        ('age', 'IQ'): [('min', 0)]
    })
```

- `_CantEncodeObjException` renames to `CantEncodeObjException`

- Changes default callback\_name\_source from 'jsonp' to 'callback'
