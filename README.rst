*Translate the document into English was a bit difficult, I have tried.*

Flask-RESTFul-extend
====================

Improve Flask-RESTFul's behavior. Add some new features.

All features that shown below was optional, choose according to your needs.


Improve error handling
----------------------
source: error_handling.py_

Flask-RESTFul's error handler can only output error message for the exceptions that raised by itself.

This make it can handling other kind of exceptions in same way.

.. code-block:: python

    api = restful_extend.ErrorHandledApi(app)   # instead of `api = restful.Api(app)`

    class MyRoutes(Resource):
        def get(self):
            raise Exception("errmsg")   # now, the 'errmsg' can output to client



Improve JSON support
--------------------

enhance JSON encode ability
^^^^^^^^^^^^^^^^^^^^^^^^^^^
sources: extend_json.py_, json_encode_manager.py_

Support more data type by default, and you can simply add supports for new data type.

.. code-block:: python

    # This is a custom type, you can't direct return a value of this type in Flask or Flask-RESTFul.
    class RationalNumber(object):
        def __init__(self, numerator, denominator):
            self.numerator = numerator
            self.denominator = denominator

    api = restful.Api(app)

    # Enable enhanced json encode feature
    enhance_json_encode(api)


    # create and register a custom encoder, to encode your custom type to serializable value.
    def rational_encoder(rational):
        return rational.numerator * 1.0 / rational.denominator

    api.json_encoder.register(rational_encoder, RationalNumber)


    class MyRoutes(Resource):
        def get(self):
            return RationalNumber(1, 5)     # now you can return the value of your custom type directly



support JSONP
^^^^^^^^^^^^^
source: extend_json.py_

Respond jsonp request automatically

.. code-block:: python

    api = restful.Api(app)
    support_jsonp(api)

    class MyRoutes(Resource):
        def get(self):
            return dict(foo='bar')

    api.add_resource(MyRoutes, '/my_routes')

    # normal request: /my_routes                    response: {"foo": "bar"}
    # jsonp request:  /my_routes?callback=my_cb     response: my_cb({"foo": "bar"})



SQLAlchemy related extend
-------------------------

marshal_with_model
^^^^^^^^^^^^^^^^^^
source: marshal.py_

Extend Flask-RESTFul's `marshal_with` decorator's behavior.
Auto define fields for ORM model.

.. code-block:: python

    class MyRoutes(Resource):
            # With `marshal_with_model`, you can return an model instance or model query
            # in view function directly.
            @marshal_with_model(MyModel, excludes=['id'])
            def get(self):
              return MyModel.query      # response: [my_model1, my_model2, ...]

            # If you need return different type of model in different situation, you can use `quick_marshal`
            def post(self):
              if something:
                  return quick_marshal(MyModel)(MyModel.query.get(1))   # response: my_model
              else:
                  return quick_marshal(HisModel)(HisModel.query)        # response: [his_model1, ...]



fast register URL converter for model
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
source: model_converter.py_

.. code-block:: python

    api = restful.Api(app)


    class Student(db.model):
        id = Column(Integer, primary_key=True)
        name =  Column(String(50))

    register_model_converter(Student)


    class MyRoutes(object):
        def get(self, classmate):
            pass

    api.add_resource(MyRoutes, '/classmates/<Student:classmate>')

    # request: /classmates/102      response: {"id": 102, "name": "superman"}



According to specified model's definition Create a RequestParser
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
source: model_reqparse.py_

required: fix_argument_convert, fixed_type (see next section)

.. code-block:: python

    class Student(db.model):
        id = Column(Integer, primary_key=True)
        name =  Column(String(50))
        age = Column(Integer)


    class MyRoutes(object):
        def post(self):
            # use `make_request_parser` quickly create a `RequestParser`
            parser = make_request_parser(Student)

            # you can update the parser as usual
            parser.add_argument('is_a_boy')

            request_data = parser.parse_args()
            print request_data['name'], request_data['age']
            # do something...


    class MyRoutes2(object):
        def post(self):
            # if you want padding the request data to a model,
            # you can use `populate_model`, it's more convenience.
            model = Student.query.get(1)
            populate_model(model)   # the model was updated use user request data



Improve Argument type handling
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sources: model_reqparse.py_, reqparse_fixed_type.py_

**fix_argument_convert**

Change `reqparse.Argument.convert`'s original behavior.

You should call this function before use `make_request_parser`, `populate_model` or fixed types.

**fixed types**

A set of customized type_constructor.

Use them in place of int、str、datetime... to be the type used in `Argument`'s `type` parameter,
this can provide some additional feature.



Model validates
^^^^^^^^^^^^^^^
source: model_validates.py_

Simplify and extend SQLAlchemy's attribute validates process.
This function has no relationship with Flask-RESTful.




More Details
------------
For more details, please read the documents in source.




.. _error_handling.py: https://github.com/anjianshi/flask-restful-extend/blob/master/flask_restful_extend/error_handling.py

.. _extend_json.py: https://github.com/anjianshi/flask-restful-extend/blob/master/flask_restful_extend/extend_json.py

.. _json_encode_manager.py: https://github.com/anjianshi/flask-restful-extend/blob/master/flask_restful_extend/json_encode_manager.py

.. _marshal.py: https://github.com/anjianshi/flask-restful-extend/blob/master/flask_restful_extend/marshal.py

.. _model_converter.py: https://github.com/anjianshi/flask-restful-extend/blob/master/flask_restful_extend/model_converter.py

.. _model_reqparse.py: https://github.com/anjianshi/flask-restful-extend/blob/master/flask_restful_extend/model_reqparse.py

.. _reqparse_fixed_type.py: https://github.com/anjianshi/flask-restful-extend/blob/master/flask_restful_extend/reqparse_fixed_type.py

.. _model_validates.py: https://github.com/anjianshi/flask-restful-extend/blob/master/flask_restful_extend/model_validates.py
