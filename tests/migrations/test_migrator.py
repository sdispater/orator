# -*- coding: utf-8 -*-

import os
import glob
from flexmock import flexmock, flexmock_teardown
from .. import OratorTestCase
from orator.migrations import Migrator, DatabaseMigrationRepository, Migration
from orator import DatabaseManager
from orator.connections import Connection


class MigratorTestCase(OratorTestCase):

    def tearDown(self):
        flexmock_teardown()

    def test_migrations_are_run_up_when_outstanding_migrations_exist(self):
        resolver = flexmock(DatabaseManager)
        resolver.should_receive('connection').and_return(None)

        migrator = flexmock(
            Migrator(
                flexmock(
                    DatabaseMigrationRepository(
                        resolver,
                        'migrations'
                    )
                ),
                resolver
            )
        )

        g = flexmock(glob)
        g.should_receive('glob').with_args(os.path.join(os.getcwd(), '*_*.py')).and_return([
            os.path.join(os.getcwd(), '2_bar.py'),
            os.path.join(os.getcwd(), '1_foo.py'),
            os.path.join(os.getcwd(), '3_baz.py')
        ])

        migrator.get_repository().should_receive('get_ran').once().and_return(['1_foo'])
        migrator.get_repository().should_receive('get_next_batch_number').once().and_return(1)
        migrator.get_repository().should_receive('log').once().with_args('2_bar', 1)
        migrator.get_repository().should_receive('log').once().with_args('3_baz', 1)
        bar_mock = flexmock(MigrationStub())
        bar_mock.should_receive('up').once()
        baz_mock = flexmock(MigrationStub())
        baz_mock.should_receive('up').once()
        migrator.should_receive('_resolve').with_args(os.getcwd(), '2_bar').once().and_return(bar_mock)
        migrator.should_receive('_resolve').with_args(os.getcwd(), '3_baz').once().and_return(baz_mock)

        migrator.run(os.getcwd())

    def test_up_migration_can_be_pretended(self):
        resolver_mock = flexmock(DatabaseManager)
        resolver_mock.should_receive('connection').and_return({})
        resolver = flexmock(DatabaseManager({}))
        connection = flexmock(Connection(None))
        connection.should_receive('pretend').replace_with(lambda callback: callback(None))
        resolver.should_receive('connection').with_args(None).and_return(connection)

        migrator = flexmock(
            Migrator(
                flexmock(
                    DatabaseMigrationRepository(
                        resolver,
                        'migrations'
                    )
                ),
                resolver
            )
        )

        g = flexmock(glob)
        g.should_receive('glob').with_args(os.path.join(os.getcwd(), '*_*.py')).and_return([
            os.path.join(os.getcwd(), '2_bar.py'),
            os.path.join(os.getcwd(), '1_foo.py'),
            os.path.join(os.getcwd(), '3_baz.py')
        ])

        migrator.get_repository().should_receive('get_ran').once().and_return(['1_foo'])
        migrator.get_repository().should_receive('get_next_batch_number').once().and_return(1)
        bar_mock = flexmock(MigrationStub())
        bar_mock.should_receive('get_connection').once().and_return(None)
        bar_mock.should_receive('up').once()
        baz_mock = flexmock(MigrationStub())
        baz_mock.should_receive('get_connection').once().and_return(None)
        baz_mock.should_receive('up').once()
        migrator.should_receive('_resolve').with_args(os.getcwd(), '2_bar').once().and_return(bar_mock)
        migrator.should_receive('_resolve').with_args(os.getcwd(), '3_baz').once().and_return(baz_mock)

        migrator.run(os.getcwd(), True)

    def test_nothing_is_done_when_no_migrations_outstanding(self):
        resolver_mock = flexmock(DatabaseManager)
        resolver_mock.should_receive('connection').and_return(None)
        resolver = flexmock(DatabaseManager({}))

        migrator = flexmock(
            Migrator(
                flexmock(
                    DatabaseMigrationRepository(
                        resolver,
                        'migrations'
                    )
                ),
                resolver
            )
        )

        g = flexmock(glob)
        g.should_receive('glob').with_args(os.path.join(os.getcwd(), '*_*.py')).and_return([
            os.path.join(os.getcwd(), '1_foo.py')
        ])

        migrator.get_repository().should_receive('get_ran').once().and_return(['1_foo'])

        migrator.run(os.getcwd())

    def test_last_batch_of_migrations_can_be_rolled_back(self):
        resolver = flexmock(DatabaseManager)
        resolver.should_receive('connection').and_return(None)

        migrator = flexmock(
            Migrator(
                flexmock(
                    DatabaseMigrationRepository(
                        resolver,
                        'migrations'
                    )
                ),
                resolver
            )
        )

        foo_migration = MigrationStub('foo')
        bar_migration = MigrationStub('bar')
        migrator.get_repository().should_receive('get_last').once().and_return([
            foo_migration,
            bar_migration
        ])

        bar_mock = flexmock(MigrationStub())
        bar_mock.should_receive('down').once()
        foo_mock = flexmock(MigrationStub())
        foo_mock.should_receive('down').once()
        migrator.should_receive('_resolve').with_args(os.getcwd(), 'bar').once().and_return(bar_mock)
        migrator.should_receive('_resolve').with_args(os.getcwd(), 'foo').once().and_return(foo_mock)

        migrator.get_repository().should_receive('delete').once().with_args(bar_migration)
        migrator.get_repository().should_receive('delete').once().with_args(foo_migration)

        migrator.rollback(os.getcwd())

    def test_rollback_migration_can_be_pretended(self):
        resolver_mock = flexmock(DatabaseManager)
        resolver_mock.should_receive('connection').and_return({})
        resolver = flexmock(DatabaseManager({}))
        connection = flexmock(Connection(None))
        connection.should_receive('pretend').replace_with(lambda callback: callback(None))
        resolver.should_receive('connection').with_args(None).and_return(connection)

        migrator = flexmock(
            Migrator(
                flexmock(
                    DatabaseMigrationRepository(
                        resolver,
                        'migrations'
                    )
                ),
                resolver
            )
        )

        foo_migration = MigrationStub('foo')
        bar_migration = MigrationStub('bar')
        migrator.get_repository().should_receive('get_last').once().and_return([
            foo_migration,
            bar_migration
        ])

        bar_mock = flexmock(MigrationStub())
        bar_mock.should_receive('down').once()
        foo_mock = flexmock(MigrationStub())
        foo_mock.should_receive('down').once()
        migrator.should_receive('_resolve').with_args(os.getcwd(), 'bar').once().and_return(bar_mock)
        migrator.should_receive('_resolve').with_args(os.getcwd(), 'foo').once().and_return(foo_mock)

        migrator.rollback(os.getcwd(), True)

    def test_nothing_is_rolled_back_when_nothing_in_repository(self):
        resolver = flexmock(DatabaseManager)
        resolver.should_receive('connection').and_return(None)

        migrator = flexmock(
            Migrator(
                flexmock(
                    DatabaseMigrationRepository(
                        resolver,
                        'migrations'
                    )
                ),
                resolver
            )
        )

        migrator.get_repository().should_receive('get_last').once().and_return([])

        migrator.rollback(os.getcwd())


class MigrationStub(Migration):

    def __init__(self, migration=None):
        self.migration = migration

    def up(self):
        pass

    def down(self):
        pass

    def __getitem__(self, item):
        return self.migration
