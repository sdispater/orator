# -*- coding: utf-8 -*-

import sys

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


def decode(s, encodings=('utf8', 'ascii', 'latin1')):
    if not PY2:
        return s

    for encoding in encodings:
        try:
            return s.decode(encoding)
        except UnicodeDecodeError:
            pass

    return s.decode('utf8', 'ignore')
