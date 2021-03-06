#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from pathlib import Path


def load_version():
    version = {}
    with open(str(here / NAME / '__version__.py'), 'r') as fp:
        exec(fp.read(), version)
    return version['__version__']


def load_readme():
    with open(str(here / 'README.md'), 'r') as fp:
        readme = fp.read()
    return readme, 'text/markdown'


here = Path(__file__).absolute().parent

NAME = 'dicewars'
VERSION = load_version()
LONG_DESC, LONG_DESC_CONTENT_TYPE = load_readme()
CLASSIFIERS = [
    'Topic :: Games/Entertainment :: Board Games',
    'Intended Audience :: Developers',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 3 :: Only',
    'Development Status :: 4 - Beta',
    'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
]
PACKAGES = find_packages()

setup(
    name=NAME,
    version=VERSION,
    description='Backend for DiceWars games/servers',
    long_description=LONG_DESC,
    long_description_content_type=LONG_DESC_CONTENT_TYPE,
    author='Thomas Schott',
    author_email='scotty@c-base.org',
    url='https://github.com/scotty007/dicewars',
    classifiers=CLASSIFIERS,
    python_requires='>=3.7',
    packages=PACKAGES,
)
