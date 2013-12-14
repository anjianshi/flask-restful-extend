# -*- coding: utf-8 -*-
from flask.ext import restful


class ErrorHandledApi(restful.Api):
    def handle_error(self, e):
        """
        解决报错信息不会被输出到客户端的问题

        python 标准的 exception 格式为(与此问题无关，仅作为参考)：
            message: error message

        werkzeug 的 HTTPException (包括 BadRequest 等)的格式为：
            code: http code
            name: str(e) 时输出的字符串
            description: error message

        flask_restful 的 handle_error 函数支持的格式为：
            code: http code
            data: ｛
            　　　　message: error message
            ｝

        此函数能把 werkzeug 的 HTTPException 和带 code 属性的标准 python exception
        改写成 flask_restful 能识别的形式
        """
        if hasattr(e, 'description'):
            e.data = dict(message=e.description)
        elif hasattr(e, 'code') and hasattr(e, 'message') and not hasattr(e, 'data'):
            e.data = dict(message=e.message)
        return super(ErrorHandledApi, self).handle_error(e)

    def unauthorized(self, response):
        """对于未授权的请求，只返回 403，不弹出登录对话框"""
        return response