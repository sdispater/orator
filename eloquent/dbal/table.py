# -*- coding: utf-8 -*-

from collections import OrderedDict
from .column import Column


class Table(object):

    def __init__(self, table_name, columns=None, indexes=None, fk_constraints=None):
        self._name = table_name
        self._columns = OrderedDict()
        self._indexes = {}
        self._fk_constraints = {}

        columns = columns or []
        indexes = indexes or []
        fk_constraints = fk_constraints or []

        columns = columns.values() if isinstance(columns, dict) else columns
        for column in columns:
            self._add_column(column)

        for index in indexes:
            self._add_index(index)

        for constraint in fk_constraints:
            self._add_foreign_key_constraint(constraint)

    def get_columns(self):
        columns = self._columns

        return columns

    def has_column(self, column):
        return column in self._columns

    def get_column(self, column):
        if self.has_column(column):
            return self._columns[column]

    def change_column(self, column_name, options):
        column = self.get_column(column_name)
        column.set_options(options)

        return self

    def _add_column(self, column):
        column_name = column.get_name()

        if column_name in self._columns:
            raise Exception('Column %s already exists.' % column_name)

        self._columns[column_name] = column

    def _add_index(self, index):
        index_name = index['name']

        self._indexes[index_name] = index

    def _add_foreign_key_constraint(self, constraint):
        name = constraint['name']

        self._fk_constraints[name] = constraint

    def get_name(self):
        return self._name

    def clone(self):
        columns = []

        for column in self._columns.values():
            columns.append(Column(column.get_name(), column.get_type(), column.to_dict()))

        table = Table(self._name, columns)

        return table
