# -*- coding: utf-8 -*-

from ..utils import PY2
from .connection import Connection
from ..query.grammars.mysql_grammar import MySQLQueryGrammar
from ..query.processors.mysql_processor import MySQLQueryProcessor
from ..schema.grammars import MySQLSchemaGrammar
from ..schema import MySQLSchemaBuilder
from ..dbal.mysql_schema_manager import MySQLSchemaManager


class MySQLConnection(Connection):

    name = 'mysql'

    def get_default_query_grammar(self):
        return MySQLQueryGrammar(marker=self._marker)

    def get_default_post_processor(self):
        return MySQLQueryProcessor()

    def get_schema_builder(self):
        """
        Return the underlying schema builder.

        :rtype: orator.schema.SchemaBuilder
        """
        if not self._schema_grammar:
            self.use_default_schema_grammar()

        return MySQLSchemaBuilder(self)

    def get_default_schema_grammar(self):
        return self.with_table_prefix(MySQLSchemaGrammar(self))

    def get_schema_manager(self):
        return MySQLSchemaManager(self)

    def begin_transaction(self):
        self._connection.autocommit(False)

        super(MySQLConnection, self).begin_transaction()

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
            return super(MySQLConnection, self)._get_cursor_query(query, bindings)

        if PY2:
            return self._cursor._last_executed.decode()

        return self._cursor._last_executed
