# -*- coding: utf-8 -*-

import os

from .. import OratorTestCase
from . import IntegrationTestCase
from orator.connections import MySqlConnection
from orator.connectors.mysql_connector import MySqlConnector


class MySQLIntegrationTestCase(IntegrationTestCase, OratorTestCase):

    @classmethod
    def get_connection_resolver(cls):
        return DatabaseIntegrationConnectionResolver()


class DatabaseIntegrationConnectionResolver(object):

    _connection = None

    def connection(self, name=None):
        if self._connection:
            return self._connection

        ci = os.environ.get('CI', False)
        if ci:
            database = 'orator_test'
            user = 'root'
            password = ''
        else:
            database = 'orator_test'
            user = 'orator'
            password = 'orator'

        self._connection = MySqlConnection(
            MySqlConnector().connect({
                'database': database,
                'user': user,
                'password': password
            })
        )

        return self._connection

    def get_default_connection(self):
        return 'default'

    def set_default_connection(self, name):
        pass
