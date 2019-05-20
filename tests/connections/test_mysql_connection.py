# -*- coding: utf-8 -*-

from flexmock import flexmock

from .. import OratorTestCase
from .. import mock

from orator.connections.mysql_connection import MySQLConnection


class MySQLConnectionTestCase(OratorTestCase):
    def test_marker_is_properly_set(self):
        connection = MySQLConnection(None, "database", "", {"use_qmark": True})

        self.assertEqual("?", connection.get_marker())

    def test_marker_default(self):
        connection = MySQLConnection(None, "database", "", {})

        self.assertIsNone(connection.get_marker())

    def test_marker_use_qmark_false(self):
        connection = MySQLConnection(None, "database", "", {"use_qmark": False})

        self.assertIsNone(connection.get_marker())

    def test_recover_if_caused_by_lost_connection_is_called(self):
        connection = flexmock(MySQLConnection(None, "database"))
        connection._connection = mock.Mock()
        connection._connection.autocommit.side_effect = Exception("lost connection")

        connection.should_receive("_recover_if_caused_by_lost_connection").once()
        connection.should_receive("reconnect")

        connection.begin_transaction()
