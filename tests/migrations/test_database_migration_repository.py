# -*- coding: utf-8 -*-

from flexmock import flexmock, flexmock_teardown
from .. import OratorTestCase
from orator.migrations import DatabaseMigrationRepository
from orator import DatabaseManager
from orator.query import QueryBuilder
from orator.connections import Connection
from orator.schema import SchemaBuilder


class DatabaseMigrationRepositoryTestCase(OratorTestCase):

    def tearDown(self):
        flexmock_teardown()

    def test_get_ran_migrations_list_migrations_by_package(self):
        repo = self.get_repository()
        connection = flexmock(Connection(None))
        query = flexmock(QueryBuilder(connection, None, None))
        repo.get_connection_resolver().should_receive('connection').with_args(None).and_return(connection)
        repo.get_connection().should_receive('table').once().with_args('migrations').and_return(query)
        query.should_receive('lists').once().with_args('migration').and_return('bar')

        self.assertEqual('bar', repo.get_ran())

    def test_get_last_migrations(self):
        resolver_mock = flexmock(DatabaseManager)
        resolver_mock.should_receive('connection').and_return(None)
        resolver = flexmock(resolver_mock({}))
        repo = flexmock(DatabaseMigrationRepository(resolver, 'migrations'))
        connection = flexmock(Connection(None))
        query = flexmock(QueryBuilder(connection, None, None))
        repo.should_receive('get_last_batch_number').and_return(1)
        repo.get_connection_resolver().should_receive('connection').with_args(None).and_return(connection)
        repo.get_connection().should_receive('table').once().with_args('migrations').and_return(query)
        query.should_receive('where').once().with_args('batch', 1).and_return(query)
        query.should_receive('order_by').once().with_args('migration', 'desc').and_return(query)
        query.should_receive('get').once().and_return('foo')

        self.assertEqual('foo', repo.get_last())

    def test_log_inserts_record_into_migration_table(self):
        repo = self.get_repository()
        connection = flexmock(Connection(None))
        query = flexmock(QueryBuilder(connection, None, None))
        repo.get_connection_resolver().should_receive('connection').with_args(None).and_return(connection)
        repo.get_connection().should_receive('table').once().with_args('migrations').and_return(query)
        query.should_receive('insert').once().with_args(migration='bar', batch=1)

        repo.log('bar', 1)

    def test_delete_removes_migration_from_table(self):
        repo = self.get_repository()
        connection = flexmock(Connection(None))
        query = flexmock(QueryBuilder(connection, None, None))
        repo.get_connection_resolver().should_receive('connection').with_args(None).and_return(connection)
        repo.get_connection().should_receive('table').once().with_args('migrations').and_return(query)
        query.should_receive('where').once().with_args('migration', 'foo').and_return(query)
        query.should_receive('delete').once()

        class Migration(object):

            migration = 'foo'

            def __getitem__(self, item):
                return self.migration

        repo.delete(Migration())

    def test_get_next_batch_number_returns_last_batch_number_plus_one(self):
        resolver_mock = flexmock(DatabaseManager)
        resolver_mock.should_receive('connection').and_return(None)
        resolver = flexmock(resolver_mock({}))
        repo = flexmock(DatabaseMigrationRepository(resolver, 'migrations'))
        repo.should_receive('get_last_batch_number').and_return(1)

        self.assertEqual(2, repo.get_next_batch_number())

    def test_get_last_batch_number_returns_max_batch(self):
        repo = self.get_repository()
        connection = flexmock(Connection(None))
        query = flexmock(QueryBuilder(connection, None, None))
        repo.get_connection_resolver().should_receive('connection').with_args(None).and_return(connection)
        repo.get_connection().should_receive('table').once().with_args('migrations').and_return(query)
        query.should_receive('max').and_return(1)

        self.assertEqual(1, repo.get_last_batch_number())

    def get_repository(self):
        resolver = flexmock(DatabaseManager)
        resolver.should_receive('connection').and_return(None)
        return DatabaseMigrationRepository(flexmock(resolver({})), 'migrations')
