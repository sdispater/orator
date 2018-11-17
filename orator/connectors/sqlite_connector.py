# -*- coding: utf-8 -*-

from pendulum import Pendulum, Date

try:
    import sqlite3

    from sqlite3 import register_adapter

    register_adapter(Pendulum, lambda val: val.isoformat(" "))
    register_adapter(Date, lambda val: val.isoformat())
except ImportError:
    sqlite3 = None

from ..dbal.platforms import SQLitePlatform
from ..utils.helpers import serialize
from .connector import Connector


class DictCursor(dict):
    def __init__(self, cursor, row):
        self.dict = {}
        self.cursor = cursor

        for idx, col in enumerate(cursor.description):
            self.dict[col[0]] = row[idx]

        super(DictCursor, self).__init__(self.dict)

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            return getattr(self.cursor, item)

    def serialize(self):
        return serialize(self)


class SQLiteConnector(Connector):

    RESERVED_KEYWORDS = [
        "log_queries",
        "driver",
        "prefix",
        "name",
        "foreign_keys",
        "use_qmark",
    ]

    def _do_connect(self, config):
        connection = self.get_api().connect(**self.get_config(config))
        connection.isolation_level = None
        connection.row_factory = DictCursor

        # We activate foreign keys support by default
        if config.get("foreign_keys", True):
            connection.execute("PRAGMA foreign_keys = ON")

        return connection

    def get_api(self):
        return sqlite3

    @property
    def isolation_level(self):
        return self._connection.isolation_level

    @isolation_level.setter
    def isolation_level(self, value):
        self._connection.isolation_level = value

    def get_dbal_platform(self):
        return SQLitePlatform()

    def is_version_aware(self):
        return False

    def get_server_version(self):
        sql = "select sqlite_version() AS sqlite_version"

        rows = self._connection.execute(sql).fetchall()
        version = rows[0]["sqlite_version"]

        return tuple(version.split(".")[:3] + [""])
