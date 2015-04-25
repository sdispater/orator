# -*- coding: utf-8 -*-

from ..query.expression import QueryExpression


class Grammar(object):

    def __init__(self):
        self._table_prefix = ''

    def wrap_list(self, values):
        return map(self.wrap, values)

    def wrap_table(self, table):
        if self.is_expression(table):
            return self.get_value(table)

        return self.wrap(self._table_prefix + table, True)

    def wrap(self, value, prefix_alias=False):
        if self.is_expression(value):
            return self.get_value(value)

        # If the value being wrapped has a column alias we will need
        # to separate out the pieces so we can wrap each of the segments
        # of the expression on it own, and then joins them
        # both back together with the "as" connector.
        if value.lower().find(' as ') >= 0:
            segments = value.split(' ')

            if prefix_alias:
                segments[2] = self._table_prefix + segments[2]

            return '%s AS %s' % (self.wrap(segments[0]),
                                 self._wrap_value(segments[2]))

        wrapped = []

        segments = value.split('.')

        # If the value is not an aliased table expression, we'll just wrap it like
        # normal, so if there is more than one segment, we will wrap the first
        # segments as if it was a table and the rest as just regular values.
        for key, segment in enumerate(segments):
            if key == 0 and len(segments) > 1:
                wrapped.append(self.wrap_table(segment))
            else:
                wrapped.append(self._wrap_value(segment))

        return '.'.join(wrapped)

    def _wrap_value(self, value):
        if value == '*':
            return value

        return '"%s"' % value.replace('"', '""')

    def columnize(self, columns):
        return ', '.join(map(self.wrap, columns))

    def parameterize(self, values):
        return ', '.join(map(self.parameter, values))

    def parameter(self, value):
        if self.is_expression(value):
            return self.get_value(value)

        return self.get_marker()

    def get_value(self, expression):
        return expression.get_value()

    def is_expression(self, value):
        return isinstance(value, QueryExpression)

    def get_date_format(self):
        return 'Y-m-d H:i:s'

    def get_table_prefix(self):
        return self._table_prefix

    def set_table_prefix(self, prefix):
        self._table_prefix = prefix

        return self

    def get_marker(self):
        return '?'
