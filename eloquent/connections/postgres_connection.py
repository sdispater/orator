# -*- coding: utf-8 -*-

from .connection import Connection
from ..query.grammars.postgres_grammar import PostgresQueryGrammar
from ..query.processors.postgres_processor import PostgresQueryProcessor


class PostgresConnection(Connection):

    def get_default_query_grammar(self):
        return PostgresQueryGrammar()

    def get_default_post_processor(self):
        return PostgresQueryProcessor()
