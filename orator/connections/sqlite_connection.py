# -*- coding: utf-8 -*-

from ..utils import PY2, decode
from .connection import Connection
from ..query.processors.sqlite_processor import SQLiteQueryProcessor
from ..query.grammars.sqlite_grammar import SQLiteQueryGrammar
from ..schema.grammars.sqlite_grammar import SQLiteSchemaGrammar
from ..dbal.platforms.sqlite_platform import SQLitePlatform
from ..dbal.sqlite_schema_manager import SQLiteSchemaManager


class SQLiteConnection(Connection):

    def get_default_query_grammar(self):
        return self.with_table_prefix(SQLiteQueryGrammar())

    def get_default_post_processor(self):
        return SQLiteQueryProcessor()

    def get_default_schema_grammar(self):
        return self.with_table_prefix(SQLiteSchemaGrammar())

    def get_database_platform(self):
        return SQLitePlatform()

    def get_schema_manager(self):
        return SQLiteSchemaManager(self)

    def begin_transaction(self):
        self._connection.isolation_level = 'DEFERRED'

        super(SQLiteConnection, self).begin_transaction()

    def commit(self):
        if self._transactions == 1:
            self._connection.commit()
            self._connection.isolation_level = None

        self._transactions -= 1

    def rollback(self):
        if self._transactions == 1:
            self._transactions = 0

            self._connection.rollback()
            self._connection.isolation_level = None
        else:
            self._transactions -= 1

    def prepare_bindings(self, bindings):
        bindings = super(SQLiteConnection, self).prepare_bindings(bindings)

        if PY2:
            return map(lambda x: decode(x) if isinstance(x, str) else x, bindings)

        return bindings
