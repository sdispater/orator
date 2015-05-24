# -*- coding: utf-8 -*-


class QueryExpression(object):

    def __init__(self, value):
        self._value = value

    def get_value(self):
        return self._value

    def __str__(self):
        return str(self.get_value())
