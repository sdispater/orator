# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

__version__ = '0.4'

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
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
