# -*- coding: utf-8 -*-

from .identifier import Identifier


class ColumnDiff(object):

    def __init__(self, old_column_name, column, changed_properties=None, from_column=None):
        self.old_column_name = old_column_name
        self.column = column
        self.changed_properties = changed_properties
        self.from_column = from_column

    def has_changed(self, property_name):
        return property_name in self.changed_properties

    def get_old_column_name(self):
        return Identifier(self.old_column_name)
