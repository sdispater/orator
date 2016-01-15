# -*- coding: utf-8 -*-

from ..utils import PY2
from .connection import Connection
from ..query.grammars.mysql_grammar import MySqlQueryGrammar
from ..query.processors.mysql_processor import MySqlQueryProcessor
from ..schema.grammars import MySqlSchemaGrammar
from ..schema import MySqlSchemaBuilder
from ..dbal.mysql_schema_manager import MySQLSchemaManager


class MySqlConnection(Connection):

    name = 'mysql'

    def get_default_query_grammar(self):
        return MySqlQueryGrammar()

    def get_default_post_processor(self):
        return MySqlQueryProcessor()

    def get_schema_builder(self):
        """
        Retturn the underlying schema builder.

        :rtype: orator.schema.SchemaBuilder
        """
        if not self._schema_grammar:
            self.use_default_schema_grammar()

        return MySqlSchemaBuilder(self)

    def get_default_schema_grammar(self):
        return self.with_table_prefix(MySqlSchemaGrammar(self))

    def get_schema_manager(self):
        return MySQLSchemaManager(self)

    def begin_transaction(self):
        self._connection.autocommit(False)

        super(MySqlConnection, self).begin_transaction()

    def commit(self):
        if self._transactions == 1:
            self._connection.commit()
            self._connection.autocommit(True)

        self._transactions -= 1

    def rollback(self):
        if self._transactions == 1:
            self._transactions = 0

            self._connection.rollback()
            self._connection.autocommit(True)
        else:
            self._transactions -= 1

    def _get_cursor_query(self, query, bindings):
        if not hasattr(self._cursor, '_last_executed') or self._pretending:
            return super(MySqlConnection, self)._get_cursor_query(query, bindings)

        if PY2:
            return self._cursor._last_executed

        return self._cursor._last_executed.decode()

    def get_server_version(self):
        tuple_version = self._connection._server_version

        return tuple_version[:2]
