# -*- coding: utf-8 -*-

from __future__ import division
from ..utils import PY2
from .connection import Connection, run
from ..query.grammars.postgres_grammar import PostgresQueryGrammar
from ..query.processors.postgres_processor import PostgresQueryProcessor
from ..schema.grammars import PostgresSchemaGrammar
from ..dbal.postgres_schema_manager import PostgresSchemaManager


class PostgresConnection(Connection):

    name = 'pgsql'

    def get_default_query_grammar(self):
        return PostgresQueryGrammar(marker=self._marker)

    def get_default_post_processor(self):
        return PostgresQueryProcessor()

    def get_default_schema_grammar(self):
        return self.with_table_prefix(PostgresSchemaGrammar(self))

    def get_schema_manager(self):
        return PostgresSchemaManager(self)

    @run
    def statement(self, query, bindings=None):
        if self.pretending():
            return True

        bindings = self.prepare_bindings(bindings)

        self._new_cursor().execute(query, bindings)

        return True

    def begin_transaction(self):
        self._connection.autocommit = False

        super(PostgresConnection, self).begin_transaction()

    def commit(self):
        if self._transactions == 1:
            self._connection.commit()
            self._connection.autocommit = True

        self._transactions -= 1

    def rollback(self):
        if self._transactions == 1:
            self._transactions = 0

            self._connection.rollback()
            self._connection.autocommit = True
        else:
            self._transactions -= 1

    def _get_cursor_query(self, query, bindings):
        if self._pretending:
            if PY2:
                return self._cursor.mogrify(query, bindings)

            return self._cursor.mogrify(query, bindings).decode()

        if not hasattr(self._cursor, 'query'):
            return super(PostgresConnection, self)._get_cursor_query(query, bindings)

        if PY2:
            return self._cursor.query

        return self._cursor.query.decode()
