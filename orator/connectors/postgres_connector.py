# -*- coding: utf-8 -*-

try:
    import psycopg2
    import psycopg2.extras

    from psycopg2 import extensions
except ImportError:
    psycopg2 = None

from .connector import Connector


class PostgresConnector(Connector):

    RESERVED_KEYWORDS = [
        'log_queries', 'driver', 'prefix', 'name',
        'register_unicode'
    ]

    SUPPORTED_PACKAGES = ['psycopg2']

    def connect(self, config):
        connection = self.get_api().connect(
            connection_factory=psycopg2.extras.DictConnection,
            **self.get_config(config)
        )

        if config.get('use_unicode', True):
            extensions.register_type(extensions.UNICODE, connection)
            extensions.register_type(extensions.UNICODEARRAY, connection)

        connection.autocommit = True

        return connection

    def get_api(self):
        return psycopg2
