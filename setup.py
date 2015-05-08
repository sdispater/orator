# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages


def get_version():
    basedir = os.path.dirname(__file__)
    with open(os.path.join(basedir, 'eloquent/version.py')) as f:
        variables = {}
        exec(f.read(), variables)

        version = variables.get('VERSION')
        if version:
            return version

    raise RuntimeError('No version info found.')


__version__ = get_version()

setup(
    name='eloquent',
    license='MIT',
    version=__version__,
    description='The Eloquent ORM provides a simple yet beautiful ActiveRecord implementation.',
    long_description=open('README.rst').read(),
    author='Sébastien Eustace',
    author_email='sebastien.eustace@gmail.com',
    url='https://github.com/sdispater/eloquent',
    download_url='https://github.com/sdispater/eloquent/archive/%s.tar.gz' % __version__,
    packages=find_packages(),
    install_requires=['simplejson', 'arrow', 'inflection', 'six'],
    tests_require=['pytest', 'mock', 'flexmock'],
    test_suite='nose.collector',
    scripts=['bin/eloquent'],
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
