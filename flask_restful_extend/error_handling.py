# -*- coding: utf-8 -*-
from flask.ext import restful
from werkzeug.exceptions import HTTPException

class ErrorHandledApi(restful.Api):
    """Usage:
        api = restful_extend.ErrorHandledApi(app)

    instead of:

        api = restful.Api(app)

    todo: support Python3 (under python3, Exception has no "message" attribute)
    """

    def handle_error(self, e):
        """
        Resolve the problem about sometimes error message specified by programmer won't output to user.

        Flask-RESTFul's error handler handling format different exceptions has different behavior.
        If we raise an normal Exception, it will raise it again.

        If we report error by `restful.abort()`,
         likes `restful.abort(400, message="my_msg", custom_data="value")`,
         it will make a response like this:

            Status     400
            Content    {"message": "my_msg", "custom_data": "value"}

        The error message we specified was outputted.

        And if we raise an HTTPException,
            likes `from werkzeug.exceptions import BadRequest; raise BadRequest('my_msg')`,
            if will make a response too, but the error message specified by ourselves was lost:

            Status     400
            Content    {"status": 400, "message": "Bad Request"}

        The reason is, flask-restful always use the `data` attribute of HTTPException to generate response content.
        But, standard HTTPException object didn't has this attribute.
        So, we use this method to add it manually.


        Some reference material:

        Structure of exceptions raised by restful.abort():
            code: status code
            description: predefined error message for this status code
            data: ｛
            　　　　message: error message
            ｝

        Structure of python's standard Exception:
            message: error message

        Structure of standard `werkzeug.exceptions.HTTPException` (same as BadRequest):
            code: status code
            name: the name correspondence to status code
            description: error message
        """
        if isinstance(e, HTTPException) and not hasattr(e, 'data'):
            e.data = dict(message=e.description)
        return super(ErrorHandledApi, self).handle_error(e)

    def unauthorized(self, response):
        """In default, when users was unauthorized, Flask-RESTFul will popup an login dialog for user.
        But for an RESTFul app, this is useless, so I override the method to remove this behavior."""
        return response
