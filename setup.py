#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from pathlib import Path


def load_version():
    version = {}
    with open(str(here / NAME / '__version__.py'), 'r') as fp:
        exec(fp.read(), version)
    return version['__version__']


here = Path(__file__).absolute().parent

NAME = 'dicewars'
VERSION = load_version()
PACKAGES = find_packages()

setup(
    name=NAME,
    version=VERSION,
    description='Backend for DiceWars games',
    author='Thomas Schott',
    author_email='scotty@c-base.org',
    python_requires='>=3.7',
    packages=PACKAGES,
)
