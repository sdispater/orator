# -*- coding: utf-8 -*-

import sys

PY2 = sys.version_info[0] == 2

if PY2:
    long = long
    unicode = unicode
    basestring = basestring

    from urllib import quote_plus, unquote_plus, quote, unquote
    from urlparse import parse_qsl
else:
    long = int
    unicode = str
    basestring = str

    from urllib.parse import (quote_plus, unquote_plus,
                              parse_qsl, quote, unquote)


class Null(object):

    def __bool__(self):
        return False

    def __eq__(self, other):
        return other is None
