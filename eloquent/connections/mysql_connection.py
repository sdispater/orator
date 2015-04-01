# -*- coding: utf-8 -*-

from .connection import Connection
from ..query.grammars.mysql_grammar import MySqlQueryGrammar
from ..query.processors.mysql_processor import MySqlQueryProcessor


class MySqlConnection(Connection):

    def get_default_query_grammar(self):
        return MySqlQueryGrammar()

    def get_default_post_processor(self):
        return MySqlQueryProcessor()

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
        if not hasattr(self._cursor, '_last_executed'):
            return super(MySqlConnection, self)._get_cursor_query(query, bindings)

        return self._cursor._last_executed
