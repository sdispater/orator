# -*- coding: utf-8 -*-


class QueryException(Exception):

    def __init__(self, sql, bindings, previous):
        self.sql = sql
        self.bindings = bindings
        self.previous = previous
        self.message = self.format_message(sql, bindings, previous)

    def format_message(self, sql, bindings, previous):
        return '%s (SQL: %s (%s))' % (str(previous), sql, bindings)

    def __repr__(self):
        return self.message

    def __str__(self):
        return self.message
