# -*- coding: utf-8 -*-
from werkzeug.exceptions import BadRequest, Unauthorized


class CustomException(Exception):
    code = 500

exception_data_list = [
    # 测试能否正常处理 HTTPException 和带 code 属性的标准 Python 异常，并输出正确的错误信息
    (BadRequest, 'my badrequest message'),
    (CustomException, 'my customexception message'),

    # 测试是否成功屏蔽了未授权情况下弹出的登录框
    (Unauthorized, 'my unauthorized message')
]