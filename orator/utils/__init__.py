# -*- coding: utf-8 -*-

import sys
import os
import errno

PY2 = sys.version_info[0] == 2
PY3K = sys.version_info[0] >= 3
PY33 = sys.version_info >= (3, 3)

if PY2:
    import imp

    long = long
    unicode = unicode
    basestring = basestring

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


def decode(string, encodings=None):
    if not PY2 and not isinstance(string, bytes):
        return string

    if encodings is None:
        encodings = ['utf-8', 'latin1', 'ascii']

    for encoding in encodings:
        try:
            return string.decode(encoding)
        except UnicodeDecodeError:
            pass

    return string.decode(encodings[0], errors='ignore')


def encode(string, encodings=None):
    if not PY2 and isinstance(string, bytes):
        return string

    if PY2 and isinstance(string, unicode):
        return string

    if encodings is None:
        encodings = ['utf-8', 'latin1', 'ascii']

    for encoding in encodings:
        try:
            return string.encode(encoding)
        except UnicodeDecodeError:
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
