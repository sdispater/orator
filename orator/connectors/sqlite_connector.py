# -*- coding: utf-8 -*-

from pendulum import Pendulum

try:
    import sqlite3

    from sqlite3 import register_adapter

    register_adapter(Pendulum, lambda val: val.isoformat(' '))
except ImportError:
    sqlite3 = None

from ..dbal.platforms import SQLitePlatform
from .connector import Connector


class DictCursor(object):

    def __init__(self, cursor, row):
        self.dict = {}
        self.cursor = cursor

        for idx, col in enumerate(cursor.description):
            self.dict[col[0]] = row[idx]

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            return getattr(self.cursor, item)

    def __getitem__(self, item):
        return self.dict[item]

    def keys(self):
        return self.dict.keys()

    def values(self):
        return self.dict.values()

    def items(self):
        return self.dict.items()


class SQLiteConnector(Connector):

    RESERVED_KEYWORDS = [
        'log_queries', 'driver', 'prefix', 'name',
        'foreign_keys', 'use_qmark'
    ]

    def _do_connect(self, config):
        connection = self.get_api().connect(**self.get_config(config))
        connection.isolation_level = None
        connection.row_factory = DictCursor

        # We activate foreign keys support by default
        if config.get('foreign_keys', True):
            connection.execute("PRAGMA foreign_keys = ON")

        return connection

    def get_api(self):
        return sqlite3

    def get_dbal_platform(self):
        return SQLitePlatform()

    def is_version_aware(self):
        return False

    def get_server_version(self):
        sql = 'select sqlite_version() AS sqlite_version'

        rows = self._connection.execute(sql).fetchall()
        version = rows[0]['sqlite_version']

        return tuple(version.split('.')[:3] + [''])
