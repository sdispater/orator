# -*- coding: utf-8 -*-

from .builder import SchemaBuilder


class MySQLSchemaBuilder(SchemaBuilder):

    def has_table(self, table):
        """
        Determine if the given table exists.

        :param table: The table
        :type table: str

        :rtype: bool
        """
        sql = self._grammar.compile_table_exists()
        database = self._connection.get_database_name()
        table = self._connection.get_table_prefix() + table

        return len(self._connection.select(sql, [database, table])) > 0

    def get_column_listing(self, table):
        """
        Get the column listing for a given table.

        :param table: The table
        :type table: str

        :rtype: list
        """
        sql = self._grammar.compile_column_exists()
        database = self._connection.get_database_name()
        table = self._connection.get_table_prefix() + table

        results = self._connection.select(sql, [database, table])

        return self._connection.get_post_processor().process_column_listing(results)
