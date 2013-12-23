# -*- coding: utf-8 -*-
from werkzeug.exceptions import BadRequest, Unauthorized


class CustomException(Exception):
    code = 500


class CustomException2(BadRequest):
    def __init__(self, data):
        self.data = dict(message=data)


exception_data_list = [
    # 测试能否正常处理各种异常，并输出正确的错误信息
    # HTTPException
    (BadRequest, 'my badrequest message'),
    # 带 code 属性的标准 Python
    (CustomException, 'my customexception message'),
    # 既带 data 属性，又带 description 属性的异常（实际是个 HTTPException 添加了一个 data 属性）
    # 如果在 reqparse.Argument 调用用户指定的构造器对参数值进行转换的途中，抛出了 TypeError 以外的异常，
    # 且 arg 的 ignore 属性为 False，它就会被转换成这种特殊的异常。
    # 具体步骤是：
    #   Argument.parse() 捕获原始异常，将其传给 handle_validation_error()
    #   然后这个函数将它转换成字符串形式的 error_msg，再交给 flask_restful.abort()
    #   abort() 函数先构造一个 HTTPException，然后把它的 data 属性的值设为 error_msg，最终将此异常抛出
    #   由用户指定的错误处理函数把结果告知客户端
    (CustomException2, 'real message'),

    # 测试是否成功屏蔽了未授权情况下弹出的登录框
    (Unauthorized, 'my unauthorized message')
]