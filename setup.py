#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

from setuptools import setup


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


def get_long_description(long_description_file):
    """
    Read long description from file.
    """
    with open(long_description_file, encoding='utf-8') as f:
        long_description = f.read()

    return long_description


version = get_version('apistar_websocket')


setup(
    name='apistar-websocket',
    version=version,
    url='https://github.com/jeffbuttars/apistar-websocket',
    license='Apache License 2.0',
    description='WebSocket Component for API Star',
    long_description=get_long_description('README.md'),
    long_description_content_type='text/markdown',
    author='Jeff Buttars',
    author_email='jeff@jeffbuttars.com',
    install_requires=[
        'apistar',
        'uvicorn',
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
