# -*- coding: utf-8 -*-

import simplejson as json
from wrapt import ObjectProxy
from ..utils import value


class Dynamic(ObjectProxy):

    _key = None
    _fluent = None

    def __init__(self, value, key, fluent):
        super(Dynamic, self).__init__(value)

        self._key = key
        self._fluent = fluent

    def __call__(self, *args, **kwargs):
        if len(args):
            self.__set_value(args[0])
        else:
            self.__set_value(True)

        return self._fluent

    def __set_value(self, value):
        self._fluent._attributes[self._key] = value


class Fluent(object):

    def __init__(self, **attributes):
        self._attributes = {}

        for key, value in attributes.items():
            self._attributes[key] = value

    def get(self, key, default=None):
        return self._attributes.get(key, value(default))

    def get_attributes(self):
        return self._attributes

    def to_dict(self):
        return self.serialize()

    def serialize(self):
        return self._attributes

    def to_json(self, **options):
        return json.dumps(self.serialize(), **options)

    def __contains__(self, item):
        return item in self._attributes

    def __getitem__(self, item):
        return self._attributes[item]

    def __setitem__(self, key, value):
        self._attributes[key] = value

    def __delitem__(self, key):
        del self._attributes[key]

    def __dynamic(self, method):
        def call(*args, **kwargs):
            if len(args):
                self._attributes[method] = args[0]
            else:
                self._attributes[method] = True

            return self

        return call

    def __getattr__(self, item):
        return Dynamic(self._attributes.get(item), item, self)

    def __setattr__(self, key, value):
        if key == '_attributes':
            super(Fluent, self).__setattr__(key, value)

        try:
            super(Fluent, self).__getattribute__(key)

            return super(Fluent, self).__setattr__(key, value)
        except AttributeError:
            pass

        self._attributes[key] = value

    def __delattr__(self, item):
        del self._attributes[item]
