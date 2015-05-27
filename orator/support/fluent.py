# -*- coding: utf-8 -*-

import simplejson as json


class Fluent(object):

    def __init__(self, **attributes):
        self.__attributes = {}

        for key, value in attributes.items():
            self.__attributes[key] = value

    def get(self, key, default=None):
        return self.__attributes.get(key, default)

    def get_attributes(self):
        return self.__attributes

    def to_dict(self):
        return self.__attributes

    def to_json(self, **options):
        return json.dumps(self.to_dict(), **options)

    def __contains__(self, item):
        return item in self.__attributes

    def __getitem__(self, item):
        return self.__attributes[item]

    def __setitem__(self, key, value):
        self.__attributes[key] = value

    def __delitem__(self, key):
        del self.__attributes[key]

    def __dynamic(self, method):
        def call(*args, **kwargs):
            if len(args):
                self.__attributes[method] = args[0]
            else:
                self.__attributes[method] = True

            return self

        return call

    def __getattr__(self, item):
        if item in self.__attributes:
            return self.__attributes[item]

        return self.__dynamic(item)

    def __setattr__(self, key, value):
        if key.startswith(('_Fluent__', '_%s__' % self.__class__.__name__, '__')):
            super(Fluent, self).__setattr__(key, value)
        elif callable(getattr(self, key, None)):
            return super(Fluent, self).__setattr__(key, value)
        else:
            self.__attributes[key] = value

    def __delattr__(self, item):
        del self.__attributes[item]
