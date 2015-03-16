# -*- coding: utf-8 -*-

from .. import EloquentTestCase
from .. import mock

from eloquent.query.builder import QueryBuilder
from eloquent.connections.connection import Connection


class ConnectionTestCase(EloquentTestCase):

    def test_table_returns_query_builder(self):
        connection = Connection(None, 'database')
        builder = connection.table('users')

        self.assertIsInstance(builder, QueryBuilder)
        self.assertEqual('users', builder.from__)
        self.assertEqual(connection.get_query_grammar(), builder.get_grammar())

    def test_transaction(self):
        connection = Connection(None, 'database')
        connection.begin_transaction = mock.MagicMock()
        connection.commit = mock.MagicMock()
        connection.rollback = mock.MagicMock()
        connection.insert = mock.MagicMock(return_value=1)

        with connection.transaction():
            connection.table('users').insert({'name': 'foo'})

        connection.begin_transaction.assert_called_once()
        connection.commit.assert_called_once()
        self.assertFalse(connection.rollback.called)

        connection.begin_transaction.reset_mock()
        connection.commit.reset_mock()
        connection.rollback.reset_mock()

        try:
            with connection.transaction():
                connection.table('users').insert({'name': 'foo'})
                raise Exception('foo')
        except Exception as e:
            self.assertEqual('foo', str(e))

        connection.begin_transaction.assert_called_once()
        connection.rollback.assert_called_once()
        self.assertFalse(connection.commit.called)
