# -*- coding: utf-8 -*-

from .table import Table
from .identifier import Identifier


class TableDiff(object):

    def __init__(self, table_name, added_columns=None,
                 changed_columns=None, removed_columns=None, added_indexes=None,
                 changed_indexes=None, removed_indexes=None, from_table=None):
        self.name = table_name
        self.new_name = False
        self.added_columns = added_columns or {}
        self.changed_columns = changed_columns or {}
        self.removed_columns = removed_columns or {}
        self.added_indexes = added_indexes or []
        self.changed_indexes = changed_indexes or []
        self.removed_indexes = removed_indexes or []
        self.added_foreign_keys = []
        self.changed_foreign_keys = []
        self.removed_foreign_keys = []
        self.renamed_columns = {}
        self.renamed_indexes = {}
        self.from_table = from_table

    def get_name(self, platform):
        if isinstance(self.from_table, Table):
            name = self.from_table.get_quoted_name(platform)
        else:
            name = self.name

        return Identifier(name)

    def get_new_name(self):
        if self.new_name:
            return Identifier(self.new_name)

        return self.new_name
