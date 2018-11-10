# -*- coding: utf-8 -*-

import os
import glob
import inspect
from flexmock import flexmock, flexmock_teardown
from .. import OratorTestCase
from orator.migrations import Migrator, DatabaseMigrationRepository, Migration
from orator import DatabaseManager
from orator.connections import Connection
from orator.utils import PY3K


class MigratorTestCase(OratorTestCase):
    def setUp(self):
        if PY3K:
            self.orig = inspect.getargspec
            inspect.getargspec = lambda fn: inspect.getfullargspec(fn)[:4]

    def tearDown(self):
        flexmock_teardown()

        if PY3K:
            inspect.getargspec = self.orig

    def test_migrations_are_run_up_when_outstanding_migrations_exist(self):
        resolver_mock = flexmock(DatabaseManager)
        resolver_mock.should_receive("connection").and_return({})
        resolver = flexmock(DatabaseManager({}))
        connection = flexmock()
        connection.should_receive("transaction").twice().and_return(connection)
        resolver.should_receive("connection").and_return(connection)

        migrator = flexmock(
            Migrator(
                flexmock(DatabaseMigrationRepository(resolver, "migrations")), resolver
            )
        )

        g = flexmock(glob)
        g.should_receive("glob").with_args(
            os.path.join(os.getcwd(), "[0-9]*_*.py")
        ).and_return(
            [
                os.path.join(os.getcwd(), "2_bar.py"),
                os.path.join(os.getcwd(), "1_foo.py"),
                os.path.join(os.getcwd(), "3_baz.py"),
            ]
        )

        migrator.get_repository().should_receive("get_ran").once().and_return(["1_foo"])
        migrator.get_repository().should_receive(
            "get_next_batch_number"
        ).once().and_return(1)
        migrator.get_repository().should_receive("log").once().with_args("2_bar", 1)
        migrator.get_repository().should_receive("log").once().with_args("3_baz", 1)
        bar_mock = flexmock(MigrationStub())
        bar_mock.set_connection(connection)
        bar_mock.should_receive("up").once()
        baz_mock = flexmock(MigrationStub())
        baz_mock.set_connection(connection)
        baz_mock.should_receive("up").once()
        migrator.should_receive("_resolve").with_args(
            os.getcwd(), "2_bar"
        ).once().and_return(bar_mock)
        migrator.should_receive("_resolve").with_args(
            os.getcwd(), "3_baz"
        ).once().and_return(baz_mock)

        migrator.run(os.getcwd())

    def test_migrations_are_run_up_directly_if_transactional_is_false(self):
        resolver_mock = flexmock(DatabaseManager)
        resolver_mock.should_receive("connection").and_return({})
        resolver = flexmock(DatabaseManager({}))
        connection = flexmock()
        connection.should_receive("transaction").never()
        resolver.should_receive("connection").and_return(connection)

        migrator = flexmock(
            Migrator(
                flexmock(DatabaseMigrationRepository(resolver, "migrations")), resolver
            )
        )

        g = flexmock(glob)
        g.should_receive("glob").with_args(
            os.path.join(os.getcwd(), "[0-9]*_*.py")
        ).and_return(
            [
                os.path.join(os.getcwd(), "2_bar.py"),
                os.path.join(os.getcwd(), "1_foo.py"),
                os.path.join(os.getcwd(), "3_baz.py"),
            ]
        )

        migrator.get_repository().should_receive("get_ran").once().and_return(["1_foo"])
        migrator.get_repository().should_receive(
            "get_next_batch_number"
        ).once().and_return(1)
        migrator.get_repository().should_receive("log").once().with_args("2_bar", 1)
        migrator.get_repository().should_receive("log").once().with_args("3_baz", 1)
        bar_mock = flexmock(MigrationStub())
        bar_mock.transactional = False
        bar_mock.set_connection(connection)
        bar_mock.should_receive("up").once()
        baz_mock = flexmock(MigrationStub())
        baz_mock.transactional = False
        baz_mock.set_connection(connection)
        baz_mock.should_receive("up").once()
        migrator.should_receive("_resolve").with_args(
            os.getcwd(), "2_bar"
        ).once().and_return(bar_mock)
        migrator.should_receive("_resolve").with_args(
            os.getcwd(), "3_baz"
        ).once().and_return(baz_mock)

        migrator.run(os.getcwd())

    def test_up_migration_can_be_pretended(self):
        resolver_mock = flexmock(DatabaseManager)
        resolver_mock.should_receive("connection").and_return({})
        resolver = flexmock(DatabaseManager({}))
        connection = flexmock(Connection(None))
        connection.should_receive("get_logged_queries").twice().and_return([])
        resolver.should_receive("connection").with_args(None).and_return(connection)

        migrator = flexmock(
            Migrator(
                flexmock(DatabaseMigrationRepository(resolver, "migrations")), resolver
            )
        )

        g = flexmock(glob)
        g.should_receive("glob").with_args(
            os.path.join(os.getcwd(), "[0-9]*_*.py")
        ).and_return(
            [
                os.path.join(os.getcwd(), "2_bar.py"),
                os.path.join(os.getcwd(), "1_foo.py"),
                os.path.join(os.getcwd(), "3_baz.py"),
            ]
        )

        migrator.get_repository().should_receive("get_ran").once().and_return(["1_foo"])
        migrator.get_repository().should_receive(
            "get_next_batch_number"
        ).once().and_return(1)
        bar_mock = flexmock(MigrationStub())
        bar_mock.should_receive("get_connection").once().and_return(connection)
        bar_mock.should_receive("up").once()
        baz_mock = flexmock(MigrationStub())
        baz_mock.should_receive("get_connection").once().and_return(connection)
        baz_mock.should_receive("up").once()
        migrator.should_receive("_resolve").with_args(
            os.getcwd(), "2_bar"
        ).once().and_return(bar_mock)
        migrator.should_receive("_resolve").with_args(
            os.getcwd(), "3_baz"
        ).once().and_return(baz_mock)

        migrator.run(os.getcwd(), True)

    def test_nothing_is_done_when_no_migrations_outstanding(self):
        resolver_mock = flexmock(DatabaseManager)
        resolver_mock.should_receive("connection").and_return(None)
        resolver = flexmock(DatabaseManager({}))

        migrator = flexmock(
            Migrator(
                flexmock(DatabaseMigrationRepository(resolver, "migrations")), resolver
            )
        )

        g = flexmock(glob)
        g.should_receive("glob").with_args(
            os.path.join(os.getcwd(), "[0-9]*_*.py")
        ).and_return([os.path.join(os.getcwd(), "1_foo.py")])

        migrator.get_repository().should_receive("get_ran").once().and_return(["1_foo"])

        migrator.run(os.getcwd())

    def test_last_batch_of_migrations_can_be_rolled_back(self):
        resolver_mock = flexmock(DatabaseManager)
        resolver_mock.should_receive("connection").and_return({})
        resolver = flexmock(DatabaseManager({}))
        connection = flexmock()
        connection.should_receive("transaction").twice().and_return(connection)
        resolver.should_receive("connection").and_return(connection)

        migrator = flexmock(
            Migrator(
                flexmock(DatabaseMigrationRepository(resolver, "migrations")), resolver
            )
        )

        foo_migration = MigrationStub("foo")
        bar_migration = MigrationStub("bar")
        migrator.get_repository().should_receive("get_last").once().and_return(
            [foo_migration, bar_migration]
        )

        bar_mock = flexmock(MigrationStub())
        bar_mock.set_connection(connection)
        bar_mock.should_receive("down").once()
        foo_mock = flexmock(MigrationStub())
        foo_mock.set_connection(connection)
        foo_mock.should_receive("down").once()
        migrator.should_receive("_resolve").with_args(
            os.getcwd(), "bar"
        ).once().and_return(bar_mock)
        migrator.should_receive("_resolve").with_args(
            os.getcwd(), "foo"
        ).once().and_return(foo_mock)

        migrator.get_repository().should_receive("delete").once().with_args(
            bar_migration
        )
        migrator.get_repository().should_receive("delete").once().with_args(
            foo_migration
        )

        migrator.rollback(os.getcwd())

    def test_last_batch_of_migrations_can_be_rolled_back_directly_if_transactional_is_false(
        self
    ):
        resolver_mock = flexmock(DatabaseManager)
        resolver_mock.should_receive("connection").and_return({})
        resolver = flexmock(DatabaseManager({}))
        connection = flexmock()
        connection.should_receive("transaction").never()
        resolver.should_receive("connection").and_return(connection)

        migrator = flexmock(
            Migrator(
                flexmock(DatabaseMigrationRepository(resolver, "migrations")), resolver
            )
        )

        foo_migration = MigrationStub("foo")
        bar_migration = MigrationStub("bar")
        migrator.get_repository().should_receive("get_last").once().and_return(
            [foo_migration, bar_migration]
        )

        bar_mock = flexmock(MigrationStub())
        bar_mock.transactional = False
        bar_mock.set_connection(connection)
        bar_mock.should_receive("down").once()
        foo_mock = flexmock(MigrationStub())
        foo_mock.transactional = False
        foo_mock.set_connection(connection)
        foo_mock.should_receive("down").once()
        migrator.should_receive("_resolve").with_args(
            os.getcwd(), "bar"
        ).once().and_return(bar_mock)
        migrator.should_receive("_resolve").with_args(
            os.getcwd(), "foo"
        ).once().and_return(foo_mock)

        migrator.get_repository().should_receive("delete").once().with_args(
            bar_migration
        )
        migrator.get_repository().should_receive("delete").once().with_args(
            foo_migration
        )

        migrator.rollback(os.getcwd())

    def test_rollback_migration_can_be_pretended(self):
        resolver_mock = flexmock(DatabaseManager)
        resolver_mock.should_receive("connection").and_return({})
        resolver = flexmock(DatabaseManager({}))
        connection = flexmock(Connection(None))
        connection.should_receive("get_logged_queries").twice().and_return([])
        resolver.should_receive("connection").with_args(None).and_return(connection)

        migrator = flexmock(
            Migrator(
                flexmock(DatabaseMigrationRepository(resolver, "migrations")), resolver
            )
        )

        foo_migration = flexmock(MigrationStub("foo"))
        foo_migration.should_receive("get_connection").and_return(connection)
        bar_migration = flexmock(MigrationStub("bar"))
        bar_migration.should_receive("get_connection").and_return(connection)
        migrator.get_repository().should_receive("get_last").once().and_return(
            [foo_migration, bar_migration]
        )

        migrator.should_receive("_resolve").with_args(
            os.getcwd(), "bar"
        ).once().and_return(bar_migration)
        migrator.should_receive("_resolve").with_args(
            os.getcwd(), "foo"
        ).once().and_return(foo_migration)

        migrator.rollback(os.getcwd(), True)

        self.assertTrue(foo_migration.downed)
        self.assertFalse(foo_migration.upped)
        self.assertTrue(foo_migration.downed)
        self.assertFalse(foo_migration.upped)

    def test_nothing_is_rolled_back_when_nothing_in_repository(self):
        resolver = flexmock(DatabaseManager)
        resolver.should_receive("connection").and_return(None)

        migrator = flexmock(
            Migrator(
                flexmock(DatabaseMigrationRepository(resolver, "migrations")), resolver
            )
        )

        migrator.get_repository().should_receive("get_last").once().and_return([])

        migrator.rollback(os.getcwd())


class MigrationStub(Migration):
    def __init__(self, migration=None):
        self.migration = migration
        self.upped = False
        self.downed = False

    def up(self):
        self.upped = True

    def down(self):
        self.downed = True

    def __getitem__(self, item):
        return self.migration
