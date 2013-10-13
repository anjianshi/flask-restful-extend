# -*- coding: utf-8 -*-
"""
extend flask-restfurl and fix some unreasonable behave

include:
	jsonp support
	disable auth dialog
	better support to sqlalchemy model return value
"""

__version__ = 0.1


class Extend(object):
	def __init__(self, api_instance, support_jsonp=True, fix_unauthorized=False):
		# let flask-restful can support jsonp
		# use jsonp_callback_getter() method to confirm was current request is jsonp request.
		# if then, the method should return the callback (a string), else it return false.
		# default support format: url?jsonp=callback_name
  	# you can extend the class, and rewrite jsonp_callback_getter() method, to handle another format 
		if support_jsonp:
			api_instance.representation('application/json')(self.output_json_with_jsonp)

		# let flask-restful don't popup an auth dialog when app call abort(401)
		if fix_unauthorized:
			restful.unauthorized = lambda resp, realm: resp

	def output_json_with_jsonp(self, data, code, headers=None):
    resp = output_json(data, code, headers)

    if code == 200:
    	callback = self.jsonp_callback_getter()
    	if callback:
        resp.headers['Content-Type'] = 'application/javascript'
        resp.set_data(str(callback) + '(' + resp.get_data() + ')')

    return resp
  
  def jsonp_callback_getter():
		return request.args.get('jsonp', False)


_type_map = {
    'str': fields.String,
    'int': fields.Integer,
    'float': fields.Integer,
    'bool': fields.Boolean,
    'datetime': fields.DateTime
}


def marshal_with_model(model, excludes=[]):
		"""
		  help view methods return orm model object more easily (only face to flask-sqlalchemy)
			1. transform columns in model to fields that flask-restful can understand. 
			   use the 'excludes' argument, you can specify columns shouldn't appear in return value
			2. when you return query object directly, auto transform it to list

			example：
			model：
			Student
				id int
				name string
				age int

			class SomeApi(Resource):
				@marshal_with_model(Student, excludes=['id'])
				def get(self):
					return Student.query

			return value to client：
			[{"name": "student_a", "age": "16"}, {"name": "student_b", "age": 18}]
		"""
    field_definition = {}
    for col in model.__table__.columns:
        if col.name not in excludes:
            field_definition[col.name] = _type_map[col.type.python_type.__name__]

    def decorated(f):
        @wraps(f)
        @marshal_with(field_definition)
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)
            return result if not fields.is_indexable_but_not_string(result) else [v for v in result]
        return wrapper
    return decorated