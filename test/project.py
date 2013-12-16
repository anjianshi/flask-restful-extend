# -*- coding: utf-8 -*-
from flask import Flask
import flask_restful_extend as restful_extend


app = Flask(__name__)

api = restful_extend.ErrorHandledApi(app)