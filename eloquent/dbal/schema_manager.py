# -*- coding: utf-8 -*-

from .table import Table
from .column import Column


class SchemaManager(object):

    def __init__(self, connection, platform=None):
        """
        :param connection: The connection to use
        :type connection: eloquent.connection.Connection

        :param platform: The platform
        :type platform: eloquent.dbal.platforms.Platform
        """
        self._connection = connection
        if not platform:
            self._platform = self._connection.get_database_platform()
        else:
            self._platform = platform

    def list_table_columns(self, table):
        sql = self._platform.get_list_table_columns_sql(table)

        cursor = self._connection.get_connection().cursor()
        options = self._platform.get_column_options()
        table_columns = []
        for column_info in cursor.execute(sql).fetchall():
            column = Column(column_info['name'], column_info['type'], column_info)

            column.set_platform_options({x: column_info[x] for x in options})

            table_columns.append(column)

        return table_columns

    def list_table_indexes(self, table):
        sql = self._platform.get_list_table_indexes_sql(table)

        cursor = self._connection.get_connection().cursor()
        table_indexes = cursor.execute(sql).fetchall()

        return table_indexes

    def list_table_foreign_keys(self, table):
        sql = self._platform.get_list_table_foreign_keys_sql(table)

        cursor = self._connection.get_connection().cursor()
        table_foreign_keys = cursor.execute(sql).fetchall()

        return table_foreign_keys

    def list_table_details(self, table_name):
        columns = self.list_table_columns(table_name)

        foreign_keys = {}
        if self._platform.supports_foreign_key_constraints():
            foreign_keys = self.list_table_foreign_keys(table_name)

        indexes = self.list_table_indexes(table_name)

        return Table(table_name, columns, indexes, foreign_keys)

    def get_database_platform(self):
        raise NotImplementedError
