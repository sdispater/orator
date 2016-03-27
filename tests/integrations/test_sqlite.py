# -*- coding: utf-8 -*-

from .. import OratorTestCase
from . import IntegrationTestCase
from orator.connections import SQLiteConnection
from orator.connectors.sqlite_connector import SQLiteConnector


class SQLiteIntegrationTestCase(IntegrationTestCase, OratorTestCase):

    @classmethod
    def get_connection_resolver(cls):
        return DatabaseIntegrationConnectionResolver()


class DatabaseIntegrationConnectionResolver(object):

    _connection = None

    def connection(self, name=None):
        if self._connection:
            return self._connection

        self._connection = SQLiteConnection(SQLiteConnector().connect({'database': ':memory:'}))

        return self._connection

    def get_default_connection(self):
        return 'default'

    def set_default_connection(self, name):
        pass

    def disconnect(self):
        if self._connection:
            self._connection.disconnect()
