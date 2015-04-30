#! /usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='Flask-RESTful-extend',
    version='0.3.4',
    url='https://github.com/anjianshi/flask-restful-extend',
    license='MIT',
    author='anjianshi',
    author_email='anjianshi@gmail.com',
    description="Improve Flask-RESTFul's behavior. Add some new features.",
    packages=['flask_restful_extend'],
    zip_safe=False,
    platforms='any',
    install_requires=['Flask>=0.10', 'Flask-RESTful>=0.3', 'Flask-SQLAlchemy', "six", "json_encode_manager"],
    keywords=['flask', 'python', 'rest', 'api'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
    ],
)
