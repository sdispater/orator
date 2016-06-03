# -*- coding: utf-8 -*-

import re

try:
    import psycopg2
    import psycopg2.extras

    from psycopg2 import extensions

    BaseDictConnection = psycopg2.extras.DictConnection
    BaseDictCursor = psycopg2.extras.DictCursor
except ImportError:
    psycopg2 = None
    BaseDictConnection = object
    BaseDictCursor = object

from .connector import Connector
from ..utils.qmarker import qmark, denullify


class DictConnection(BaseDictConnection):

    def cursor(self, *args, **kwargs):
        kwargs.setdefault('cursor_factory', DictCursor)

        return super(DictConnection, self).cursor(*args, **kwargs)


class DictCursor(BaseDictCursor):

    def execute(self, query, vars=None):
        query = qmark(query)

        return super(DictCursor, self).execute(query, vars)

    def executemany(self, query, args_seq):
        query = qmark(query)

        return super(DictCursor, self).executemany(
            query, denullify(args_seq))


class PostgresConnector(Connector):

    RESERVED_KEYWORDS = [
        'log_queries', 'driver', 'prefix', 'name',
        'register_unicode', 'use_qmark'
    ]

    SUPPORTED_PACKAGES = ['psycopg2']

    def _do_connect(self, config):
        connection = self.get_api().connect(
            connection_factory=self.get_connection_class(config),
            **self.get_config(config)
        )

        if config.get('use_unicode', True):
            extensions.register_type(extensions.UNICODE, connection)
            extensions.register_type(extensions.UNICODEARRAY, connection)

        connection.autocommit = True

        return connection

    def get_connection_class(self, config):
        if config.get('use_qmark'):
            return DictConnection

        return BaseDictConnection

    def get_api(self):
        return psycopg2
