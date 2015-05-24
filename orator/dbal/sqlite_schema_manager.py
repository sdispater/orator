# -*- coding: utf-8 -*-

from .schema_manager import SchemaManager
from .platforms.sqlite_platform import SQLitePlatform
from .column import Column


class SQLiteSchemaManager(SchemaManager):

    def list_table_columns(self, table):
        sql = self._platform.get_list_table_columns_sql(table)

        cursor = self._connection.get_connection().cursor()
        options = self._platform.get_column_options()
        table_columns = []
        for column_info in cursor.execute(sql).fetchall():
            column_info = dict(column_info.items())
            column_info['default'] = column_info['dflt_value']

            column = Column(column_info['name'], column_info['type'], column_info)

            column.set_platform_options({x: column_info[x] for x in options})

            table_columns.append(column)

        return table_columns

    def list_table_indexes(self, table):
        sql = self._platform.get_list_table_indexes_sql(table)

        cursor = self._connection.get_connection().cursor()
        table_indexes = cursor.execute(sql).fetchall()

        indexes = []
        for index in table_indexes:
            table_index = dict(index.items())
            index_info = cursor.execute('PRAGMA index_info(%s)' % index['name']).fetchall()
            columns = []
            for column in index_info:
                columns.append(column['name'])

            table_index['columns'] = columns

            indexes.append(table_index)

        return indexes

    def get_database_platform(self):
        return SQLitePlatform()
