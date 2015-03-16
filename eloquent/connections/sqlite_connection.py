# -*- coding: utf-8 -*-

from .connection import Connection
from ..query.processors.sqlite_processor import SQLiteQueryProcessor


class SQLiteConnection(Connection):

    def get_default_post_processor(self):
        return SQLiteQueryProcessor()
