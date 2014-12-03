# -*- coding: utf-8 -*-
from werkzeug.exceptions import BadRequest, Unauthorized


class CustomException(Exception):
    code = 500


class CustomException2(BadRequest):
    def __init__(self, data):
        self.data = dict(message=data)


exception_data_list = [
    # Test if it can handle any type of exceptions, and output the right error message.

    # test HTTPException
    (BadRequest, 'my badrequest message'),

    # test normal python exception, with `code` attribute
    (CustomException, 'my customexception message'),

    # test exceptions that has both `data` and `description` attribute.
    (CustomException2, 'real message'),

    # test has disabled the unauthorized dialog
    (Unauthorized, 'my unauthorized message')
]