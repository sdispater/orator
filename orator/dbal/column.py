# -*- coding: utf-8 -*-

from .abstract_asset import AbstractAsset
from ..utils import basestring


class Column(AbstractAsset):

    def __init__(self, name, type, options=None):
        self._set_name(name)
        self._type = type

        self._length = None
        self._precision = 10
        self._scale = 0
        self._unsigned = False
        self._fixed = False
        self._notnull = True
        self._default = None
        self._autoincrement = False
        self._extra = {}
        self._platform_options = {}

        self.set_options(options or {})

    def set_options(self, options):
        for key, value in options.items():
            method = 'set_%s' % key
            if hasattr(self, method):
                getattr(self, method)(value)

        return self

    def set_platform_options(self, platform_options):
        self._platform_options = platform_options

        return self

    def set_platform_option(self, name, value):
        self._platform_options[name] = value

        return self

    def get_platform_options(self):
        return self._platform_options

    def has_platform_option(self, option):
        return option in self._platform_options

    def get_platform_option(self, option):
        return self._platform_options[option]

    def set_length(self, length):
        if length is not None:
            self._length = int(length)
        else:
            self._length = None

        return self

    def set_precision(self, precision):
        if precision is None or isinstance(precision, basestring) and not precision.isdigit():
            precision = 10

        self._precision = int(precision)

        return self

    def set_scale(self, scale):
        if scale is None or isinstance(scale, basestring) and not scale.isdigit():
            scale = 0

        self._scale = int(scale)

        return self

    def set_unsigned(self, unsigned):
        self._unsigned = bool(unsigned)

    def set_fixed(self, fixed):
        self._fixed = bool(fixed)

    def set_notnull(self, notnull):
        self._notnull = bool(notnull)

    def set_default(self, default):
        self._default = default

    def set_autoincrement(self, flag):
        self._autoincrement = flag

        return self

    def set_type(self, type):
        self._type = type

    def set_extra(self, extra, key=None):
        if key:
            self._extra[key] = extra
        else:
            self._extra = extra

    def get_name(self):
        return self._name

    def get_type(self):
        return self._type

    def get_extra(self, name=None):
        if name is not None:
            return self._extra[name]

        return self._extra

    def get_autoincrement(self):
        return self._autoincrement

    def get_notnull(self):
        return self._notnull

    def get_default(self):
        return self._default

    def to_dict(self):
        d = {
            'name': self._name,
            'type': self._type,
            'default': self._default,
            'notnull': self._notnull,
            'length': self._length,
            'precision': self._precision,
            'scale': self._scale,
            'fixed': self._fixed,
            'unsigned': self._unsigned,
            'autoincrement': self._autoincrement,
            'extra': self._extra
        }

        d.update(self._platform_options)

        return d


