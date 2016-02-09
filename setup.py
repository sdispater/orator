# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages


def get_version():
    basedir = os.path.dirname(__file__)
    with open(os.path.join(basedir, 'orator/version.py')) as f:
        variables = {}
        exec(f.read(), variables)

        version = variables.get('VERSION')
        if version:
            return version

    raise RuntimeError('No version info found.')


__version__ = get_version()

setup(
    name='orator',
    license='MIT',
    version=__version__,
    description='The Orator ORM provides a simple yet beautiful ActiveRecord implementation.',
    long_description=open('README.rst').read(),
    entry_points={
        'console_scripts': ['orator=orator.commands.application:application.run'],
    },
    author='Sébastien Eustace',
    author_email='sebastien.eustace@gmail.com',
    url='https://github.com/sdispater/orator',
    download_url='https://github.com/sdispater/orator/archive/%s.tar.gz' % __version__,
    packages=find_packages(exclude=['tests']),
    install_requires=[
        'simplejson',
        'arrow',
        'inflection',
        'six',
        'cleo>=0.4.1',
        'blinker',
        'lazy-object-proxy',
        'fake-factory',
        'wrapt',
        'pyaml'
    ],
    tests_require=['pytest', 'mock', 'flexmock==0.9.7'],
    test_suite='nose.collector',
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
