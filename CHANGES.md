Version 0.3.1 (2014-12-)
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
