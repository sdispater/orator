# -*- coding: utf-8 -*-

import sys
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


from .helpers import mkdir_p, value


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
