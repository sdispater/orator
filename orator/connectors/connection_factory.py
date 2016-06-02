# -*- coding: utf-8 -*-

import random
from ..exceptions import ArgumentError
from ..exceptions.connectors import UnsupportedDriver
from .mysql_connector import MySQLConnector
from .postgres_connector import PostgresConnector
from .sqlite_connector import SQLiteConnector
from ..connections import (
    MySQLConnection,
    PostgresConnection,
    SQLiteConnection
)


class ConnectionFactory(object):

    CONNECTORS = {
        'sqlite': SQLiteConnector,
        'mysql': MySQLConnector,
        'postgres': PostgresConnector,
        'pgsql': PostgresConnector
    }

    CONNECTIONS = {
        'sqlite': SQLiteConnection,
        'mysql': MySQLConnection,
        'postgres': PostgresConnection,
        'pgsql': PostgresConnection
    }

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
        connection = self._create_single_connection(self._get_write_config(config))

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

        if driver not in self.CONNECTORS:
            raise UnsupportedDriver(driver)

        return self.CONNECTORS[driver](driver)

    @classmethod
    def register_connector(cls, name, connector):
        cls.CONNECTORS[connector] = connector

    @classmethod
    def register_connection(cls, name, connection):
        cls.CONNECTIONS[name] = connection

    def _create_connection(self, driver, connection, database, prefix='', config=None):
        if config is None:
            config = {}

        if driver not in self.CONNECTIONS:
            raise UnsupportedDriver(driver)

        return self.CONNECTIONS[driver](connection, database, prefix, config)
