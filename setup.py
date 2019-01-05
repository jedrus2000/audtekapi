# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from setuptools import find_packages, setup


def get_version(filename):
    with open(filename) as fh:
        metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", fh.read()))
        return metadata['version']


setup(
    name='audtekapi',
    version=get_version('audtekapi/__init__.py'),
    url='https://github.com/jedrus2000/audtekapi',
    license='Apache License, Version 2.0',
    author=u'Andrzej Bargański',
    author_email='a.barganski@gmail.com',
    description='Unofficial API for Audioteka',
    long_description=open('README.rst').read(),
    packages=find_packages(exclude=['tests', 'tests.*']),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'setuptools',
        'requests >= 2.21.0',
    ],
    classifiers=[
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Multimedia :: Sound/Audio',
    ],
)
