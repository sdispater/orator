# -*- coding: utf-8 -*-

from .table import Table
from .column import Column


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

        cursor = self._connection.get_connection().cursor()
        table_indexes = cursor.execute(sql).fetchall()

        return table_indexes

    def list_table_foreign_keys(self, table):
        sql = self._platform.get_list_table_foreign_keys_sql(table)

        cursor = self._connection.get_connection().cursor()
        cursor.execute(sql)
        table_foreign_keys = cursor.fetchall()

        return table_foreign_keys

    def list_table_details(self, table_name):
        columns = self.list_table_columns(table_name)

        foreign_keys = {}
        if self._platform.supports_foreign_key_constraints():
            foreign_keys = self.list_table_foreign_keys(table_name)

        #indexes = self.list_table_indexes(table_name)

        return Table(table_name, columns, [], foreign_keys)

    def _get_portable_table_columns_list(self, table, table_columns):
        columns_list = {}

        for table_column in table_columns:
            column = self._get_portable_table_column_definition(table_column)

            if column:
                name = column.get_name().lower()
                columns_list[name] = column

        return columns_list

    def _get_portable_table_column_definition(self, table_column):
        raise NotImplementedError

    def get_database_platform(self):
        raise NotImplementedError
