# -*- coding: utf-8 -*-

try:
    import psycopg2
    import psycopg2.extras

    from psycopg2 import extensions

    connection_class = psycopg2.extras.DictConnection
    cursor_class = psycopg2.extras.DictCursor
    row_class = psycopg2.extras.DictRow
except ImportError:
    psycopg2 = None
    connection_class = object
    cursor_class = object
    row_class = object

from ..dbal.platforms import PostgresPlatform
from .connector import Connector
from ..utils.qmarker import qmark, denullify
from ..utils.helpers import serialize


class BaseDictConnection(connection_class):
    def cursor(self, *args, **kwargs):
        kwargs.setdefault("cursor_factory", BaseDictCursor)

        return super(BaseDictConnection, self).cursor(*args, **kwargs)


class DictConnection(BaseDictConnection):
    def cursor(self, *args, **kwargs):
        kwargs.setdefault("cursor_factory", DictCursor)

        return super(DictConnection, self).cursor(*args, **kwargs)


class BaseDictCursor(cursor_class):
    def __init__(self, *args, **kwargs):
        kwargs["row_factory"] = DictRow
        super(cursor_class, self).__init__(*args, **kwargs)
        self._prefetch = 1


class DictCursor(BaseDictCursor):
    def execute(self, query, vars=None):
        query = qmark(query)

        return super(DictCursor, self).execute(query, vars)

    def executemany(self, query, args_seq):
        query = qmark(query)

        return super(DictCursor, self).executemany(query, denullify(args_seq))


class DictRow(row_class):
    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError(item)

    def serialize(self):
        serialized = {}
        for column, index in self._index.items():
            serialized[column] = list.__getitem__(self, index)

        return serialize(serialized)


class PostgresConnector(Connector):

    RESERVED_KEYWORDS = [
        "log_queries",
        "driver",
        "prefix",
        "name",
        "register_unicode",
        "use_qmark",
    ]

    SUPPORTED_PACKAGES = ["psycopg2"]

    def _do_connect(self, config):
        connection = self.get_api().connect(
            connection_factory=self.get_connection_class(config),
            **self.get_config(config)
        )

        if config.get("use_unicode", True):
            extensions.register_type(extensions.UNICODE, connection)
            extensions.register_type(extensions.UNICODEARRAY, connection)

        connection.autocommit = True

        return connection

    def get_connection_class(self, config):
        if config.get("use_qmark"):
            return DictConnection

        return BaseDictConnection

    def get_api(self):
        return psycopg2

    @property
    def autocommit(self):
        return self._connection.autocommit

    @autocommit.setter
    def autocommit(self, value):
        self._connection.autocommit = value

    def get_dbal_platform(self):
        return PostgresPlatform()

    def is_version_aware(self):
        return False

    def get_server_version(self):
        int_version = self._connection.server_version
        major = int_version // 10000
        minor = int_version // 100 % 100
        fix = int_version % 10

        return major, minor, fix, ""
