# -*- coding: utf-8 -*-

import random
from ..exceptions import ArgumentError
from ..exceptions.connectors import UnsupportedDriver
from .mysql_connector import MySqlConnector
from .postgres_connector import PostgresConnector
from .sqlite_connector import SQLiteConnector
from ..connections import (
    MySqlConnection,
    PostgresConnection,
    SQLiteConnection
)


class ConnectionFactory(object):

    def make(self, config, name=None):
        if 'read' in config:
            return self._create_read_write_connection(config)

        return self._create_single_connection(config)

    def _create_single_connection(self, config):
        conn = self.create_connector(config).connect(config)

        return self._create_connection(
            config['driver'],
            conn,
            config['database'],
            config.get('prefix', ''),
            config
        )

    def _create_read_write_connection(self, config):
        connection = self._create_single_connection(config)

        connection.set_read_connection(self._create_read_connection(config))

        return connection

    def _create_read_connection(self, config):
        read_config = self._get_read_config(config)

        return self.create_connector(read_config).connect(read_config)

    def _get_read_config(self, config):
        read_config = self._get_read_write_config(config, 'read')

        return self._merge_read_write_config(config, read_config)

    def _get_write_config(self, config):
        write_config = self._get_read_write_config(config, 'write')

        return self._merge_read_write_config(config, write_config)

    def _get_read_write_config(self, config, type):
        if config.get(type, []):
            return random.choice(config[type])

        return config[type]

    def _merge_read_write_config(self, config, merge):
        config = config.copy()
        config.update(merge)

        del config['read']
        del config['write']

        return config

    def create_connector(self, config):
        if 'driver' not in config:
            raise ArgumentError('A driver must be specified')

        driver = config['driver']

        if driver == 'mysql':
            return MySqlConnector()
        elif driver == 'postgres':
            return PostgresConnector()
        elif driver == 'sqlite':
            return SQLiteConnector()

        raise UnsupportedDriver(driver)

    def _create_connection(self, driver, connection, database, prefix='', config=None):
        if config is None:
            config = {}

        if driver == 'mysql':
            return MySqlConnection(connection, database, prefix, config)
        elif driver == 'postgres':
            return PostgresConnection(connection, database, prefix, config)
        elif driver == 'sqlite':
            return SQLiteConnection(connection, database, prefix, config)

        raise UnsupportedDriver(driver)
