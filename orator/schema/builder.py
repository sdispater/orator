# -*- coding: utf-8 -*-

from contextlib import contextmanager
from .blueprint import Blueprint


class SchemaBuilder(object):
    def __init__(self, connection):
        """
        :param connection: The schema connection
        :type connection: orator.connections.Connection
        """
        self._connection = connection
        self._grammar = connection.get_schema_grammar()

    def has_table(self, table):
        """
        Determine if the given table exists.

        :param table: The table
        :type table: str

        :rtype: bool
        """
        sql = self._grammar.compile_table_exists()

        table = self._connection.get_table_prefix() + table

        return len(self._connection.select(sql, [table])) > 0

    def has_column(self, table, column):
        """
        Determine if the given table has a given column.

        :param table: The table
        :type table: str

        :type column: str

        :rtype: bool
        """
        column = column.lower()

        return column in list(map(lambda x: x.lower(), self.get_column_listing(table)))

    def get_column_listing(self, table):
        """
        Get the column listing for a given table.

        :param table: The table
        :type table: str

        :rtype: list
        """
        table = self._connection.get_table_prefix() + table

        results = self._connection.select(self._grammar.compile_column_exists(table))

        return self._connection.get_post_processor().process_column_listing(results)

    @contextmanager
    def table(self, table):
        """
        Modify a table on the schema.

        :param table: The table
        """
        try:
            blueprint = self._create_blueprint(table)

            yield blueprint
        except Exception as e:
            raise

        try:
            self._build(blueprint)
        except Exception:
            raise

    @contextmanager
    def create(self, table):
        """
        Create a new table on the schema.

        :param table: The table
        :type table: str

        :rtype: Blueprint
        """
        try:
            blueprint = self._create_blueprint(table)
            blueprint.create()

            yield blueprint
        except Exception as e:
            raise

        try:
            self._build(blueprint)
        except Exception:
            raise

    def drop(self, table):
        """
        Drop a table from the schema.

        :param table: The table
        :type table: str
        """
        blueprint = self._create_blueprint(table)

        blueprint.drop()

        self._build(blueprint)

    def drop_if_exists(self, table):
        """
        Drop a table from the schema.

        :param table: The table
        :type table: str
        """
        blueprint = self._create_blueprint(table)

        blueprint.drop_if_exists()

        self._build(blueprint)

    def rename(self, from_, to):
        """
        Rename a table on the schema.
        """
        blueprint = self._create_blueprint(from_)

        blueprint.rename(to)

        self._build(blueprint)

    def _build(self, blueprint):
        """
        Execute the blueprint to build / modify the table.

        :param blueprint: The blueprint
        :type blueprint: orator.schema.Blueprint
        """
        blueprint.build(self._connection, self._grammar)

    def _create_blueprint(self, table):
        return Blueprint(table)

    def get_connection(self):
        return self._connection

    def set_connection(self, connection):
        self._connection = connection

        return self
