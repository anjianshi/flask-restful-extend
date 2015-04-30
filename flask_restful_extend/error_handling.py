# -*- coding: utf-8 -*-
from flask.ext import restful


class ErrorHandledApi(restful.Api):
    """Usage:
        api = restful_extend.ErrorHandledApi(app)

    instead of:

        api = restful.Api(app)

    todo: support Python3 (under python3, Exception has no "message" attribute)
    """

    def handle_error(self, e):
        """Resolve the problem about sometimes error message specified by programmer won't output to user.

        Flask-RESTFul's error handler handling format different exceptions has different behavior.
        If we report error by `restful.abort()`,
         likes `restful.abort(400, message="my_msg", custom_data="value")`,
         it will output:

            Status     400
            Content    {"message": "my_msg", "custom_data": "value"}

        The error message was outputted normally.

        But, if we use `flask.abort()`, or raise an exception by any other way,
         example `from werkzeug.exceptions import BadRequest; raise BadRequest('my_msg')`,
         it will output:

            Status     400
            Content    {"status": 400, "message": "Bad Request"}

        The output content's format was change, and the error message specified by ourselves was lose.

        Let's see why.

        The exception-format supported by Flask-RESTFul's error handler was:
            code: status code
            data: ｛
            　　　　message: error message
            }

        Exceptions raised by Flask-RESTFul's format was like this, so error handler can handling it normally:
            code: status code
            description: predefined error message for this status code
            data: ｛
            　　　　message: error message
            ｝

        This is python's standard Exception's format:
            message: error message

        And this is `werkzeug.exceptions.HTTPException` (same as BadRequest) 's format:
            code: status code
            name: the name correspondence to status code
            description: error message

        Flask-RESTFul's error handler hasn't handle these exceptions as my expectation.
        What I need to do, was create an attribute names `code` for exceptions doesn't have it,
         and create an attribute names `data` to represent the original error message."""

        if not hasattr(e, 'data'):
            if hasattr(e, 'description'):
                e.data = dict(message=e.description)
            elif hasattr(e, 'message'):
                if not hasattr(e, 'code'):
                    e.code = 500
                e.data = dict(message=e.message)
        return super(ErrorHandledApi, self).handle_error(e)

    def unauthorized(self, response):
        """In default, when users was unauthorized, Flask-RESTFul will popup an login dialog for user.
        But for an RESTFul app, this is useless, so I override the method to remove this behavior."""
        return response
