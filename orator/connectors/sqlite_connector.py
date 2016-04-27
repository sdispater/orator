# -*- coding: utf-8 -*-

try:
    import sqlite3
except ImportError:
    sqlite3 = None

from .connector import Connector


class DictCursor(object):

    def __init__(self, cursor, row):
        self.dict = {}
        self.cursor = cursor

        for idx, col in enumerate(cursor.description):
            self.dict[col[0]] = row[idx]

    def __getattr__(self, item):
        try:
            return object.__getattribute__(self, item)
        except AttributeError:
            return getattr(self.cursor, item)

    def __getitem__(self, item):
        return self.dict[item]

    def items(self):
        return self.dict.items()


class SQLiteConnector(Connector):

    RESERVED_KEYWORDS = [
        'log_queries', 'driver', 'prefix', 'name',
        'foreign_keys'
    ]

    def connect(self, config):
        connection = self.get_api().connect(**self.get_config(config))
        connection.isolation_level = None
        connection.row_factory = DictCursor

        # We activate foreign keys support by default
        if config.get('foreign_keys', True):
            connection.execute("PRAGMA foreign_keys = ON")

        return connection

    def get_api(self):
        return sqlite3
