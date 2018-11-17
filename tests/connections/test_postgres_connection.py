# -*- coding: utf-8 -*-

from .. import OratorTestCase

from orator.connections.postgres_connection import PostgresConnection


class PostgresConnectionTestCase(OratorTestCase):
    def test_marker_is_properly_set(self):
        connection = PostgresConnection(None, "database", "", {"use_qmark": True})

        self.assertEqual("?", connection.get_marker())

    def test_marker_default(self):
        connection = PostgresConnection(None, "database", "", {})

        self.assertIsNone(connection.get_marker())

    def test_marker_use_qmark_false(self):
        connection = PostgresConnection(None, "database", "", {"use_qmark": False})

        self.assertIsNone(connection.get_marker())
