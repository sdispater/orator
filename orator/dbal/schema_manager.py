# -*- coding: utf-8 -*-

from collections import OrderedDict
from .table import Table
from .column import Column
from .index import Index


class SchemaManager(object):

    def __init__(self, connection, platform=None):
        """
        :param connection: The connection to use
        :type connection: orator.connection.Connection

        :param platform: The platform
        :type platform: orator.dbal.platforms.Platform
        """
        self._connection = connection

        if not platform:
            self._platform = self._connection.get_database_platform()
        else:
            self._platform = platform

    def list_table_columns(self, table):
        sql = self._platform.get_list_table_columns_sql(table)

        cursor = self._connection.get_connection().cursor()
        cursor.execute(sql)
        table_columns = map(lambda x: dict(x.items()), cursor.fetchall())

        return self._get_portable_table_columns_list(table, table_columns)

    def list_table_indexes(self, table):
        sql = self._platform.get_list_table_indexes_sql(table)

        table_indexes = self._connection.select(sql)

        return self._get_portable_table_indexes_list(table_indexes, table)

    def list_table_foreign_keys(self, table):
        sql = self._platform.get_list_table_foreign_keys_sql(table)

        table_foreign_keys = self._connection.select(sql)

        return self._get_portable_table_foreign_keys_list(table_foreign_keys)

    def list_table_details(self, table_name):
        columns = self.list_table_columns(table_name)

        foreign_keys = []
        if self._platform.supports_foreign_key_constraints():
            foreign_keys = self.list_table_foreign_keys(table_name)

        indexes = self.list_table_indexes(table_name)

        table = Table(table_name, columns, indexes, foreign_keys)

        return table

    def _get_portable_table_columns_list(self, table, table_columns):
        columns_list = OrderedDict()

        for table_column in table_columns:
            column = self._get_portable_table_column_definition(table_column)

            if column:
                name = column.get_name().lower()
                columns_list[name] = column

        return columns_list

    def _get_portable_table_column_definition(self, table_column):
        raise NotImplementedError

    def _get_portable_table_indexes_list(self, table_indexes, table_name):
        result = OrderedDict()

        for table_index in table_indexes:
            index_name = table_index['key_name']
            key_name = table_index['key_name']
            if table_index['primary']:
                key_name = 'primary'

            key_name = key_name.lower()

            if key_name not in result:
                options = {}
                if 'where' in table_index:
                    options['where'] = table_index['where']

                result[key_name] = {
                    'name': index_name,
                    'columns': [table_index['column_name']],
                    'unique': not table_index['non_unique'],
                    'primary': table_index['primary'],
                    'flags': table_index.get('flags') or None,
                    'options': options
                }
            else:
                result[key_name]['columns'].append(table_index['column_name'])

        indexes = OrderedDict()
        for index_key, data in result.items():
            index = Index(
                data['name'], data['columns'],
                data['unique'], data['primary'],
                data['flags'], data['options']
            )

            indexes[index_key] = index

        return indexes

    def _get_portable_table_foreign_keys_list(self, table_foreign_keys):
        foreign_keys = []
        for value in table_foreign_keys:
            value = self._get_portable_table_foreign_key_definition(value)
            if value:
                foreign_keys.append(value)

        return foreign_keys

    def _get_portable_table_foreign_key_definition(self, table_foreign_key):
        return table_foreign_key

    def get_database_platform(self):
        return self._connection.get_database_platform()
