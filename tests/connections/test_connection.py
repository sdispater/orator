# -*- coding: utf-8 -*-

import threading
try:
    from Queue import Queue
except ImportError:
    from queue import Queue

from .. import OratorTestCase
from .. import mock
from ..orm.models import User

from orator.query.builder import QueryBuilder
from orator.connections.connection import Connection


class ConnectionTestCase(OratorTestCase):

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


class ConnectionThreadLocalTest(OratorTestCase):

    threads = 4

    def test_create_thread_local(self):
        self.init_database()

        def create_user_thread(low, hi):
            for _ in range(low, hi):
                User.create(name='u%d' % i)

            User.get_connection_resolver().disconnect()

        threads = []
        for i in range(self.threads):
            threads.append(threading.Thread(target=create_user_thread, args=(i*10, i * 10 + 10)))

        [t.start() for t in threads]
        [t.join() for t in threads]

        self.assertEqual(User.select().count(), self.threads * 10)

    def test_read_thread_local(self):
        self.init_database()

        data_queue = Queue()

        def reader_thread(q, num):
            for _ in range(num):
                data_queue.put(User.select().count())

        threads = []

        for i in range(self.threads):
            threads.append(threading.Thread(target=reader_thread, args=(data_queue, 20)))

        [t.start() for t in threads]
        [t.join() for t in threads]

        self.assertEqual(data_queue.qsize(), self.threads * 20)
