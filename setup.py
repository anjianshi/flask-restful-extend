#! /usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import os
import sys
import flask_restful_extend

setup(
    name='Flask-RESTful-extend',
    version=flask_restful_extend.__version__,
    url='https://github.com/anjianshi/flask-restful-extend',
    license='MIT',
    author='anjianshi',
    author_email='anjianshi@gmail.com',
    description='extend flask-restfurl and fix some unreasonable behave',
    packages=['flask_restful_extend'],
    zip_safe=False,
    platforms='any',
    install_requires=['Flask>=0.8'],
    keywords=['flask', 'python', 'rest', 'api'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
    ],
)