# -*- coding: utf-8 -*-

from ..utils import PY2
from .connection import Connection
from ..query.grammars.mysql_grammar import MySqlQueryGrammar
from ..query.processors.mysql_processor import MySqlQueryProcessor
from ..schema.grammars import MySqlSchemaGrammar
from ..schema import MySqlSchemaBuilder
from ..dbal.platforms.mysql_platform import MySqlPlatform
from ..dbal.mysql_schema_manager import MySqlSchemaManager


class MySqlConnection(Connection):

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
        return self.with_table_prefix(MySqlSchemaGrammar())

    def get_database_platform(self):
        return MySqlPlatform()

    def get_schema_manager(self):
        return MySqlSchemaManager(self)

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
