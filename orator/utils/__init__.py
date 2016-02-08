# -*- coding: utf-8 -*-

import sys
import os
import errno
import warnings
import functools

PY2 = sys.version_info[0] == 2
PY3K = sys.version_info[0] >= 3
PY33 = sys.version_info >= (3, 3)

if PY2:
    import imp

    long = long
    unicode = unicode
    basestring = basestring

    reduce = reduce

    from urllib import quote_plus, unquote_plus, quote, unquote
    from urlparse import parse_qsl

    def load_module(module, path):
        with open(path, 'rb') as fh:
            mod = imp.load_source(module, path, fh)

            return mod
else:
    long = int
    unicode = str
    basestring = str

    from functools import reduce

    from urllib.parse import (quote_plus, unquote_plus,
                              parse_qsl, quote, unquote)

    if PY33:
        from importlib import machinery

        def load_module(module, path):
            return machinery.SourceFileLoader(
                module, path
            ).load_module(module)
    else:
        import imp

        def load_module(module, path):
            with open(path, 'rb') as fh:
                mod = imp.load_source(module, path, fh)

                return mod


class Null(object):

    def __bool__(self):
        return False

    def __eq__(self, other):
        return other is None


def deprecated(func):
    '''This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used.'''

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        if PY3K:
            func_code = func.__code__
        else:
            func_code = func.func_code

        warnings.warn_explicit(
            "Call to deprecated function {}.".format(func.__name__),
            category=DeprecationWarning,
            filename=func_code.co_filename,
            lineno=func_code.co_firstlineno + 1
        )

        return func(*args, **kwargs)

    return new_func


def decode(string, encodings=None):
    if not PY2 and not isinstance(string, bytes):
        return string

    if PY2 and isinstance(string, unicode):
        return string

    if encodings is None:
        encodings = ['utf-8', 'latin1', 'ascii']

    for encoding in encodings:
        try:
            return string.decode(encoding)
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass

    return string.decode(encodings[0], errors='ignore')


def encode(string, encodings=None):
    if not PY2 and isinstance(string, bytes):
        return string

    if PY2 and isinstance(string, str):
        return string

    if encodings is None:
        encodings = ['utf-8', 'latin1', 'ascii']

    for encoding in encodings:
        try:
            return string.encode(encoding)
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass

    return string.encode(encodings[0], errors='ignore')


def mkdir_p(path, mode=0o777):
    try:
        os.makedirs(path, mode)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def value(val):
    if callable(val):
        return val()

    return val


def data_get(target, key, default=None):
    """
    Get an item from a list, a dict or an object using "dot" notation.

    :param target: The target element
    :type target: list or dict or object

    :param key: The key to get
    :type key: string or list

    :param default: The default value
    :type default: mixed

    :rtype: mixed
    """
    from ..support import Collection

    if key is None:
        return target

    if not isinstance(key, list):
        key = key.split('.')

    for segment in key:
        if isinstance(target, (list, tuple)):
            try:
                target = target[segment]
            except IndexError:
                return value(default)
        elif isinstance(target, dict):
            try:
                target = target[segment]
            except IndexError:
                return value(default)
        elif isinstance(target, Collection):
            try:
                target = target[segment]
            except IndexError:
                return value(default)
        else:
            try:
                target = getattr(target, segment)
            except AttributeError:
                return value(default)

    return target
